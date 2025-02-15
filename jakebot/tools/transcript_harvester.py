"""Tool to harvest and anonymize Close.com call transcripts for testing"""
import logging
from typing import List, Dict, Optional
import re
from datetime import datetime, timedelta
import json
from pathlib import Path

from jakebot.integrations.close.client import CloseClient
from jakebot.config import JakeBotConfig

logger = logging.getLogger(__name__)

class TranscriptAnonymizer:
    """Anonymize sensitive information in transcripts"""
    
    def __init__(self):
        self.pii_patterns = {
            'phone': [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Standard phone
                r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',     # (555) 555-5555
            ],
            'ssn': [
                r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',   # SSN
            ],
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            'address': [
                r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\.?',
            ],
            'name': [
                r'(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+[A-Z][a-z]+',  # Titles with names
            ]
        }
        
    def anonymize(self, text: str) -> str:
        """Anonymize PII in text"""
        for pii_type, patterns in self.pii_patterns.items():
            for pattern in patterns:
                text = re.sub(
                    pattern,
                    f"[REDACTED_{pii_type.upper()}]",
                    text
                )
        return text

class TranscriptHarvester:
    """Harvest and process Close.com call transcripts"""
    
    def __init__(self, config: JakeBotConfig):
        self.close_client = CloseClient(api_key=config.CLOSE_API_KEY)
        self.anonymizer = TranscriptAnonymizer()
        self.output_dir = Path(__file__).parent.parent / "tests" / "data" / "real_transcripts"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def harvest_transcripts(self, 
                          days_back: int = 365,
                          min_duration: int = 60,  # minimum 1-minute calls
                          max_transcripts: int = 100) -> List[Dict]:
        """
        Harvest transcripts from Close.com
        
        Args:
            days_back: How far back to look for calls
            min_duration: Minimum call duration in seconds
            max_transcripts: Maximum number of transcripts to harvest
        """
        logger.info(f"Harvesting up to {max_transcripts} transcripts from the past {days_back} days")
        
        start_date = datetime.now() - timedelta(days=days_back)
        harvested = []
        
        try:
            # Get calls from Close
            calls = self.close_client.get_calls(
                start_date=start_date,
                min_duration=min_duration
            )
            
            for call in calls[:max_transcripts]:
                try:
                    # Get full call details with transcript
                    call_details = self.close_client.get_call(call['id'])
                    if not call_details.get('note'):  # Skip calls without transcripts
                        continue
                        
                    # Anonymize the transcript
                    anonymized_transcript = self.anonymizer.anonymize(call_details['note'])
                    
                    # Save transcript
                    transcript_data = {
                        'id': call['id'],
                        'duration': call['duration'],
                        'direction': call['direction'],
                        'date': call['date_created'],
                        'transcript': anonymized_transcript
                    }
                    
                    self._save_transcript(transcript_data)
                    harvested.append(transcript_data)
                    
                except Exception as e:
                    logger.error(f"Error processing call {call['id']}: {str(e)}")
                    continue
                    
            logger.info(f"Successfully harvested {len(harvested)} transcripts")
            return harvested
            
        except Exception as e:
            logger.error(f"Error harvesting transcripts: {str(e)}")
            return []
    
    def _save_transcript(self, transcript_data: Dict):
        """Save transcript to file"""
        filename = f"transcript_{transcript_data['id']}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(transcript_data, f, indent=2)

def main():
    """Run transcript harvester"""
    logging.basicConfig(level=logging.INFO)
    
    config = JakeBotConfig()
    harvester = TranscriptHarvester(config)
    
    # Harvest transcripts
    transcripts = harvester.harvest_transcripts(
        days_back=365,    # Last year
        min_duration=60,  # At least 1-minute calls
        max_transcripts=50  # Start with 50 transcripts
    )
    
    logger.info(f"Saved {len(transcripts)} anonymized transcripts")

if __name__ == "__main__":
    main() 