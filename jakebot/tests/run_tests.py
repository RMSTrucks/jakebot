"""Test runner with detailed output"""
import pytest
import sys
import logging
from pathlib import Path

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get test directory
    test_dir = Path(__file__).parent
    
    # Run tests with detailed output
    args = [
        str(test_dir),
        "-v",
        "--tb=short",
        "-s",
        "--show-capture=all"
    ]
    
    # Add coverage reporting
    if "--coverage" in sys.argv:
        args.extend([
            "--cov=jakebot",
            "--cov-report=term-missing",
            "--cov-report=html"
        ])
    
    pytest.main(args)

if __name__ == "__main__":
    main() 