"""Task management for commitments"""
import logging
from typing import Dict, Optional
from datetime import datetime

from jakebot.integrations.nowcerts.client import NowCertsClient
from jakebot.integrations.close.client import CloseClient
from jakebot.ai_agents.commitment_detector import Commitment
from jakebot.workflow.task_status import TaskStatusTracker, TaskStatus

logger = logging.getLogger(__name__)

class TaskManager:
    """Manage tasks across systems"""
    
    def __init__(self, config):
        self.nowcerts_client = NowCertsClient(config)
        self.close_client = CloseClient(config)
        self.status_tracker = TaskStatusTracker()
        
    async def create_task_from_commitment(self, 
                                        commitment: Commitment,
                                        call_data: Dict) -> Dict:
        """Create appropriate task from commitment"""
        
        try:
            # Create task in appropriate system
            if commitment.system == "NowCerts":
                task = await self._create_nowcerts_task(commitment, call_data)
            elif commitment.system == "CRM":
                task = await self._create_close_task(commitment, call_data)
            else:
                raise ValueError(f"Unknown system: {commitment.system}")
            
            # Track the task
            self.status_tracker.add_task(task['id'], {
                "commitment": commitment.to_dict(),
                "system": commitment.system,
                "call_id": call_data["id"],
                "task_data": task
            })
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            if commitment.id in self.status_tracker.tasks:
                self.status_tracker.update_status(
                    commitment.id,
                    TaskStatus.FAILED,
                    notes=str(e)
                )
            raise
    
    async def update_task_status(self, task_id: str, 
                                status: TaskStatus,
                                notes: Optional[str] = None):
        """Update task status"""
        try:
            task_data = self.status_tracker.get_task_status(task_id)
            
            # Update in appropriate system
            if task_data["system"] == "NowCerts":
                await self.nowcerts_client.update_task(
                    task_id,
                    {"status": status.value}
                )
            else:  # Close
                await self.close_client.update_task(
                    task_id,
                    {"status": status.value}
                )
            
            # Update tracker
            self.status_tracker.update_status(task_id, status, notes)
            
        except Exception as e:
            logger.error(f"Failed to update task status: {str(e)}")
            raise
    
    async def _create_nowcerts_task(self, 
                                   commitment: Commitment,
                                   call_data: Dict) -> Dict:
        """Create task in NowCerts"""
        task_data = {
            "type": commitment.type,
            "description": commitment.description,
            "due_date": commitment.due_date.isoformat(),
            "priority": commitment.priority,
            "source": {
                "type": "call",
                "id": call_data["id"],
                "date": call_data["date"]
            },
            "requires_approval": commitment.requires_approval
        }
        
        try:
            task = await self.nowcerts_client.create_task(task_data)
            logger.info(f"Created NowCerts task: {task['id']}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to create NowCerts task: {str(e)}")
            raise
    
    async def _create_close_task(self, 
                                commitment: Commitment,
                                call_data: Dict) -> Dict:
        """Create task in Close"""
        task_data = {
            "lead_id": call_data["lead_id"],
            "text": commitment.description,
            "due_date": commitment.due_date.isoformat(),
            "status": "open"
        }
        
        try:
            task = await self.close_client.create_task(task_data)
            logger.info(f"Created Close task: {task['id']}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to create Close task: {str(e)}")
            raise 