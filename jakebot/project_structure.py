# Project root (jakebot/)
#   ├── ai_agents/          # CrewAI agents and AI logic
#   ├── integrations/       # External API integrations
#   ├── automation_scripts/ # Standalone automation scripts
#   ├── n8n_workflows/     # n8n workflow configurations
#   ├── tests/             # Test cases
#   ├── docs/              # Documentation
#   └── config/            # Configuration files 

"""
Project Structure:

/jakebot
    /api
        - close.py      # Close.com API client
        - nowcerts.py   # NowCerts API client
    /workflow
        - manager.py    # Main workflow orchestration
        - task.py       # Task management
        - sync.py       # System synchronization
    /monitoring
        - health.py     # Health checks
        - metrics.py    # Performance metrics
    /utils
        - retry.py      # Retry logic
        - validation.py # Data validation
    /tests
        /integration    # Integration tests
        /unit          # Unit tests
""" 