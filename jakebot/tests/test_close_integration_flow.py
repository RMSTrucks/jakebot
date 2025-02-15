import pytest
from unittest.mock import patch
import responses

from main import CallProcessor
from integrations.close.client import CloseClient

@pytest.fixture
def sample_webhook_flow():
    """Sample data for testing the complete webhook flow"""
    return {
        "webhook_payload": {
            "data": {
                "id": "call_123",
                "lead_id": "lead_456",
                "user_id": "user_789",
                "direction": "outbound",
                "duration": 300,
                "status": "completed"
            }
        },
        "call_details": {
            "id": "call_123",
            "lead_id": "lead_456",
            "user_id": "user_789",
            "direction": "outbound",
            "duration": 300,
            "status": "completed",
            "note": """
                Agent: I'll send you the policy documents tomorrow.
                Customer: Great, thanks.
                Agent: I'll also update your vehicle information in the system.
                Customer: Perfect, appreciate it.
            """
        },
        "expected_commitments": [
            {
                "description": "Send policy documents",
                "system": "NowCerts",
                "due_date": "tomorrow"
            },
            {
                "description": "Update vehicle information",
                "system": "NowCerts",
                "due_date": "today"
            }
        ]
    }

@pytest.mark.asyncio
async def test_complete_webhook_flow(sample_webhook_flow):
    """Test the complete flow from webhook to task creation"""
    
    with responses.RequestsMock() as rsps:
        # Mock the Close API calls
        rsps.add(
            responses.GET,
            f"https://api.close.com/api/v1/activity/call/{sample_webhook_flow['webhook_payload']['data']['id']}",
            json=sample_webhook_flow['call_details'],
            status=200
        )
        
        # Mock task creation endpoints
        rsps.add(
            responses.POST,
            "https://api.close.com/api/v1/task",
            json={"id": "task_123"},
            status=200
        )
        
        # Process webhook
        from api.routes.close_webhooks import handle_call_completed
        response = await handle_call_completed(
            request=Mock(
                json=Mock(return_value=sample_webhook_flow['webhook_payload'])
            )
        )
        
        # Verify webhook was processed
        assert response["status"] == "success"
        
        # Verify tasks were created
        task_creation_calls = [
            call for call in rsps.calls 
            if call.request.url.endswith("/task")
        ]
        assert len(task_creation_calls) == len(sample_webhook_flow['expected_commitments']) 