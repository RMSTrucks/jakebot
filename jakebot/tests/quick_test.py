"""Quick test script for JakeBot"""
import logging
from pathlib import Path
from jakebot.config import JakeBotConfig
from jakebot.ai_agents.commitment_detector import CommitmentDetector
from jakebot.tests.data.sample_transcripts import SAMPLE_TRANSCRIPTS

def main():
    # Setup
    logging.basicConfig(level=logging.INFO)
    config = JakeBotConfig()
    detector = CommitmentDetector()
    
    # Test each transcript
    for name, transcript in SAMPLE_TRANSCRIPTS.items():
        print(f"\nTesting {name} transcript:")
        print("-" * 50)
        
        commitments = detector.detect_commitments(transcript)
        
        print(f"\nFound {len(commitments)} commitments:")
        for c in commitments:
            print(f"\n- {c.description}")
            print(f"  Due: {c.due_date}")
            print(f"  System: {c.system}")
            print(f"  Priority: {c.priority}")

if __name__ == "__main__":
    main() 