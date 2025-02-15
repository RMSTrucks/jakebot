"""Task lifecycle management"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from jakebot.exceptions import (
    TaskError, ValidationError, TaskNotFoundError, TaskUpdateError
)
from jakebot.validation import TaskValidator
from jakebot.workflow.task_status import TaskStatus, TaskStatusTracker
from jakebot.monitoring import MetricsTracker

logger = logging.getLogger(__name__)

class TaskLifecycleManager:
    """Manage task state transitions and lifecycle"""
    
    def __init__(self, config, nowcerts_client, close_client):
        self.config = config
        self.nowcerts_client = nowcerts_client
        self.close_client = close_client
        self.status_tracker = TaskStatusTracker()
        self.metrics = MetricsTracker()
        self.validator = TaskValidator()
        
    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task"""
        try:
            # Start timing
            start_time = datetime.now()
            
            # Validate task data
            self.validator.validate_task(task_data)
            
            # Generate task ID if not provided
            task_data['id'] = task_data.get('id', f"task_{uuid.uuid4()}")
            
            # Create in appropriate system
            if task_data['system'] == 'NowCerts':
                task = await self._create_nowcerts_task(task_data)
            else:  # Close
                task = await self._create_close_task(task_data)
            
            # Track status
            self.status_tracker.add_task(task['id'], {
                'task_data': task,
                'system': task_data['system'],
                'created_at': datetime.now()
            })
            
            # Track metrics
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics.track_api_call(
                task_data['system'],
                'create_task',
                success=True,
                duration=duration
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            self.metrics.track_error('task_creation_error', {
                'error': str(e),
                'task_data': task_data
            })
            raise TaskError(f"Failed to create task: {str(e)}")
    
    async def update_task(self, 
                         task_id: str, 
                         updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task"""
        try:
            # Get current task status
            current_task = self.status_tracker.get_task_status(task_id)
            
            # Validate state transition
            if 'status' in updates:
                self._validate_state_transition(
                    current_task['status'],
                    updates['status']
                )
            
            # Update in appropriate system
            if current_task['system'] == 'NowCerts':
                updated_task = await self.nowcerts_client.update_task(
                    task_id,
                    updates
                )
            else:  # Close
                updated_task = await self.close_client.update_task(
                    task_id,
                    updates
                )
            
            # Update status tracker
            self.status_tracker.update_status(
                task_id,
                updates.get('status', current_task['status']),
                notes=updates.get('notes')
            )
            
            return updated_task
            
        except TaskNotFoundError:
            logger.error(f"Task not found: {task_id}")
            raise
        except Exception as e:
            logger.error(f"Failed to update task: {str(e)}")
            raise TaskUpdateError(f"Failed to update task: {str(e)}")
    
    async def cancel_task(self, task_id: str, reason: str) -> Dict[str, Any]:
        """Cancel a task"""
        try:
            # Get current task
            current_task = self.status_tracker.get_task_status(task_id)
            
            # Update status to cancelled
            updates = {
                'status': TaskStatus.CANCELLED,
                'notes': f"Cancelled: {reason}"
            }
            
            # Cancel in appropriate system
            if current_task['system'] == 'NowCerts':
                cancelled_task = await self.nowcerts_client.update_task(
                    task_id,
                    updates
                )
            else:  # Close
                cancelled_task = await self.close_client.update_task(
                    task_id,
                    updates
                )
            
            # Update status tracker
            self.status_tracker.update_status(
                task_id,
                TaskStatus.CANCELLED,
                notes=reason
            )
            
            return cancelled_task
            
        except Exception as e:
            logger.error(f"Failed to cancel task: {str(e)}")
            raise TaskError(f"Failed to cancel task: {str(e)}")
    
    def _validate_state_transition(self, 
                                 current_status: TaskStatus,
                                 new_status: TaskStatus):
        """Validate task state transition"""
        valid_transitions = {
            TaskStatus.PENDING: {
                TaskStatus.IN_PROGRESS,
                TaskStatus.CANCELLED
            },
            TaskStatus.IN_PROGRESS: {
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.NEEDS_APPROVAL,
                TaskStatus.CANCELLED
            },
            TaskStatus.NEEDS_APPROVAL: {
                TaskStatus.IN_PROGRESS,
                TaskStatus.COMPLETED,
                TaskStatus.REJECTED,
                TaskStatus.CANCELLED
            }
        }
        
        if new_status not in valid_transitions.get(current_status, set()):
            raise ValidationError(
                f"Invalid state transition from {current_status} to {new_status}"
            )
    
    async def _create_nowcerts_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create task in NowCerts"""
        try:
            return await self.nowcerts_client.create_task(task_data)
        except Exception as e:
            logger.error(f"NowCerts task creation failed: {str(e)}")
            raise
    
    async def _create_close_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create task in Close"""
        try:
            return await self.close_client.create_task(task_data)
        except Exception as e:
            logger.error(f"Close task creation failed: {str(e)}")
            raise 