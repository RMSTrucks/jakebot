from typing import List
import re
from datetime import datetime, timedelta

from .base_agent import BaseAgent, Commitment

class RuleBasedAgent(BaseAgent):
    """Agent that uses rule-based patterns to extract commitments"""
    
    def __init__(self):
        self.commitment_patterns = [
            # Common phrases that indicate commitments
            r"I will (send|email|update|call|get back to)",
            r"I'll (send|email|update|call|get back to)",
            r"Let me (send|email|update|call|get back to)",
            r"going to (send|email|update|call|get back to)"
        ]
        
        self.policy_keywords = [
            "policy", "coverage", "insurance", "certificate",
            "proof of insurance", "card", "documents"
        ]
    
    def extract_commitments(self, transcript: str) -> List[Commitment]:
        """Extract commitments using pattern matching"""
        commitments = []
        
        # Split transcript into sentences for analysis
        sentences = transcript.split('.')
        
        for sentence in sentences:
            for pattern in self.commitment_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    # Determine if it's a policy-related task
                    is_policy_task = any(keyword in sentence.lower() 
                                       for keyword in self.policy_keywords)
                    
                    commitments.append(Commitment(
                        description=sentence.strip(),
                        due_date=datetime.now() + timedelta(days=1),  # Default to tomorrow
                        assignee="agent",  # Default to the agent
                        requires_approval=is_policy_task,  # Require approval for policy tasks
                        system="NowCerts" if is_policy_task else "CRM"
                    ))
        
        return commitments 