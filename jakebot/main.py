import logging
from typing import Dict, Any
from datetime import datetime

from ai_agents import RuleBasedAgent
from integrations import CloseIntegration, NowCertsIntegration, SlackIntegration
from config.settings import (
    CLOSE_API_KEY,
    NOWCERTS_API_KEY,
    SLACK_WEBHOOK_URL,
    SLACK_NOTIFICATION_CHANNEL
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CallProcessor:
    """Main class to process call transcripts and handle integrations"""
    
    def __init__(self):
        self.agent = RuleBasedAgent()
        self.close = CloseIntegration(CLOSE_API_KEY)
        self.nowcerts = NowCertsIntegration(NOWCERTS_API_KEY)
        self.slack = SlackIntegration(SLACK_WEBHOOK_URL)
    
    def process_call(self, transcript: str, call_metadata: Dict[str, Any]) -> None:
        """
        Process a call transcript and create appropriate tasks/notifications
        
        Args:
            transcript: The call transcript text
            call_metadata: Dictionary containing call info (agent_id, lead_id, etc.)
        """
        try:
            logger.info(f"Processing call for lead {call_metadata.get('lead_id')}")
            
            # Extract commitments from transcript
            commitments = self.agent.extract_commitments(transcript)
            
            if not commitments:
                logger.info("No commitments found in call")
                return
            
            # Process each commitment
            for commitment in commitments:
                if commitment.system == "NowCerts":
                    # Handle policy-related tasks
                    if commitment.requires_approval:
                        self._request_approval(commitment, call_metadata)
                    else:
                        self._handle_nowcerts_task(commitment, call_metadata)
                else:
                    # Handle CRM tasks
                    self._handle_crm_task(commitment, call_metadata)
            
            # Send summary to Slack
            self._send_summary(commitments, call_metadata)
            
        except Exception as e:
            logger.error(f"Error processing call: {str(e)}")
            self.slack.send_notification(
                f"⚠️ Error processing call for lead {call_metadata.get('lead_id')}: {str(e)}",
                channel=SLACK_NOTIFICATION_CHANNEL
            )
    
    def _handle_crm_task(self, commitment, call_metadata):
        """Create a task in Close CRM"""
        task_data = {
            "description": commitment.description,
            "due_date": commitment.due_date.isoformat() if commitment.due_date else None,
            "lead_id": call_metadata.get("lead_id"),
            "assigned_to": call_metadata.get("agent_id")
        }
        self.close.create_task(task_data)
        logger.info(f"Created CRM task: {commitment.description}")
    
    def _handle_nowcerts_task(self, commitment, call_metadata):
        """Handle a NowCerts-related task"""
        # For now, create a task in both systems for tracking
        self._handle_crm_task(commitment, call_metadata)
        
        # TODO: Implement actual NowCerts API calls based on commitment type
        logger.info(f"Would handle NowCerts task: {commitment.description}")
    
    def _request_approval(self, commitment, call_metadata):
        """Request approval via Slack for sensitive tasks"""
        message = (
            f"🔔 *Approval Needed*\n"
            f"Lead: {call_metadata.get('lead_id')}\n"
            f"Task: {commitment.description}\n"
            f"Requested by: {call_metadata.get('agent_name')}"
        )
        self.slack.send_notification(message, channel=SLACK_NOTIFICATION_CHANNEL)
        logger.info(f"Requested approval for: {commitment.description}")
    
    def _send_summary(self, commitments, call_metadata):
        """Send a summary of all commitments to Slack"""
        summary = (
            f"📞 *Call Summary*\n"
            f"Lead: {call_metadata.get('lead_id')}\n"
            f"Agent: {call_metadata.get('agent_name')}\n"
            f"Commitments found: {len(commitments)}\n\n"
        )
        
        for i, commitment in enumerate(commitments, 1):
            summary += f"{i}. {commitment.description}"
            if commitment.requires_approval:
                summary += " _(Needs Approval)_"
            summary += "\n"
        
        self.slack.send_notification(summary, channel=SLACK_NOTIFICATION_CHANNEL)

def handle_call_webhook(webhook_data: Dict[str, Any]) -> None:
    """
    Entry point for webhook handling
    
    Args:
        webhook_data: The webhook payload from Close/Twilio
    """
    processor = CallProcessor()
    
    # Extract relevant data from webhook
    call_metadata = {
        "lead_id": webhook_data.get("lead_id"),
        "agent_id": webhook_data.get("user_id"),
        "agent_name": webhook_data.get("user_name"),
        "call_id": webhook_data.get("call_id")
    }
    
    # For now, assume transcript is in webhook data
    # In reality, we might need to fetch it from Twilio
    transcript = webhook_data.get("transcript", "")
    
    processor.process_call(transcript, call_metadata)

if __name__ == "__main__":
    # Example usage/testing
    test_data = {
        "lead_id": "lead_123",
        "user_id": "user_456",
        "user_name": "John Agent",
        "call_id": "call_789",
        "transcript": """
        Agent: I will send you the insurance documents by email tomorrow.
        Customer: Great, thank you.
        Agent: I'll also update your policy with the new vehicle information.
        Customer: Perfect, appreciate it.
        """
    }
    handle_call_webhook(test_data) 