from typing import List
import openai
from datetime import datetime

from .base_agent import BaseAgent, Commitment

class GPTAgent(BaseAgent):
    """Agent that uses GPT to extract commitments from call transcripts"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        super().__init__(model_name)
        openai.api_key = api_key
        
    def extract_commitments(self, transcript: str) -> List[Commitment]:
        """Extract commitments from the transcript using GPT"""
        
        # Prompt engineering for commitment extraction
        prompt = """
        Extract all commitments or promises made during this call. 
        For each commitment, provide:
        - Description of the task
        - Due date (if mentioned)
        - Who is responsible
        - Whether it requires approval
        - Whether it's a CRM task or NowCerts (policy) task
        
        Respond in a structured format.
        
        Transcript:
        {transcript}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts commitments from call transcripts."},
                    {"role": "user", "content": prompt.format(transcript=transcript)}
                ]
            )
            
            # Parse response and create Commitment objects
            # For MVP, we'll do simple parsing - can be enhanced later
            commitments = []
            result = response.choices[0].message.content
            
            # TODO: Implement proper parsing of GPT response
            # For now, return a dummy commitment for testing
            dummy_commitment = Commitment(
                description="Send follow-up email",
                due_date=datetime.now(),
                assignee="agent",
                requires_approval=False,
                system="CRM"
            )
            commitments.append(dummy_commitment)
            
            return commitments
            
        except Exception as e:
            print(f"Error extracting commitments: {str(e)}")
            return [] 