"""Complete system integration tests"""
import pytest
from datetime import datetime

@pytest.mark.integration
class TestCompleteFlow:
    """Test complete system flow"""
    
    async def test_commitment_to_task_flow(self, system):
        """Test complete flow from commitment to task completion"""
        # Create test call data
        call_data = {
            'transcript': "I'll update your policy tomorrow",
            'customer_id': 'test_123'
        }
        
        # Process call
        result = await system.process_call(call_data)
        
        # Verify commitment detected
        assert len(result.commitments) > 0
        
        # Verify tasks created
        assert len(result.tasks) > 0
        
        # Verify task synced
        task = result.tasks[0]
        assert await system.verify_task_sync(task.id) 