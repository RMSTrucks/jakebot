"""Run transcript analysis and generate report"""
import logging
from pathlib import Path
import json
from datetime import datetime

from .transcript_harvester import TranscriptHarvester
from .transcript_analyzer import TranscriptAnalyzer
from jakebot.config import JakeBotConfig

def main():
    """Run transcript analysis"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Setup
    config = JakeBotConfig()
    harvester = TranscriptHarvester(config)
    analyzer = TranscriptAnalyzer()
    
    # Harvest transcripts
    transcripts = harvester.harvest_transcripts(
        days_back=365,
        min_duration=60,
        max_transcripts=100
    )
    
    if not transcripts:
        logger.error("No transcripts found to analyze")
        return
    
    # Analyze transcripts
    analysis_results = analyzer.analyze_transcripts(transcripts)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(__file__).parent.parent / "analysis" / f"transcript_analysis_{timestamp}.json"
    
    analyzer.save_analysis(analysis_results, output_file)
    
    # Print summary
    print("\nTranscript Analysis Summary")
    print("-" * 30)
    print(f"Total Transcripts: {analysis_results['total_transcripts']}")
    print("\nTop Commitment Phrases:")
    for phrase in analysis_results['commitment_phrases'][:5]:
        print(f"- {phrase['phrase']} (count: {phrase['count']})")
    
    print("\nCategory Distribution:")
    for category, transcripts in analysis_results['categories'].items():
        print(f"- {category}: {len(transcripts)} transcripts")

if __name__ == "__main__":
    main() 