"""Main workflow manager"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from jakebot.exceptions import WorkflowError, APIError
from jakebot.monitoring import MetricsTracker
from jakebot.utils.retry import with_retry

logger = logging.getLogger(__name__)

class WorkflowManager:
    """Manage core business workflows"""
    
    def __init__(self, config):
        self.config = config
        self.metrics = MetricsTracker()
        self.nowcerts_client = None  # Will be initialized from config
        self.close_client = None     # Will be initialized from config
    
    @with_retry()
    async def process_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process call data and create tasks"""
        try:
            start_time = datetime.now()
            
            # Detect commitments
            commitments = await self.detect_commitments(call_data['transcript'])
            
            # Create tasks for each commitment
            tasks = []
            for commitment in commitments:
                task = await self.create_task(commitment)
                tasks.append(task)
            
            # Track metrics
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics.track_api_call(
                'workflow',
                'process_call',
                duration=duration,
                success=True
            )
            
            return {
                'commitments': commitments,
                'tasks': tasks
            }
            
        except Exception as e:
            logger.error(f"Failed to process call: {str(e)}")
            self.metrics.track_error('call_processing_error', {
                'error': str(e),
                'call_data': call_data
            })
            raise WorkflowError(
                str(e),
                step='process_call',
                context={'call_data': call_data}
            ) 