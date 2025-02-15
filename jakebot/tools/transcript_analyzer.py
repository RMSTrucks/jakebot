"""Analyze transcripts to discover patterns and categories"""
import logging
from typing import List, Dict, Set
from collections import Counter
import re
from pathlib import Path
import json
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np

logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    """Analyze transcripts for patterns and categories"""
    
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.common_patterns = Counter()
        self.commitment_phrases = Counter()
        self.categories = {}
        
    def analyze_transcripts(self, transcripts: List[Dict]) -> Dict:
        """Analyze a collection of transcripts"""
        
        analysis_results = {
            'total_transcripts': len(transcripts),
            'patterns': [],
            'categories': {},
            'commitment_phrases': [],
            'statistics': {}
        }
        
        # Extract and categorize common patterns
        all_patterns = self._extract_patterns(transcripts)
        analysis_results['patterns'] = self._rank_patterns(all_patterns)
        
        # Categorize transcripts
        analysis_results['categories'] = self._categorize_transcripts(transcripts)
        
        # Find common commitment phrases
        analysis_results['commitment_phrases'] = self._find_commitment_phrases(transcripts)
        
        # Generate statistics
        analysis_results['statistics'] = self._generate_statistics(transcripts)
        
        return analysis_results
    
    def _extract_patterns(self, transcripts: List[Dict]) -> Counter:
        """Extract common language patterns"""
        patterns = Counter()
        
        for transcript in transcripts:
            text = transcript['transcript']
            doc = self.nlp(text)
            
            # Look for commitment-like patterns
            for sent in doc.sents:
                # Agent statements starting with "I will" or "I'll"
                if sent.text.strip().startswith("Agent:"):
                    commitment_matches = re.finditer(
                        r"I(?:'ll| will) (?:\w+\s?){1,5}",
                        sent.text,
                        re.IGNORECASE
                    )
                    for match in commitment_matches:
                        patterns[match.group(0)] += 1
                        
                # Look for time-related phrases
                time_matches = re.finditer(
                    r"(?:today|tomorrow|next week|within|by|end of|morning|afternoon)",
                    sent.text,
                    re.IGNORECASE
                )
                for match in time_matches:
                    patterns[match.group(0)] += 1
        
        return patterns
    
    def _categorize_transcripts(self, transcripts: List[Dict]) -> Dict:
        """Categorize transcripts by content"""
        categories = {
            'policy_changes': [],
            'claims': [],
            'quotes': [],
            'general_inquiry': [],
            'document_requests': [],
            'urgent_matters': []
        }
        
        # Keywords for each category
        category_keywords = {
            'policy_changes': ['change', 'update', 'modify', 'adjust', 'coverage'],
            'claims': ['claim', 'accident', 'damage', 'incident', 'loss'],
            'quotes': ['quote', 'estimate', 'price', 'cost', 'premium'],
            'document_requests': ['document', 'certificate', 'proof', 'id card'],
            'urgent_matters': ['urgent', 'asap', 'emergency', 'immediately']
        }
        
        for transcript in transcripts:
            text = transcript['transcript'].lower()
            
            # Score each category
            scores = {cat: 0 for cat in categories.keys()}
            
            for category, keywords in category_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        scores[category] += 1
            
            # Assign to highest scoring category (or general_inquiry if no clear winner)
            max_score = max(scores.values())
            if max_score > 0:
                top_category = max(scores.items(), key=lambda x: x[1])[0]
                categories[top_category].append(transcript['id'])
            else:
                categories['general_inquiry'].append(transcript['id'])
        
        return categories
    
    def _find_commitment_phrases(self, transcripts: List[Dict]) -> List[Dict]:
        """Find and analyze common commitment phrases"""
        commitment_phrases = Counter()
        
        commitment_starters = [
            r"I(?:'ll| will)",
            r"(?:let|going to) (?:me|us)",
            r"(?:can|should) (?:get|have)",
        ]
        
        for transcript in transcripts:
            text = transcript['transcript']
            for starter in commitment_starters:
                matches = re.finditer(
                    f"{starter} (?:\\w+\\s?){{1,10}}",
                    text,
                    re.IGNORECASE
                )
                for match in matches:
                    commitment_phrases[match.group(0)] += 1
        
        # Convert to ranked list
        ranked_phrases = [
            {
                'phrase': phrase,
                'count': count,
                'confidence': min(count / len(transcripts) * 2, 1.0)
            }
            for phrase, count in commitment_phrases.most_common(50)
        ]
        
        return ranked_phrases
    
    def _generate_statistics(self, transcripts: List[Dict]) -> Dict:
        """Generate statistical analysis of transcripts"""
        stats = {
            'total_transcripts': len(transcripts),
            'avg_duration': np.mean([t['duration'] for t in transcripts]),
            'commitment_density': {},  # commitments per minute
            'common_timeframes': Counter(),
            'direction_split': Counter([t['direction'] for t in transcripts])
        }
        
        # Analyze timeframes
        timeframe_pattern = r"(?:today|tomorrow|next week|within \d+ \w+)"
        for transcript in transcripts:
            timeframes = re.findall(timeframe_pattern, transcript['transcript'], re.IGNORECASE)
            stats['common_timeframes'].update(timeframes)
        
        return stats
    
    def _rank_patterns(self, patterns: Counter, min_count: int = 3) -> List[Dict]:
        """Rank and filter patterns"""
        return [
            {
                'pattern': pattern,
                'count': count,
                'confidence': min(count / len(patterns) * 2, 1.0)
            }
            for pattern, count in patterns.most_common()
            if count >= min_count
        ]

    def save_analysis(self, analysis_results: Dict, output_file: str):
        """Save analysis results to file"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(analysis_results, f, indent=2) 