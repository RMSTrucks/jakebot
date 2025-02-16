import requests
from typing import List, Dict, Any

class TranscriptionService:
    def __init__(self, twilio_account_sid: str, twilio_auth_token: str):
        self.twilio_account_sid = twilio_account_sid
        self.twilio_auth_token = twilio_auth_token
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/"

    def get_transcription(self, recording_sid: str) -> str:
        """Retrieve the transcription for a given recording SID."""
        url = f"{self.base_url}Recordings/{recording_sid}/Transcriptions.json"
        response = requests.get(url, auth=(self.twilio_account_sid, self.twilio_auth_token))
        
        if response.status_code == 200:
            transcription_data = response.json()
            return transcription_data['transcriptions'][0]['transcription_text']
        else:
            raise Exception(f"Failed to retrieve transcription: {response.text}")

    def search_tasks(self, tasks: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Search for tasks based on a query string."""
        return [task for task in tasks if query.lower() in task['description'].lower()]

def example_function():
    pass  # Example function 