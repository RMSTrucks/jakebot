import ast
from typing import Dict
from pathlib import Path

class CodeHealthMonitor:
    """Monitor code complexity and size"""
    
    def analyze_file(self, file_path: Path) -> Dict:
        with open(file_path) as f:
            content = f.read()
            
        stats = {
            'lines': len(content.splitlines()),
            'classes': 0,
            'methods': 0,
            'max_method_lines': 0
        }
        
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                stats['classes'] += 1
            elif isinstance(node, ast.FunctionDef):
                stats['methods'] += 1
                method_lines = len(node.body)
                stats['max_method_lines'] = max(
                    stats['max_method_lines'],
                    method_lines
                )
                
        return stats

    def get_project_health(self, project_root: Path) -> Dict:
        """Analyze entire project"""
        total_stats = {
            'total_lines': 0,
            'total_files': 0,
            'large_files': [],
            'complex_methods': []
        }
        
        for file_path in project_root.rglob('*.py'):
            stats = self.analyze_file(file_path)
            total_stats['total_lines'] += stats['lines']
            total_stats['total_files'] += 1
            
            if stats['lines'] > 300:
                total_stats['large_files'].append(str(file_path))
            
            if stats['max_method_lines'] > 30:
                total_stats['complex_methods'].append(str(file_path))
                
        return total_stats 