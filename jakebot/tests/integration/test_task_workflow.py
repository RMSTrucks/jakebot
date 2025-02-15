"""Integration tests for task workflow"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from jakebot.workflow.task_lifecycle import TaskLifecycleManager
from jakebot.workflow.task_status import TaskStatus
from jakebot.exceptions import TaskError, ValidationError
from jakebot.config import JakeBotConfig

@pytest.fixture
def mock_clients():
    """Mock API clients"""
    return {
        'nowcerts': Mock(),
        'close': Mock()
    }

@pytest.fixture
def lifecycle_manager(mock_clients):
    """Create lifecycle manager with mocked clients"""
    config = JakeBotConfig()
    return TaskLifecycleManager(
        config,
        mock_clients['nowcerts'],
        mock_clients['close']
    )

@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        'description': 'Update vehicle coverage',
        'due_date': datetime.now() + timedelta(days=1),
        'type': 'policy_update',
        'system': 'NowCerts',
        'priority': 'high'
    }

class TestTaskWorkflow:
    async def test_complete_task_lifecycle(self, lifecycle_manager, sample_task_data):
        """Test complete task lifecycle"""
        # Setup mock responses
        lifecycle_manager.nowcerts_client.create_task.return_value = {
            'id': 'task_123',
            'status': 'pending'
        }
        
        # 1. Create task
        task = await lifecycle_manager.create_task(sample_task_data)
        assert task['id'] == 'task_123'
        
        # 2. Update to in progress
        await lifecycle_manager.update_task(
            task['id'],
            {'status': TaskStatus.IN_PROGRESS}
        )
        
        # 3. Update to needs approval
        await lifecycle_manager.update_task(
            task['id'],
            {'status': TaskStatus.NEEDS_APPROVAL}
        )
        
        # 4. Complete task
        completed_task = await lifecycle_manager.update_task(
            task['id'],
            {'status': TaskStatus.COMPLETED}
        )
        
        # Verify status history
        status_history = lifecycle_manager.status_tracker.get_task_status(task['id'])
        assert len(status_history['status_history']) == 4
    
    async def test_error_handling(self, lifecycle_manager, sample_task_data):
        """Test error handling scenarios"""
        # Test API error
        lifecycle_manager.nowcerts_client.create_task.side_effect = Exception("API Error")
        
        with pytest.raises(TaskError):
            await lifecycle_manager.create_task(sample_task_data)
        
        # Test invalid state transition
        task = {
            'id': 'task_123',
            'status': TaskStatus.COMPLETED
        }
        lifecycle_manager.status_tracker.add_task('task_123', {'task_data': task})
        
        with pytest.raises(ValidationError):
            await lifecycle_manager.update_task(
                'task_123',
                {'status': TaskStatus.IN_PROGRESS}
            )
    
    async def test_task_cancellation(self, lifecycle_manager, sample_task_data):
        """Test task cancellation"""
        # Create task
        task = await lifecycle_manager.create_task(sample_task_data)
        
        # Cancel task
        cancelled_task = await lifecycle_manager.cancel_task(
            task['id'],
            "Customer request"
        )
        
        # Verify cancellation
        status = lifecycle_manager.status_tracker.get_task_status(task['id'])
        assert status['status'] == TaskStatus.CANCELLED
        assert "Customer request" in status['status_history'][-1]['notes']
    
    async def test_metrics_tracking(self, lifecycle_manager, sample_task_data):
        """Test metrics tracking"""
        # Create task
        await lifecycle_manager.create_task(sample_task_data)
        
        # Verify metrics
        metrics = lifecycle_manager.metrics.metrics
        assert metrics['api_calls']['NowCerts']['total_calls'] > 0
        assert 'create_task' in metrics['api_calls']['NowCerts']['endpoints'] 