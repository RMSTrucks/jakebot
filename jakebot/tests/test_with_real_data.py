"""Tests using real (anonymized) Close.com transcripts"""
import pytest
import json
from pathlib import Path
from typing import List, Dict

from jakebot.ai_agents.commitment_detector import CommitmentDetector
from jakebot.config import JakeBotConfig

class TestWithRealData:
    @pytest.fixture
    def real_transcripts(self) -> List[Dict]:
        """Load real transcripts from harvested data"""
        transcript_dir = Path(__file__).parent / "data" / "real_transcripts"
        transcripts = []
        
        for file in transcript_dir.glob("*.json"):
            with open(file) as f:
                transcripts.append(json.load(f))
        
        return transcripts
    
    def test_commitment_detection_real_data(self, real_transcripts):
        """Test commitment detection on real transcripts"""
        detector = CommitmentDetector()
        
        total_commitments = 0
        commitment_types = {}
        
        for transcript_data in real_transcripts:
            commitments = detector.detect_commitments(transcript_data['transcript'])
            total_commitments += len(commitments)
            
            # Track commitment types
            for commitment in commitments:
                commitment_types[commitment.type] = commitment_types.get(commitment.type, 0) + 1
        
        # Log statistics
        print(f"\nProcessed {len(real_transcripts)} real transcripts")
        print(f"Found {total_commitments} total commitments")
        print("\nCommitment types found:")
        for type_name, count in commitment_types.items():
            print(f"- {type_name}: {count}") 