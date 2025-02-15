"""Core functionality tests"""
import pytest
from datetime import datetime

@pytest.mark.integration
class TestCoreFlow:
    """Test core business flows"""
    
    async def test_call_to_task(self, workflow_manager):
        """Test complete flow from call to task creation"""
        # Test call processing
        call_data = {
            'transcript': "I'll update the policy tomorrow",
            'customer_id': 'test_123'
        }
        result = await workflow_manager.process_call(call_data)
        
        # Verify commitment detected
        assert len(result.commitments) > 0
        
        # Verify task created in both systems
        task = result.tasks[0]
        assert task['id']
        assert await workflow_manager.verify_task_sync(task['id']) 