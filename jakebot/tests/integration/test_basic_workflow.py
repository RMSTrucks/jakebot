"""Basic workflow integration tests"""
import pytest
from datetime import datetime

@pytest.mark.integration
class TestBasicWorkflow:
    async def test_basic_task_creation(self, workflow_manager):
        """Test basic task creation and sync"""
        # Create task
        task = await workflow_manager.create_task({
            'type': 'policy_update',
            'description': 'Update vehicle coverage',
            'due_date': datetime.now(),
            'system': 'NowCerts'
        })
        
        # Verify task created
        assert task['id']
        assert task['status'] == 'pending'
        
        # Verify sync
        assert await workflow_manager.verify_sync(task['id']) 