"""Central workflow manager for JakeBot"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from jakebot.config import JakeBotConfig
from jakebot.workflow.task_manager import TaskManager
from jakebot.integrations.close.client import CloseClient
from jakebot.integrations.nowcerts.client import NowCertsClient
from jakebot.integrations.slack.client import SlackClient
from jakebot.ai_agents.commitment_detector import CommitmentDetector, Commitment

logger = logging.getLogger(__name__)

class WorkflowManager:
    """Manages the complete workflow from call detection to task creation"""
    
    def __init__(self, config: JakeBotConfig):
        # Initialize components
        self.task_manager = TaskManager(config)
        self.close_client = CloseClient(config)
        self.nowcerts_client = NowCertsClient(config)
        self.slack_client = SlackClient(config)
        self.detector = CommitmentDetector()
        
        # Configuration
        self.config = config
        
    async def handle_new_call(self, call_id: str):
        """Entry point for processing new calls"""
        try:
            # 1. Get call details from Close
            call_data = await self.close_client.get_call(call_id)
            
            # 2. Detect commitments
            commitments = self.detector.detect_commitments(call_data['note'])
            
            # 3. Process each commitment
            results = []
            for commitment in commitments:
                result = await self.process_commitment(commitment, call_data)
                results.append(result)
            
            # 4. Send summary to Slack if configured
            if self.config.SLACK_NOTIFICATIONS_ENABLED:
                await self.send_summary(call_data, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing call {call_id}: {str(e)}")
            # Notify about failure
            if self.config.SLACK_NOTIFICATIONS_ENABLED:
                await self.slack_client.send_message(
                    f"❌ Failed to process call {call_id}: {str(e)}",
                    channel=self.config.SLACK_ERROR_CHANNEL
                )
            raise  # Re-raise to let caller handle
    
    async def process_commitment(self, 
                               commitment: Commitment, 
                               call_data: Dict) -> Dict:
        """Process a single commitment"""
        try:
            # 1. Validate commitment
            if not self.validate_commitment(commitment):
                return {
                    "status": "invalid",
                    "commitment": commitment,
                    "error": "Failed validation"
                }
            
            # 2. Check if approval needed
            if commitment.requires_approval:
                approved = await self.request_approval(commitment, call_data)
                if not approved:
                    return {
                        "status": "rejected",
                        "commitment": commitment
                    }
            
            # 3. Create task
            task = await self.task_manager.create_task_from_commitment(
                commitment, 
                call_data
            )
            
            # 4. Track in monitoring system
            self.track_commitment(commitment, task)
            
            return {
                "status": "completed",
                "commitment": commitment,
                "task": task
            }
            
        except Exception as e:
            logger.error(f"Error processing commitment: {str(e)}")
            return {
                "status": "error",
                "commitment": commitment,
                "error": str(e)
            }
    
    def validate_commitment(self, commitment: Commitment) -> bool:
        """Validate commitment before processing"""
        # Must have description
        if not commitment.description:
            return False
            
        # Must have valid due date
        if not commitment.due_date or commitment.due_date < datetime.now():
            return False
            
        # Must have valid system
        if commitment.system not in ["NowCerts", "CRM"]:
            return False
            
        return True
    
    async def request_approval(self, 
                             commitment: Commitment, 
                             call_data: Dict) -> bool:
        """Request approval via Slack"""
        message = (
            f"*New Commitment Requires Approval*\n"
            f"From Call: {call_data['id']}\n"
            f"Type: {commitment.type}\n"
            f"Description: {commitment.description}\n"
            f"Due Date: {commitment.due_date}\n"
            f"Priority: {commitment.priority}\n"
            f"System: {commitment.system}"
        )
        
        return await self.slack_client.request_approval(
            message,
            channel=self.config.SLACK_APPROVAL_CHANNEL
        )
    
    def track_commitment(self, commitment: Commitment, task: Dict):
        """Track commitment for monitoring"""
        # TODO: Implement monitoring
        pass
    
    async def send_summary(self, call_data: Dict, results: List[Dict]):
        """Send summary to Slack"""
        # Format summary message
        summary = (
            f"*Call Processing Summary*\n"
            f"Call ID: {call_data['id']}\n"
            f"Duration: {call_data['duration']} seconds\n"
            f"Commitments Found: {len(results)}\n\n"
        )
        
        for result in results:
            status = result['status']
            commitment = result['commitment']
            summary += (
                f"• {status.upper()}: {commitment.description}\n"
                f"  Due: {commitment.due_date}\n"
                f"  System: {commitment.system}\n\n"
            )
        
        await self.slack_client.send_message(
            summary,
            channel=self.config.SLACK_SUMMARY_CHANNEL
        ) 