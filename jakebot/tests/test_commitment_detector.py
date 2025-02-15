import pytest
from datetime import datetime, timedelta

from ai_agents.commitment_detector import CommitmentDetector, Commitment

@pytest.fixture
def detector():
    return CommitmentDetector()

class TestCommitmentDetector:
    def test_basic_send_commitment(self, detector):
        transcript = "Agent: I will send you the policy documents tomorrow."
        commitments = detector.detect_commitments(transcript)
        
        assert len(commitments) == 1
        assert commitments[0].system == "NowCerts"
        assert "policy documents" in commitments[0].description.lower()
        assert commitments[0].due_date > datetime.now()

    def test_multiple_commitments(self, detector):
        transcript = """
        Agent: I'll send you the documents tomorrow.
        Customer: Great, thanks.
        Agent: And I'll call you back next week to follow up.
        """
        commitments = detector.detect_commitments(transcript)
        
        assert len(commitments) == 2
        assert any(c.system == "NowCerts" for c in commitments)
        assert any(c.system == "CRM" for c in commitments)

    def test_due_date_parsing(self, detector):
        reference_date = datetime(2024, 1, 1, 10, 0)  # Jan 1, 2024, 10:00 AM
        
        # Test "today"
        today_date = detector.parse_due_date("today", reference_date)
        assert today_date.day == reference_date.day
        assert today_date.hour == 17  # EOD
        
        # Test "tomorrow"
        tomorrow_date = detector.parse_due_date("tomorrow", reference_date)
        assert tomorrow_date.day == reference_date.day + 1
        
        # Test "next week"
        next_week_date = detector.parse_due_date("next week", reference_date)
        assert next_week_date.day == reference_date.day + 7

    def test_priority_classification(self, detector):
        # Test high priority
        urgent_commitment = Commitment(
            description="Urgent: Send policy documents",
            system="NowCerts"
        )
        assert detector.classify_priority(urgent_commitment) == "high"
        
        # Test low priority
        low_commitment = Commitment(
            description="Send documents when you can",
            system="NowCerts"
        )
        assert detector.classify_priority(low_commitment) == "low"

    def test_approval_requirements(self, detector):
        transcript = """
        Agent: I'll update your policy coverage amounts.
        Customer: Great.
        Agent: And I'll send you the updated documents.
        """
        commitments = detector.detect_commitments(transcript)
        
        # Policy updates should require approval
        update_commitments = [c for c in commitments if "update" in c.description.lower()]
        assert all(c.requires_approval for c in update_commitments)
        
        # Document sending should not require approval
        send_commitments = [c for c in commitments if "send" in c.description.lower()]
        assert all(not c.requires_approval for c in send_commitments) 