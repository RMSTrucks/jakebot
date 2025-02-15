"""Validate Sprint 1 deliverables"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json

from jakebot.config import JakeBotConfig
from jakebot.workflow.workflow_manager import WorkflowManager
from jakebot.health.system_check import SystemHealthCheck

async def validate_sprint1():
    """Run comprehensive validation of Sprint 1 features"""
    config = JakeBotConfig()
    workflow = WorkflowManager(config)
    health_check = SystemHealthCheck(config, workflow.clients)
    
    results = {
        'timestamp': datetime.now(),
        'tests': {},
        'health': {},
        'issues': []
    }
    
    try:
        # 1. System Health
        results['health'] = await health_check.check_all_systems()
        
        # 2. Basic Workflow
        call_result = await workflow.handle_new_call('test_call_123')
        results['tests']['basic_workflow'] = len(call_result) > 0
        
        # 3. Error Handling
        try:
            await workflow.handle_new_call('invalid_call')
            results['tests']['error_handling'] = False
        except Exception:
            results['tests']['error_handling'] = True
        
        # 4. Task Synchronization
        task = await workflow.create_task({
            'type': 'test',
            'description': 'Validation'
        })
        results['tests']['task_sync'] = await workflow.verify_sync(task['id'])
        
        # Save results
        output_dir = Path(__file__).parent.parent / 'validation'
        output_dir.mkdir(exist_ok=True)
        
        with open(output_dir / 'sprint1_validation.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        return results
        
    except Exception as e:
        logging.error(f"Validation failed: {str(e)}")
        results['issues'].append(str(e))
        return results

if __name__ == "__main__":
    asyncio.run(validate_sprint1()) 