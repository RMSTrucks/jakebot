import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys and Credentials
CLOSE_API_KEY = os.getenv("CLOSE_API_KEY")
NOWCERTS_API_KEY = os.getenv("NOWCERTS_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Service URLs
CLOSE_BASE_URL = "https://api.close.com/api/v1"
NOWCERTS_BASE_URL = "https://api.nowcerts.com/api"  # Update as needed

# Slack Settings
SLACK_NOTIFICATION_CHANNEL = os.getenv("SLACK_NOTIFICATION_CHANNEL", "#call-followups")
SLACK_APPROVAL_CHANNEL = os.getenv("SLACK_APPROVAL_CHANNEL", "#approvals")

# Task Settings
DEFAULT_TASK_DUE_DAYS = 1  # Number of days until task is due by default 