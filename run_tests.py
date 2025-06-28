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
    
    # Priority-based test selection
    parser.add_argument(
        "--priority1", "-p1",
        action="store_true",
        help="Run only Priority 1 critical tests"
    )
    parser.add_argument(
        "--priority2", "-p2", 
        action="store_true",
        help="Run only Priority 2 important tests"
    )
    parser.add_argument(
        "--priority3", "-p3",
        action="store_true", 
        help="Run only Priority 3 nice-to-have tests"
    )
    
    # Category-based test selection
    parser.add_argument(
        "--security",
        action="store_true",
        help="Run only security tests"
    )
    parser.add_argument(
        "--integration",
        action="store_true", 
        help="Run only integration tests"
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    parser.add_argument(
        "--regression",
        action="store_true",
        help="Run only regression tests"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run only fast tests (excludes slow tests)"
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run only smoke tests for basic functionality"
    )
    parser.add_argument(
        "--core",
        action="store_true",
        help="Run only core business logic tests"
    )
    
    # Custom marker selection
    parser.add_argument(
        "--marker", "-m",
        type=str,
        help="Run tests with specific marker (e.g., 'priority1 and security')"
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    python_cmd = PROJECT_ROOT / ".venv" / "bin" / "python"
    cmd = [str(python_cmd), "-m", "pytest"]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    # Determine which tests to run based on markers
    if args.priority1:
        cmd.extend(["-m", "priority1"])
        description = "Running Priority 1 Critical Tests"
    elif args.priority2:
        cmd.extend(["-m", "priority2"])
        description = "Running Priority 2 Important Tests"
    elif args.priority3:
        cmd.extend(["-m", "priority3"])
        description = "Running Priority 3 Nice-to-Have Tests"
    elif args.security:
        cmd.extend(["-m", "security"])
        description = "Running Security Tests"
    elif args.integration:
        cmd.extend(["-m", "integration"])
        description = "Running Integration Tests"
    elif args.unit:
        cmd.extend(["-m", "unit"])
        description = "Running Unit Tests"
    elif args.regression:
        cmd.extend(["-m", "regression"])
        description = "Running Regression Tests"
    elif args.fast:
        cmd.extend(["-m", "fast"])
        description = "Running Fast Tests"
    elif args.smoke:
        cmd.extend(["-m", "smoke"])
        description = "Running Smoke Tests"
    elif args.core:
        cmd.extend(["-m", "core"])
        description = "Running Core Business Logic Tests"
    elif args.marker:
        cmd.extend(["-m", args.marker])
        description = f"Running Tests with Marker: {args.marker}"
    elif args.session:
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
