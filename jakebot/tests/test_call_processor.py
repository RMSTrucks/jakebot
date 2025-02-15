import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from main import CallProcessor
from ai_agents import Commitment

@pytest.fixture
def mock_integrations():
    """Mock all external integrations"""
    with patch('main.CloseIntegration') as mock_close, \
         patch('main.NowCertsIntegration') as mock_nowcerts, \
         patch('main.SlackIntegration') as mock_slack, \
         patch('main.RuleBasedAgent') as mock_agent:
        
        # Configure mock agent to return test commitments
        mock_agent.return_value.extract_commitments.return_value = [
            Commitment(
                description="Send insurance documents",
                due_date=datetime.now(),
                assignee="agent",
                requires_approval=False,
                system="NowCerts"
            )
        ]
        
        yield {
            'close': mock_close.return_value,
            'nowcerts': mock_nowcerts.return_value,
            'slack': mock_slack.return_value,
            'agent': mock_agent.return_value
        }

@pytest.fixture
def processor(mock_integrations):
    return CallProcessor()

def test_process_call_with_commitments(processor, mock_integrations):
    """Test processing a call with valid commitments"""
    
    call_metadata = {
        "lead_id": "lead_123",
        "agent_id": "agent_456",
        "agent_name": "Test Agent",
        "call_id": "call_789"
    }
    
    transcript = """
    Agent: I will send the documents tomorrow.
    Customer: Thanks.
    """
    
    processor.process_call(transcript, call_metadata)
    
    # Verify agent was called to extract commitments
    mock_integrations['agent'].extract_commitments.assert_called_once_with(transcript)
    
    # Verify task was created in CRM
    mock_integrations['close'].create_task.assert_called_once()
    
    # Verify Slack notification was sent
    mock_integrations['slack'].send_notification.assert_called()

def test_process_call_no_commitments(processor, mock_integrations):
    """Test processing a call with no commitments found"""
    
    # Configure mock agent to return no commitments
    mock_integrations['agent'].extract_commitments.return_value = []
    
    call_metadata = {
        "lead_id": "lead_123",
        "agent_id": "agent_456",
        "agent_name": "Test Agent",
        "call_id": "call_789"
    }
    
    transcript = "Customer: How are you? Agent: I'm fine, thanks."
    
    processor.process_call(transcript, call_metadata)
    
    # Verify no tasks were created
    mock_integrations['close'].create_task.assert_not_called()
    mock_integrations['nowcerts'].create_task.assert_not_called()

def test_process_call_with_approval_needed(processor, mock_integrations):
    """Test processing a call with a commitment requiring approval"""
    
    # Configure mock agent to return a commitment needing approval
    mock_integrations['agent'].extract_commitments.return_value = [
        Commitment(
            description="Update policy coverage",
            due_date=datetime.now(),
            assignee="agent",
            requires_approval=True,
            system="NowCerts"
        )
    ]
    
    call_metadata = {
        "lead_id": "lead_123",
        "agent_id": "agent_456",
        "agent_name": "Test Agent",
        "call_id": "call_789"
    }
    
    transcript = "Agent: I'll update your policy coverage."
    
    processor.process_call(transcript, call_metadata)
    
    # Verify approval request was sent to Slack
    assert any(
        "Approval Needed" in str(call.args[0])
        for call in mock_integrations['slack'].send_notification.call_args_list
    )

def test_process_call_error_handling(processor, mock_integrations):
    """Test error handling during call processing"""
    
    # Make the Close integration raise an error
    mock_integrations['close'].create_task.side_effect = Exception("API Error")
    
    call_metadata = {
        "lead_id": "lead_123",
        "agent_id": "agent_456",
        "agent_name": "Test Agent",
        "call_id": "call_789"
    }
    
    transcript = "Agent: I will send the documents."
    
    # Should not raise exception
    processor.process_call(transcript, call_metadata)
    
    # Verify error notification was sent to Slack
    assert any(
        "Error" in str(call.args[0])
        for call in mock_integrations['slack'].send_notification.call_args_list
    )

def test_process_call_multiple_commitments(processor, mock_integrations):
    """Test processing a call with multiple commitments"""
    
    # Configure mock agent to return multiple commitments
    mock_integrations['agent'].extract_commitments.return_value = [
        Commitment(
            description="Send insurance documents",
            system="NowCerts"
        ),
        Commitment(
            description="Call back next week",
            system="CRM"
        )
    ]
    
    call_metadata = {
        "lead_id": "lead_123",
        "agent_id": "agent_456",
        "agent_name": "Test Agent",
        "call_id": "call_789"
    }
    
    transcript = """
    Agent: I will send the documents and call you back next week.
    Customer: Perfect, thanks.
    """
    
    processor.process_call(transcript, call_metadata)
    
    # Verify two tasks were created
    assert mock_integrations['close'].create_task.call_count == 2
    
    # Verify summary includes both commitments
    summary_calls = [
        call for call in mock_integrations['slack'].send_notification.call_args_list
        if "Call Summary" in str(call.args[0])
    ]
    assert len(summary_calls) == 1
    summary_text = str(summary_calls[0].args[0])
    assert "Commitments found: 2" in summary_text

def test_process_call_with_date_parsing(processor, mock_integrations):
    """Test processing commitments with different date formats"""
    
    # Configure mock agent to return commitments with different date formats
    mock_integrations['agent'].extract_commitments.return_value = [
        Commitment(
            description="Send documents tomorrow",
            due_date=datetime.now(),  # Would be tomorrow in real implementation
            system="CRM"
        ),
        Commitment(
            description="Follow up next week",
            due_date=datetime.now(),  # Would be next week in real implementation
            system="CRM"
        ),
        Commitment(
            description="Update policy by end of day",
            due_date=datetime.now(),  # Would be EOD in real implementation
            system="NowCerts"
        )
    ]
    
    call_metadata = {
        "lead_id": "lead_123",
        "agent_id": "agent_456",
        "agent_name": "Test Agent",
        "call_id": "call_789"
    }
    
    transcript = """
    Agent: I will send the documents tomorrow, follow up with you next week,
    and update the policy by end of day.
    Customer: Sounds good.
    """
    
    processor.process_call(transcript, call_metadata)
    
    # Verify tasks were created with correct dates
    assert mock_integrations['close'].create_task.call_count == 3
    
    # Verify all tasks appear in Slack summary
    summary_calls = [
        call for call in mock_integrations['slack'].send_notification.call_args_list
        if "Call Summary" in str(call.args[0])
    ]
    assert len(summary_calls) == 1
    summary_text = str(summary_calls[0].args[0])
    assert "Commitments found: 3" in summary_text 