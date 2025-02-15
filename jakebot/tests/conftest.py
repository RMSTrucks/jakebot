"""Test configuration and fixtures"""
import pytest
from ai_agents import RuleBasedAgent
from integrations import CloseIntegration, NowCertsIntegration, SlackIntegration
from unittest.mock import Mock
from pathlib import Path
import os
import json

from jakebot.config import JakeBotConfig

@pytest.fixture
def rule_based_agent():
    return RuleBasedAgent()

@pytest.fixture
def sample_transcript():
    return """
    Agent: I will send you the insurance documents by email tomorrow.
    Customer: Great, thank you.
    Agent: I'll also update your policy with the new vehicle information.
    Customer: Perfect, appreciate it.
    """

@pytest.fixture
def mock_close_integration():
    return CloseIntegration(api_key="test_key")

@pytest.fixture
def mock_nowcerts_integration():
    return NowCertsIntegration(api_key="test_key")

@pytest.fixture
def mock_slack_integration():
    return SlackIntegration(webhook_url="https://test.slack.com/webhook")

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return JakeBotConfig(
        CLOSE_API_KEY="test_close_key",
        NOWCERTS_API_KEY="test_nowcerts_key",
        ENABLE_PII_DETECTION=True,
        REQUIRE_APPROVAL=True,
        LOG_LEVEL="DEBUG",
        MAX_RETRIES=2
    )

@pytest.fixture
def mock_close_api():
    """Mock Close.com API responses"""
    mock = Mock()
    
    # Sample successful response
    mock.get_call.return_value = {
        "id": "call_123",
        "status": "completed",
        "duration": 300,
        "direction": "outbound",
        "note": "Sample call transcript"
    }
    
    return mock

@pytest.fixture
def mock_nowcerts_api():
    """Mock NowCerts API responses"""
    mock = Mock()
    
    # Sample successful response
    mock.get_policy.return_value = {
        "id": "policy_123",
        "status": "active",
        "type": "auto",
        "effective_date": "2024-01-01"
    }
    
    # Add specific error cases
    def raise_api_error(*args, **kwargs):
        raise Exception("NowCerts API Error")
    
    mock.update_policy.side_effect = raise_api_error
    
    return mock

@pytest.fixture
def sample_transcripts():
    """Load sample transcripts from test data"""
    transcript_dir = Path(__file__).parent / "data" / "transcripts"
    transcripts = {}
    
    for file in transcript_dir.glob("*.txt"):
        with open(file) as f:
            transcripts[file.stem] = f.read() 