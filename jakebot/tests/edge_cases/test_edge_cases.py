"""Edge case tests for JakeBot"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from jakebot.workflow.workflow_manager import WorkflowManager
from jakebot.workflow.task_lifecycle import TaskLifecycleManager
from jakebot.sync.system_sync import SystemSynchronizer
from jakebot.exceptions import (
    TaskSyncError, NowCertsAPIError, CloseAPIError, PerformanceError, TransactionError
)

@pytest.mark.edge_cases
class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    async def test_concurrent_updates(self, workflow_manager):
        """Test handling concurrent task updates"""
        # Create initial task
        task = await workflow_manager.create_task({
            'type': 'test',
            'description': 'Concurrent test'
        })
        
        # Simulate concurrent updates
        updates = [
            {'status': 'in_progress', 'notes': 'Update 1'},
            {'status': 'completed', 'notes': 'Update 2'},
            {'status': 'needs_review', 'notes': 'Update 3'}
        ]
        
        # Run updates concurrently
        tasks = [
            workflow_manager.update_task(task['id'], update)
            for update in updates
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify only one update succeeded
        successful_updates = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_updates) == 1
    
    async def test_system_outage_recovery(self, workflow_manager, mock_clients):
        """Test recovery from system outages"""
        # Simulate NowCerts outage
        mock_clients['nowcerts'].create_task.side_effect = [
            NowCertsAPIError("Service unavailable", "SRV001"),
            NowCertsAPIError("Service unavailable", "SRV001"),
            {'id': 'task_123'}  # Succeeds on third try
        ]
        
        # Attempt task creation
        task = await workflow_manager.create_task({
            'type': 'test',
            'description': 'Outage test'
        })
        
        assert task['id'] == 'task_123'
        assert mock_clients['nowcerts'].create_task.call_count == 3
    
    async def test_data_consistency(self, workflow_manager, mock_clients):
        """Test data consistency during sync failures"""
        # Create task
        task = await workflow_manager.create_task({
            'type': 'test',
            'description': 'Consistency test'
        })
        
        # Simulate sync failure
        mock_clients['close'].create_task.side_effect = CloseAPIError(
            "Sync failed", "SYNC001"
        )
        
        # Attempt update
        with pytest.raises(TaskSyncError):
            await workflow_manager.update_task(task['id'], {'status': 'completed'})
        
        # Verify original task unchanged
        current_task = await workflow_manager.get_task(task['id'])
        assert current_task['status'] == task['status']
    
    async def test_performance_degradation(self, workflow_manager, mock_clients):
        """Test handling of performance degradation"""
        # Simulate slow API responses
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(2)  # Simulate delay
            return {'id': 'task_123'}
        
        mock_clients['nowcerts'].create_task.side_effect = slow_response
        
        # Attempt task creation with timeout
        with pytest.raises(PerformanceError):
            await asyncio.wait_for(
                workflow_manager.create_task({
                    'type': 'test',
                    'description': 'Performance test'
                }),
                timeout=1.0
            )
    
    async def test_invalid_state_transitions(self, workflow_manager):
        """Test invalid task state transitions"""
        # Create task
        task = await workflow_manager.create_task({
            'type': 'test',
            'description': 'State transition test'
        })
        
        # Attempt invalid transition
        with pytest.raises(ValidationError):
            await workflow_manager.update_task(
                task['id'],
                {'status': 'completed'}  # Can't go directly to completed
            )
    
    async def test_duplicate_detection(self, workflow_manager):
        """Test handling of duplicate tasks"""
        # Create original task
        task1 = await workflow_manager.create_task({
            'type': 'test',
            'description': 'Duplicate test',
            'external_id': 'ext_123'
        })
        
        # Attempt to create duplicate
        task2 = await workflow_manager.create_task({
            'type': 'test',
            'description': 'Duplicate test',
            'external_id': 'ext_123'
        })
        
        # Should return existing task
        assert task1['id'] == task2['id']
    
    async def test_memory_pressure(self, workflow_manager):
        """Test behavior under memory pressure"""
        # Create many tasks
        tasks = []
        for i in range(1000):
            task = await workflow_manager.create_task({
                'type': 'test',
                'description': f'Memory test {i}'
            })
            tasks.append(task)
            
        # Verify memory metrics
        assert workflow_manager.performance_monitor.memory_metrics['current_memory'] > 0
    
    async def test_rollback(self, workflow_manager, mock_clients):
        """Test transaction rollback"""
        # Setup mock to fail after partial completion
        mock_clients['nowcerts'].create_task.return_value = {'id': 'task_123'}
        mock_clients['close'].create_task.side_effect = CloseAPIError(
            "API Error", "API001"
        )
        
        # Attempt operation that should trigger rollback
        with pytest.raises(TransactionError) as exc:
            await workflow_manager.create_synced_task({
                'type': 'test',
                'description': 'Rollback test'
            })
            
        # Verify rollback occurred
        assert mock_clients['nowcerts'].delete_task.called
        assert 'needs_rollback' in exc.value.details 