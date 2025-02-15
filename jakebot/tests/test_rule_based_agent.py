import pytest
from datetime import datetime
from ai_agents import Commitment

def test_extract_commitments(rule_based_agent, sample_transcript):
    commitments = rule_based_agent.extract_commitments(sample_transcript)
    
    assert len(commitments) == 2
    assert isinstance(commitments[0], Commitment)
    
    # Check first commitment (send documents)
    assert "send" in commitments[0].description.lower()
    assert "documents" in commitments[0].description.lower()
    assert commitments[0].system == "NowCerts"
    
    # Check second commitment (update policy)
    assert "update" in commitments[1].description.lower()
    assert "policy" in commitments[1].description.lower()
    assert commitments[1].system == "NowCerts"
    assert commitments[1].requires_approval == True

def test_empty_transcript(rule_based_agent):
    commitments = rule_based_agent.extract_commitments("")
    assert len(commitments) == 0

def test_no_commitments_transcript(rule_based_agent):
    transcript = "Customer: How are you? Agent: I'm fine, thank you."
    commitments = rule_based_agent.extract_commitments(transcript)
    assert len(commitments) == 0 