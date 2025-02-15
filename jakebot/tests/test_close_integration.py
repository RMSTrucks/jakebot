import pytest
from datetime import datetime
import responses
import json
import hmac
import hashlib
from unittest.mock import Mock, patch
from fastapi import HTTPException

from integrations.close.client import CloseClient, CloseAPIError
from api.routes.close_webhooks import handle_call_completed, process_call_async

@pytest.fixture
def close_client():
    return CloseClient(
        api_key="test_key",
        webhook_secret="test_webhook_secret"
    )

@pytest.fixture
def mock_request():
    """Mock FastAPI request object"""
    request = Mock()
    request.json = Mock(return_value={
        "data": {
            "id": "call_123",
            "lead_id": "lead_456",
            "user_id": "user_789",
            "direction": "outbound",
            "duration": 300,
            "status": "completed"
        }
    })
    return request

@pytest.fixture
def sample_call_response():
    """Sample response from Close API for call details"""
    return {
        "id": "call_123",
        "lead_id": "lead_456",
        "user_id": "user_789",
        "direction": "outbound",
        "duration": 300,
        "status": "completed",
        "note": "Agent: I will send the documents tomorrow.\nCustomer: Great, thank you."
    }

@pytest.fixture
def webhook_payload():
    return {
        "data": {
            "id": "call_123",
            "lead_id": "lead_456",
            "user_id": "user_789",
            "direction": "outbound",
            "duration": 300,
            "status": "completed",
            "note": "Agent: I will send the documents tomorrow."
        }
    }

@pytest.fixture
def webhook_signature(webhook_payload):
    """Generate valid webhook signature for testing"""
    payload_string = json.dumps(webhook_payload, separators=(',', ':'))
    return hmac.new(
        b"test_webhook_secret",
        payload_string.encode(),
        hashlib.sha256
    ).hexdigest()

class TestCloseClient:
    def test_init_with_webhook_secret(self):
        """Test client initialization with webhook secret"""
        client = CloseClient(
            api_key="test_key",
            webhook_secret="test_secret",
            max_retries=5
        )
        assert client.webhook_secret == "test_secret"
        assert client.max_retries == 5

    @responses.activate
    def test_get_call_with_retries(self, close_client):
        """Test get_call with retry mechanism"""
        # Mock first two calls to fail, third to succeed
        responses.add(
            responses.GET,
            "https://api.close.com/api/v1/activity/call/call_123",
            status=500
        )
        responses.add(
            responses.GET,
            "https://api.close.com/api/v1/activity/call/call_123",
            status=500
        )
        responses.add(
            responses.GET,
            "https://api.close.com/api/v1/activity/call/call_123",
            json={"id": "call_123", "note": "Test transcript"},
            status=200
        )
        
        response = close_client.get_call("call_123")
        assert response["id"] == "call_123"
        assert len(responses.calls) == 3

    @responses.activate
    def test_get_call_max_retries_exceeded(self, close_client):
        """Test get_call when max retries are exceeded"""
        # Mock all calls to fail
        responses.add(
            responses.GET,
            "https://api.close.com/api/v1/activity/call/call_123",
            status=500,
            body="Server Error"
        )
        
        with pytest.raises(CloseAPIError) as exc_info:
            close_client.get_call("call_123")
        
        assert "Failed to get call details" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    def test_verify_webhook_valid_signature(self, close_client, webhook_payload, webhook_signature):
        """Test webhook verification with valid signature"""
        assert close_client.verify_webhook(webhook_payload, webhook_signature) == True

    def test_verify_webhook_invalid_signature(self, close_client, webhook_payload):
        """Test webhook verification with invalid signature"""
        assert close_client.verify_webhook(webhook_payload, "invalid_signature") == False

    def test_verify_webhook_handles_errors(self, close_client):
        """Test webhook verification error handling"""
        # Test with invalid payload that can't be JSON serialized
        payload = {"data": object()}  # object() can't be JSON serialized
        assert close_client.verify_webhook(payload, "any_signature") == False

    @responses.activate
    def test_create_task(self, close_client):
        """Test creating a task in Close"""
        # Mock the API response
        responses.add(
            responses.POST,
            "https://api.close.com/api/v1/task",
            json={"id": "task_123", "lead_id": "lead_456", "text": "Send documents"},
            status=200
        )
        
        # Create a task
        response = close_client.create_task(
            lead_id="lead_456",
            description="Send documents",
            due_date=datetime.now()
        )
        
        # Verify response
        assert response["id"] == "task_123"
        assert response["lead_id"] == "lead_456"
        
        # Verify request
        assert len(responses.calls) == 1
        assert "lead_id" in responses.calls[0].request.body.decode()
        assert "text" in responses.calls[0].request.body.decode()

    @responses.activate
    def test_rate_limit_handling(self, close_client):
        """Test handling of rate limit responses from Close API"""
        # Mock rate limit response
        responses.add(
            responses.GET,
            "https://api.close.com/api/v1/activity/call/call_123",
            status=429,
            headers={"Retry-After": "2"},
            json={"error": "Rate limit exceeded"}
        )
        
        # Mock successful retry
        responses.add(
            responses.GET,
            "https://api.close.com/api/v1/activity/call/call_123",
            json={"id": "call_123", "note": "Test transcript"},
            status=200
        )
        
        response = close_client.get_call("call_123")
        assert response["id"] == "call_123"
        assert len(responses.calls) == 2

    @responses.activate
    def test_malformed_transcript_handling(self, close_client):
        """Test handling of malformed transcript data"""
        responses.add(
            responses.GET,
            "https://api.close.com/api/v1/activity/call/call_123",
            json={
                "id": "call_123",
                "note": None,  # Sometimes the API might return null
                "status": "completed"
            },
            status=200
        )
        
        response = close_client.get_call("call_123")
        assert response["id"] == "call_123"
        assert "note" in response
        assert response["note"] is None

    @responses.activate
    def test_create_task_with_priority(self, close_client):
        """Test creating tasks with different priority levels"""
        responses.add(
            responses.POST,
            "https://api.close.com/api/v1/task",
            json={"id": "task_123", "priority": "high"},
            status=200
        )
        
        response = close_client.create_task(
            lead_id="lead_456",
            description="Urgent: Update policy",
            priority="high"
        )
        
        assert response["priority"] == "high"
        request_body = json.loads(responses.calls[0].request.body.decode())
        assert request_body["priority"] == "high"

class TestCloseWebhooks:
    @pytest.mark.asyncio
    async def test_process_call_async_success(self, webhook_payload):
        """Test successful async call processing"""
        with patch('main.CallProcessor') as MockProcessor:
            mock_processor = MockProcessor.return_value
            mock_processor.process_call.return_value = {"success": True}
            
            await process_call_async(webhook_payload["data"])
            
            mock_processor.process_call.assert_called_once()
            call_args = mock_processor.process_call.call_args[1]
            assert call_args["call_metadata"]["call_id"] == "call_123"

    @pytest.mark.asyncio
    async def test_process_call_async_error(self, webhook_payload):
        """Test error handling in async call processing"""
        with patch('main.CallProcessor') as MockProcessor:
            mock_processor = MockProcessor.return_value
            mock_processor.process_call.side_effect = Exception("Processing error")
            
            # Should not raise exception (errors are logged)
            await process_call_async(webhook_payload["data"])

    @pytest.mark.asyncio
    @responses.activate
    async def test_handle_call_completed_full_flow(self, webhook_payload, webhook_signature):
        """Test the complete webhook handling flow"""
        # Mock the call details API request
        responses.add(
            responses.GET,
            "https://api.close.com/api/v1/activity/call/call_123",
            json=webhook_payload["data"],
            status=200
        )
        
        # Create mock request with payload
        mock_request = Mock()
        mock_request.json.return_value = webhook_payload
        
        # Create mock background tasks
        mock_background = Mock()
        
        response = await handle_call_completed(
            request=mock_request,
            background_tasks=mock_background,
            x_close_signature=webhook_signature
        )
        
        assert response["status"] == "success"
        assert response["call_id"] == "call_123"
        mock_background.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_call_completed_missing_fields(self):
        """Test webhook handling with missing required fields"""
        mock_request = Mock()
        mock_request.json.return_value = {"data": {}}
        
        with pytest.raises(HTTPException) as exc_info:
            await handle_call_completed(
                request=mock_request,
                background_tasks=Mock()
            )
        
        assert exc_info.value.status_code == 400
        assert "Missing required fields" in str(exc_info.value.detail)

    @responses.activate
    async def test_handle_call_completed(self, mock_request, sample_call_response):
        """Test handling a call completion webhook"""
        # Mock the Close API call for getting call details
        responses.add(
            responses.GET,
            "https://api.close.com/api/v1/activity/call/call_123",
            json=sample_call_response,
            status=200
        )
        
        # Handle the webhook
        response = await handle_call_completed(
            request=mock_request,
            x_close_signature="test_signature"
        )
        
        # Verify response
        assert response["status"] == "success"
        assert response["call_id"] == "call_123"
        
        # Verify API call was made
        assert len(responses.calls) == 1
        assert "activity/call/call_123" in responses.calls[0].request.url

    @responses.activate
    async def test_handle_call_completed_error(self, mock_request):
        """Test handling errors in call completion webhook"""
        # Mock an API error
        responses.add(
            responses.GET,
            "https://api.close.com/api/v1/activity/call/call_123",
            status=500
        )
        
        # Verify error handling
        with pytest.raises(HTTPException) as exc_info:
            await handle_call_completed(
                request=mock_request,
                x_close_signature="test_signature"
            )
        
        assert exc_info.value.status_code == 500

    async def test_handle_invalid_signature(self, mock_request):
        """Test handling invalid webhook signatures"""
        # Mock verify_webhook to return False
        with patch('integrations.close.client.CloseClient.verify_webhook', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await handle_call_completed(
                    request=mock_request,
                    x_close_signature="invalid_signature"
                )
            
            assert exc_info.value.status_code == 401
            assert "Invalid webhook signature" in str(exc_info.value.detail)

    @responses.activate
    async def test_handle_missing_data(self, mock_request):
        """Test handling webhooks with missing data"""
        # Override mock request to return incomplete data
        mock_request.json.return_value = {"data": {}}
        
        # Verify error handling for missing data
        with pytest.raises(HTTPException) as exc_info:
            await handle_call_completed(request=mock_request)
        
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_handle_long_transcript(self, webhook_payload):
        """Test processing of long transcripts"""
        # Create a long transcript with multiple potential commitments
        long_transcript = "\n".join([
            "Agent: Hello, how can I help you today?",
            "Customer: I need help with my policy.",
            "Agent: I'll help you update your policy today.",
            "Customer: Great, thanks.",
            "Agent: I'll also send you the updated documents by email.",
            "Customer: Perfect.",
            "Agent: And I'll call you next week to follow up.",
            "Customer: Sounds good.",
            # ... add more conversation
            "Agent: Is there anything else I can help you with?",
            "Customer: No, that's all. Thank you."
        ])
        
        webhook_payload["data"]["note"] = long_transcript
        
        with patch('main.CallProcessor') as MockProcessor:
            mock_processor = MockProcessor.return_value
            mock_processor.process_call.return_value = {"success": True}
            
            await process_call_async(webhook_payload["data"])
            
            # Verify the processor was called with the full transcript
            call_args = mock_processor.process_call.call_args[1]
            assert len(call_args["transcript"].split("\n")) > 5

    @pytest.mark.asyncio
    async def test_concurrent_webhook_handling(self, webhook_payload):
        """Test handling multiple webhooks concurrently"""
        import asyncio
        
        # Create multiple webhook payloads
        payloads = [
            {**webhook_payload, "data": {**webhook_payload["data"], "id": f"call_{i}"}}
            for i in range(5)
        ]
        
        # Mock the API responses
        for payload in payloads:
            responses.add(
                responses.GET,
                f"https://api.close.com/api/v1/activity/call/{payload['data']['id']}",
                json=payload["data"],
                status=200
            )
        
        # Process webhooks concurrently
        mock_background = Mock()
        tasks = [
            handle_call_completed(
                request=Mock(json=Mock(return_value=payload)),
                background_tasks=mock_background,
                x_close_signature="test_signature"
            )
            for payload in payloads
        ]
        
        # Wait for all webhooks to be processed
        results = await asyncio.gather(*tasks)
        
        # Verify all webhooks were processed
        assert len(results) == 5
        assert all(r["status"] == "success" for r in results)
        assert mock_background.add_task.call_count == 5 