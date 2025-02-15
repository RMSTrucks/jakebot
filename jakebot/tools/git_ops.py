"""Git operations automation tool"""
import subprocess
import sys
import argparse
from typing import List, Optional
from enum import Enum
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitOps:
    """Git operations automation"""
    
    class BranchType(Enum):
        FEATURE = 'feature'
        BUGFIX = 'bugfix'
        HOTFIX = 'hotfix'
        
    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()
        
    def run_command(self, command: List[str]) -> str:
        """Run git command and return output"""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            raise
    
    def create_feature(self, name: str) -> str:
        """Create new feature branch"""
        # Ensure clean working directory
        if self.has_uncommitted_changes():
            raise ValueError("Working directory not clean")
            
        # Update develop branch
        self.run_command(['git', 'checkout', 'develop'])
        self.run_command(['git', 'pull', 'origin', 'develop'])
        
        # Create feature branch
        branch_name = f"feature/{name}"
        self.run_command(['git', 'checkout', '-b', branch_name])
        
        logger.info(f"Created feature branch: {branch_name}")
        return branch_name
    
    def commit_changes(self, message: str, type_: str = 'feat'):
        """Commit changes with conventional commit message"""
        if not self.has_uncommitted_changes():
            logger.info("No changes to commit")
            return
            
        # Stage changes
        self.run_command(['git', 'add', '.'])
        
        # Create conventional commit message
        full_message = f"{type_}: {message}"
        self.run_command(['git', 'commit', '-m', full_message])
        
        logger.info(f"Committed changes: {full_message}")
    
    def push_changes(self, branch: Optional[str] = None):
        """Push changes to remote"""
        if branch is None:
            branch = self.current_branch()
            
        self.run_command(['git', 'push', 'origin', branch])
        logger.info(f"Pushed changes to {branch}")
    
    def create_pull_request(self, title: str, body: str):
        """Create pull request using GitHub CLI"""
        try:
            self.run_command([
                'gh', 'pr', 'create',
                '--title', title,
                '--body', body,
                '--base', 'develop'
            ])
            logger.info("Created pull request")
        except subprocess.CalledProcessError:
            logger.error("Failed to create PR. Is GitHub CLI installed?")
            raise
    
    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes"""
        result = self.run_command(['git', 'status', '--porcelain'])
        return bool(result)
    
    def current_branch(self) -> str:
        """Get current branch name"""
        return self.run_command(['git', 'branch', '--show-current'])
    
    def create_release(self, version: str):
        """Create a new release"""
        # Ensure we're on main
        self.run_command(['git', 'checkout', 'main'])
        self.run_command(['git', 'pull', 'origin', 'main'])
        
        # Merge develop
        self.run_command(['git', 'merge', 'develop'])
        
        # Create and push tag
        tag = f"v{version}"
        self.run_command(['git', 'tag', '-a', tag, '-m', f"Release {tag}"])
        self.run_command(['git', 'push', 'origin', tag])
        
        logger.info(f"Created release {tag}")

def main():
    parser = argparse.ArgumentParser(description="Git operations automation")
    parser.add_argument('command', choices=['feature', 'commit', 'push', 'pr', 'release'])
    parser.add_argument('--name', help="Feature name or commit message")
    parser.add_argument('--type', help="Commit type", default='feat')
    parser.add_argument('--version', help="Release version")
    
    args = parser.parse_args()
    git_ops = GitOps()
    
    try:
        if args.command == 'feature':
            if not args.name:
                parser.error("Feature name required")
            git_ops.create_feature(args.name)
            
        elif args.command == 'commit':
            if not args.name:
                parser.error("Commit message required")
            git_ops.commit_changes(args.name, args.type)
            
        elif args.command == 'push':
            git_ops.push_changes()
            
        elif args.command == 'pr':
            if not args.name:
                parser.error("PR title required")
            git_ops.create_pull_request(args.name, "")
            
        elif args.command == 'release':
            if not args.version:
                parser.error("Version required")
            git_ops.create_release(args.version)
            
    except Exception as e:
        logger.error(f"Operation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 