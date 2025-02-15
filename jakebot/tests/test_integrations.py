import pytest
import responses
from integrations import CloseIntegration, NowCertsIntegration, SlackIntegration

@pytest.fixture
def mock_responses():
    with responses.RequestsMock() as rsps:
        yield rsps

def test_close_create_task(mock_responses, mock_close_integration):
    mock_responses.add(
        responses.POST,
        "https://api.close.com/api/v1/task",
        json={"id": "task_123", "status": "open"},
        status=200
    )
    
    response = mock_close_integration.create_task({
        "description": "Send documents",
        "due_date": "2024-01-01"
    })
    
    assert response["id"] == "task_123"
    assert response["status"] == "open"

def test_nowcerts_update_policy(mock_responses, mock_nowcerts_integration):
    mock_responses.add(
        responses.PUT,
        "https://api.nowcerts.com/api/policy/123",
        json={"status": "updated"},
        status=200
    )
    
    response = mock_nowcerts_integration.update_policy("123", {
        "vehicle": {"make": "Toyota", "model": "Camry"}
    })
    
    assert response["status"] == "updated"

def test_slack_notification(mock_responses, mock_slack_integration):
    mock_responses.add(
        responses.POST,
        "https://test.slack.com/webhook",
        json={"ok": True},
        status=200
    )
    
    response = mock_slack_integration.send_notification(
        "Test message",
        channel="#test-channel"
    )
    
    assert response["status"] == "sent" 