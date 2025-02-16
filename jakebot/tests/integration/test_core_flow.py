"""Core functionality tests"""
import pytest
from datetime import datetime
from unittest.mock import patch
import time

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

    @pytest.mark.integration
    @patch('jakebot.integrations.close.client.CloseClient.get_call')
    async def test_call_transcript_retrieval(self, mock_get_call, workflow_manager):
        """Test retrieval of call transcript from Close API"""
        mock_get_call.return_value = {
            "recording_transcript": {
                "summary_text": "This is a test transcript."
            }
        }
        
        call_id = "test_call_id"  # Replace with a valid test call ID
        call_data = await workflow_manager.get_call_transcript(call_id)
        
        assert "recording_transcript" in call_data
        assert "summary_text" in call_data["recording_transcript"]

    @pytest.mark.integration
    @patch('jakebot.integrations.close.client.send_slack_notification')
    async def test_task_creation_sends_notification(self, mock_send_notification, workflow_manager):
        """Test that task creation sends a notification to Slack"""
        lead_id = "test_lead_id"
        description = "Follow up with the customer"
        
        await workflow_manager.create_task(lead_id, description)
        
        mock_send_notification.assert_called_once_with(f"New task created for lead {lead_id}: {description}")

@pytest.mark.integration
def test_search_tasks():
    """Test the search functionality for tasks"""
    tasks = [
        {"description": "Follow up with the customer"},
        {"description": "Send invoice"},
        {"description": "Update policy"}
    ]
    
    result = search_tasks(tasks, "invoice")
    assert len(result) == 1
    assert result[0]["description"] == "Send invoice"

@pytest.mark.integration
async def test_performance_get_call(workflow_manager):
    """Test the performance of retrieving call details"""
    call_id = "test_call_id"  # Replace with a valid test call ID
    
    start_time = time.time()
    await workflow_manager.get_call_transcript(call_id)
    duration = time.time() - start_time
    
    assert duration < 2  # Ensure the call retrieval is under 2 seconds