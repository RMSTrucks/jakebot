"""Initial validation of commitment detection with real data"""
import logging
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List
import pandas as pd
from tabulate import tabulate

from jakebot.config import JakeBotConfig
from jakebot.tools.transcript_harvester import TranscriptHarvester
from jakebot.tools.transcript_analyzer import TranscriptAnalyzer
from jakebot.ai_agents.commitment_detector import CommitmentDetector

logger = logging.getLogger(__name__)

class ValidationAnalysis:
    """Analyze and validate commitment detection on real data"""
    
    def __init__(self, config: JakeBotConfig):
        self.config = config
        self.harvester = TranscriptHarvester(config)
        self.analyzer = TranscriptAnalyzer()
        self.detector = CommitmentDetector()
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        
    def run_validation(self, days_back: int = 30, sample_size: int = 20):
        """Run validation analysis on recent transcripts"""
        logger.info(f"Starting validation analysis on {sample_size} transcripts from last {days_back} days")
        
        # Collect transcripts
        transcripts = self.harvester.harvest_transcripts(
            days_back=days_back,
            max_transcripts=sample_size
        )
        
        if not transcripts:
            logger.error("No transcripts found for analysis")
            return
        
        # Analyze patterns
        analysis_results = self.analyzer.analyze_transcripts(transcripts)
        
        # Test commitment detection
        detection_results = self._test_commitment_detection(transcripts)
        
        # Combine results
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'sample_size': len(transcripts),
            'pattern_analysis': analysis_results,
            'detection_results': detection_results
        }
        
        # Save results
        self._save_results(validation_results)
        
        # Generate report
        self._generate_report(validation_results)
        
    def _test_commitment_detection(self, transcripts: List[Dict]) -> Dict:
        """Test commitment detection on transcripts"""
        results = {
            'total_commitments': 0,
            'commitments_by_type': {},
            'confidence_scores': [],
            'processing_times': [],
            'potential_issues': []
        }
        
        for transcript in transcripts:
            try:
                # Time the detection
                start_time = datetime.now()
                commitments = self.detector.detect_commitments(transcript['transcript'])
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                
                results['total_commitments'] += len(commitments)
                results['processing_times'].append(processing_time)
                
                # Track commitment types and confidence
                for commitment in commitments:
                    results['commitments_by_type'][commitment.type] = \
                        results['commitments_by_type'].get(commitment.type, 0) + 1
                    results['confidence_scores'].append(commitment.confidence)
                    
                    # Flag potential issues
                    if commitment.confidence < 0.7:
                        results['potential_issues'].append({
                            'transcript_id': transcript['id'],
                            'commitment_type': commitment.type,
                            'confidence': commitment.confidence,
                            'description': commitment.description
                        })
                        
            except Exception as e:
                logger.error(f"Error processing transcript {transcript['id']}: {str(e)}")
                continue
        
        return results
    
    def _save_results(self, results: Dict):
        """Save validation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"validation_results_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Saved validation results to {output_file}")
    
    def _generate_report(self, results: Dict):
        """Generate human-readable report"""
        report = []
        report.append("Commitment Detection Validation Report")
        report.append("=" * 40)
        report.append(f"\nSample Size: {results['sample_size']} transcripts")
        report.append(f"Total Commitments Detected: {results['detection_results']['total_commitments']}")
        
        # Commitment type distribution
        report.append("\nCommitment Types:")
        type_data = []
        for ctype, count in results['detection_results']['commitments_by_type'].items():
            type_data.append([ctype, count])
        report.append(tabulate(type_data, headers=['Type', 'Count']))
        
        # Performance metrics
        times = results['detection_results']['processing_times']
        report.append(f"\nPerformance Metrics:")
        report.append(f"Average Processing Time: {sum(times)/len(times):.2f}ms")
        
        # Confidence analysis
        scores = results['detection_results']['confidence_scores']
        report.append(f"\nConfidence Analysis:")
        report.append(f"Average Confidence: {sum(scores)/len(scores):.2f}")
        report.append(f"Low Confidence Detections: {len([s for s in scores if s < 0.7])}")
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"validation_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report))
            
        logger.info(f"Generated validation report: {report_file}")
        
        # Print summary to console
        print('\n'.join(report))

def main():
    """Run initial validation"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config = JakeBotConfig()
    validator = ValidationAnalysis(config)
    
    validator.run_validation(
        days_back=30,    # Last month
        sample_size=20   # Start with 20 transcripts
    )

if __name__ == "__main__":
    main() 