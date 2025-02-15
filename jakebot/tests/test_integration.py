"""Integration tests for JakeBot"""
import pytest
from datetime import datetime, timedelta
import responses
import json
from unittest.mock import patch

from jakebot.ai_agents.commitment_detector import CommitmentDetector
from jakebot.integrations.close.client import CloseClient
from jakebot.integrations.nowcerts.client import NowCertsClient

class TestIntegration:
    @responses.activate
    def test_full_workflow(self, mock_config, sample_transcripts):
        """Test complete workflow from transcript to commitments"""
        # Setup API mocks
        responses.add(
            responses.GET,
            "https://api.close.com/api/v1/activity/call/call_123",
            json={"id": "call_123", "note": sample_transcripts['policy_update']},
            status=200
        )
        
        responses.add(
            responses.GET,
            "https://api.nowcerts.com/api/v1/policies/policy_123",
            json={"id": "policy_123", "status": "active"},
            status=200
        )
        
        # Initialize components
        detector = CommitmentDetector()
        close_client = CloseClient(api_key=mock_config.CLOSE_API_KEY)
        nowcerts_client = NowCertsClient(api_key=mock_config.NOWCERTS_API_KEY)
        
        # Process transcript
        transcript = sample_transcripts['policy_update']
        commitments = detector.detect_commitments(transcript)
        
        # Verify commitments
        assert len(commitments) >= 3  # Should detect at least 3 commitments
        
        # Verify commitment types
        commitment_types = [c.type for c in commitments]
        assert 'policy_update' in commitment_types
        assert 'follow_up' in commitment_types
        assert 'document_sending' in commitment_types
        
        # Verify timing
        for commitment in commitments:
            assert commitment.due_date > datetime.now()
            if commitment.type == 'policy_update':
                assert commitment.requires_approval == True
                assert commitment.priority == 'high'
    
    @responses.activate
    def test_error_handling(self, mock_config, sample_transcripts):
        """Test error handling in the integration"""
        # Setup API error responses
        responses.add(
            responses.GET,
            "https://api.close.com/api/v1/activity/call/call_123",
            json={"error": "API Error"},
            status=500
        )
        
        responses.add(
            responses.GET,
            "https://api.nowcerts.com/api/v1/policies/policy_123",
            json={"error": "API Error"},
            status=500
        )
        
        # Initialize components
        detector = CommitmentDetector()
        
        # Process transcript
        transcript = sample_transcripts['policy_update']
        commitments = detector.detect_commitments(transcript)
        
        # Verify error handling
        assert len(commitments) > 0  # Should still detect commitments despite API errors
        
        # Verify logging
        # TODO: Add log capture and verification
    
    def test_pii_handling(self, mock_config, sample_transcripts):
        """Test PII detection and handling"""
        # Add PII to transcript
        transcript = sample_transcripts['policy_update'].replace(
            "Jake from",
            "Jake from. My social is 123-45-6789 and my phone is (555) 123-4567"
        )
        
        detector = CommitmentDetector()
        commitments = detector.detect_commitments(transcript)
        
        # Verify PII is not in commitments
        for commitment in commitments:
            assert "123-45-6789" not in commitment.description
            assert "555-123-4567" not in commitment.description 