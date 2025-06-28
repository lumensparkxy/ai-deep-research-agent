#!/usr/bin/env python3
"""
Test runner script for Deep Research Agent.
Provides convenient commands for running tests.
"""

import sys
import subprocess
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent


def run_command(cmd, description):
    """Run a command and handle the output."""
    print(f"\n🔬 {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def main():
    """Main test runner function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test runner for Deep Research Agent")
    parser.add_argument(
        "--all", "-a", 
        action="store_true", 
        help="Run all tests"
    )
    parser.add_argument(
        "--session", "-s", 
        action="store_true", 
        help="Run SessionManager tests only"
    )
    parser.add_argument(
        "--coverage", "-c", 
        action="store_true", 
        help="Run tests with coverage report"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    python_cmd = PROJECT_ROOT / ".venv" / "bin" / "python"
    cmd = [str(python_cmd), "-m", "pytest"]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    # Determine which tests to run
    if args.session:
        cmd.append("tests/test_session_manager.py")
        description = "Running SessionManager Tests"
    elif args.all:
        cmd.append("tests/")
        description = "Running All Tests"
    else:
        # Default: run all tests
        cmd.append("tests/")
        description = "Running All Tests (default)"
    
    # Run the tests
    success = run_command(cmd, description)
    
    if success:
        print("\n✅ All tests passed!")
        if args.coverage:
            print("\n📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
