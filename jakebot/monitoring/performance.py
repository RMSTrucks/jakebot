"""Performance monitoring for JakeBot"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import statistics
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data"""
    total_calls: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    durations: List[float] = field(default_factory=list)
    error_count: int = 0
    last_error: Optional[datetime] = None

class PerformanceMonitor:
    """Monitor system performance"""
    
    def __init__(self):
        self.metrics: Dict[str, Dict[str, PerformanceMetrics]] = {
            'api': {},      # API call metrics
            'sync': {},     # Sync operation metrics
            'workflow': {}  # Workflow metrics
        }
        self.thresholds = {
            'api_call': 1.0,       # seconds
            'sync': 5.0,           # seconds
            'workflow': 10.0,      # seconds
            'error_rate': 0.05,     # 5%
            'memory_threshold': 500_000_000,  # 500MB
            'concurrent_tasks': 100,
            'queue_size': 1000
        }
        
        # Add memory tracking
        self.memory_metrics = {
            'peak_memory': 0,
            'current_memory': 0
        }
    
    def track_api_call(self, system: str, endpoint: str, duration: float, success: bool):
        """Track API call performance"""
        key = f"{system}.{endpoint}"
        if key not in self.metrics['api']:
            self.metrics['api'][key] = PerformanceMetrics()
        
        metrics = self.metrics['api'][key]
        metrics.total_calls += 1
        metrics.total_duration += duration
        metrics.durations.append(duration)
        metrics.min_duration = min(metrics.min_duration, duration)
        metrics.max_duration = max(metrics.max_duration, duration)
        
        if not success:
            metrics.error_count += 1
            metrics.last_error = datetime.now()
        
        # Check thresholds
        if duration > self.thresholds['api_call']:
            logger.warning(
                f"API call to {key} exceeded threshold: {duration:.2f}s"
            )
    
    def track_sync_operation(self, operation: str, duration: float, success: bool):
        """Track sync operation performance"""
        if operation not in self.metrics['sync']:
            self.metrics['sync'][operation] = PerformanceMetrics()
        
        metrics = self.metrics['sync'][operation]
        metrics.total_calls += 1
        metrics.total_duration += duration
        metrics.durations.append(duration)
        
        if not success:
            metrics.error_count += 1
            metrics.last_error = datetime.now()
    
    def track_memory_usage(self):
        """Track memory usage"""
        import psutil
        process = psutil.Process()
        current_memory = process.memory_info().rss
        
        self.memory_metrics['current_memory'] = current_memory
        self.memory_metrics['peak_memory'] = max(
            self.memory_metrics['peak_memory'],
            current_memory
        )
        
        if current_memory > self.thresholds['memory_threshold']:
            logger.warning(f"Memory usage exceeded threshold: {current_memory}")
    
    def get_performance_report(self) -> Dict:
        """Generate performance report"""
        report = {
            'timestamp': datetime.now(),
            'api_performance': {},
            'sync_performance': {},
            'workflow_performance': {},
            'alerts': [],
            'memory_metrics': self.memory_metrics
        }
        
        # Analyze API metrics
        for key, metrics in self.metrics['api'].items():
            if metrics.total_calls == 0:
                continue
                
            avg_duration = metrics.total_duration / metrics.total_calls
            error_rate = metrics.error_count / metrics.total_calls
            
            report['api_performance'][key] = {
                'avg_duration': avg_duration,
                'min_duration': metrics.min_duration,
                'max_duration': metrics.max_duration,
                'error_rate': error_rate,
                'total_calls': metrics.total_calls,
                'p95_duration': statistics.quantiles(metrics.durations, n=20)[18]
                if len(metrics.durations) >= 20 else None
            }
            
            # Add alerts
            if error_rate > self.thresholds['error_rate']:
                report['alerts'].append({
                    'type': 'high_error_rate',
                    'system': key,
                    'error_rate': error_rate
                })
        
        return report
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            'api': {},
            'sync': {},
            'workflow': {}
        } 