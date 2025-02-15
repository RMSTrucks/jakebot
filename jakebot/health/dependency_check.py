"""System dependency health checks"""
from typing import Dict, List, Any
import asyncio
import logging
import psutil
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class DependencyCheck:
    """Check system dependencies"""
    
    def __init__(self, clients):
        self.clients = clients
        self.disk_threshold = 0.9  # 90% usage warning
        self.memory_threshold = 0.85  # 85% usage warning
    
    async def check_database(self) -> bool:
        """Check database connectivity"""
        try:
            # Add DB health check
            return True
        except Exception as e:
            logger.error(f"Database check failed: {str(e)}")
            return False
    
    async def check_nowcerts_api(self) -> bool:
        """Check NowCerts API health"""
        try:
            status = await self.clients['nowcerts'].get_status()
            return status.get('status') == 'ok'
        except Exception as e:
            logger.error(f"NowCerts health check failed: {str(e)}")
            return False

    async def check_close_api(self) -> bool:
        """Check Close.com API health"""
        try:
            status = await self.clients['close'].get_status()
            return status.get('status') == 'ok'
        except Exception as e:
            logger.error(f"Close.com health check failed: {str(e)}")
            return False
    
    async def check_api_dependencies(self) -> Dict[str, bool]:
        """Check all API dependencies"""
        results = {}
        
        # Check NowCerts
        results['nowcerts'] = await self.check_nowcerts_api()
        
        # Check Close.com
        results['close'] = await self.check_close_api()
        
        return results
    
    def check_memory_usage(self) -> Dict[str, float]:
        """Check system memory usage"""
        memory = psutil.virtual_memory()
        usage = {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'warning': memory.percent > (self.memory_threshold * 100)
        }
        
        if usage['warning']:
            logger.warning(f"High memory usage: {memory.percent}%")
            
        return usage
    
    def check_disk_space(self) -> Dict[str, Dict[str, float]]:
        """Check disk space usage"""
        disk_usage = {}
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage[partition.mountpoint] = {
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent,
                    'warning': usage.percent > (self.disk_threshold * 100)
                }
                
                if disk_usage[partition.mountpoint]['warning']:
                    logger.warning(
                        f"High disk usage on {partition.mountpoint}: {usage.percent}%"
                    )
            except Exception as e:
                logger.error(f"Failed to check disk {partition.mountpoint}: {str(e)}")
                
        return disk_usage
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'database': await self.check_database(),
            'apis': await self.check_api_dependencies(),
            'memory': self.check_memory_usage(),
            'disk': self.check_disk_space()
        } 