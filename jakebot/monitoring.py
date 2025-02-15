"""Monitoring and metrics for JakeBot"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class MetricsTracker:
    """Track metrics for monitoring"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            'api_calls': {},
            'task_creation': {},
            'errors': {},
            'performance': {}
        }
        
    def track_api_call(self, system: str, endpoint: str, 
                      success: bool, duration: float):
        """Track API call metrics"""
        if system not in self.metrics['api_calls']:
            self.metrics['api_calls'][system] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_duration': 0.0,
                'endpoints': {}
            }
        
        system_metrics = self.metrics['api_calls'][system]
        system_metrics['total_calls'] += 1
        system_metrics['total_duration'] += duration
        
        if success:
            system_metrics['successful_calls'] += 1
        else:
            system_metrics['failed_calls'] += 1
        
        if endpoint not in system_metrics['endpoints']:
            system_metrics['endpoints'][endpoint] = {
                'calls': 0,
                'errors': 0
            }
        
        system_metrics['endpoints'][endpoint]['calls'] += 1
        if not success:
            system_metrics['endpoints'][endpoint]['errors'] += 1
    
    def track_error(self, error_type: str, details: Dict[str, Any]):
        """Track error occurrences"""
        if error_type not in self.metrics['errors']:
            self.metrics['errors'][error_type] = {
                'count': 0,
                'last_occurrence': None,
                'details': []
            }
        
        self.metrics['errors'][error_type]['count'] += 1
        self.metrics['errors'][error_type]['last_occurrence'] = datetime.now()
        self.metrics['errors'][error_type]['details'].append(details)
    
    def save_metrics(self, output_dir: Optional[Path] = None):
        """Save metrics to file"""
        if output_dir is None:
            output_dir = Path(__file__).parent / "metrics"
        
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"metrics_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)

class PerformanceMonitor:
    """Monitor task processing performance"""
    
    def track_task_timing(self, task_id: str, operation: str, duration: float):
        # Track operation timing
        pass
        
    def track_api_performance(self, system: str, endpoint: str, duration: float):
        # Track API call performance
        pass 