"""System synchronization logic"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from jakebot.exceptions import SyncError
from jakebot.workflow.task_status import TaskStatus
from jakebot.monitoring import MetricsTracker

logger = logging.getLogger(__name__)

class SystemSynchronizer:
    """Synchronize task state between systems"""
    
    def __init__(self, nowcerts_client, close_client, metrics_tracker: Optional[MetricsTracker] = None):
        self.nowcerts_client = nowcerts_client
        self.close_client = close_client
        self.metrics_tracker = metrics_tracker
        self.task_mappings: Dict[str, Dict] = {}
    
    async def sync_task(self, primary_task_id: str, primary_system: str) -> Dict:
        """Synchronize a task between systems"""
        try:
            # Get task details from primary system
            if primary_system == "NowCerts":
                primary_task = await self.nowcerts_client.get_task(primary_task_id)
                secondary_system = "Close"
                secondary_client = self.close_client
            else:
                primary_task = await self.close_client.get_task(primary_task_id)
                secondary_system = "NowCerts"
                secondary_client = self.nowcerts_client
            
            # Check if we have a mapping
            if primary_task_id not in self.task_mappings:
                # Create task in secondary system
                secondary_task = await secondary_client.create_task({
                    "type": primary_task["type"],
                    "description": primary_task["description"],
                    "status": primary_task["status"],
                    "due_date": primary_task["due_date"],
                    "linked_task_id": primary_task_id
                })
                
                # Store mapping
                self.task_mappings[primary_task_id] = {
                    "primary_system": primary_system,
                    "primary_task_id": primary_task_id,
                    "secondary_system": secondary_system,
                    "secondary_task_id": secondary_task["id"],
                    "last_synced": datetime.now()
                }
            else:
                # Update existing task in secondary system
                mapping = self.task_mappings[primary_task_id]
                await secondary_client.update_task(
                    mapping["secondary_task_id"],
                    {
                        "status": primary_task["status"],
                        "description": primary_task["description"]
                    }
                )
                
                mapping["last_synced"] = datetime.now()
            
            return self.task_mappings[primary_task_id]
            
        except Exception as e:
            logger.error(f"Failed to sync task {primary_task_id}: {str(e)}")
            if self.metrics_tracker:
                self.metrics_tracker.track_error(
                    "sync_error",
                    {
                        "task_id": primary_task_id,
                        "primary_system": primary_system,
                        "error": str(e)
                    }
                )
            raise SyncError(f"Failed to sync task: {str(e)}")
    
    async def verify_sync(self, task_id: str) -> bool:
        """Verify task synchronization"""
        if task_id not in self.task_mappings:
            return False
            
        mapping = self.task_mappings[task_id]
        
        # Get tasks from both systems
        if mapping["primary_system"] == "NowCerts":
            primary_task = await self.nowcerts_client.get_task(mapping["primary_task_id"])
            secondary_task = await self.close_client.get_task(mapping["secondary_task_id"])
        else:
            primary_task = await self.close_client.get_task(mapping["primary_task_id"])
            secondary_task = await self.nowcerts_client.get_task(mapping["secondary_task_id"])
        
        # Compare critical fields
        return (
            primary_task["status"] == secondary_task["status"] and
            primary_task["description"] == secondary_task["description"]
        ) 