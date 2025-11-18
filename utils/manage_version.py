#!/usr/bin/env python3
"""
Simple version management wrapper that uses the virtual environment.
This makes it easy to manage versions without worrying about the Python path.
"""

import subprocess
import sys
from pathlib import Path

def run_version_manager(*args):
    """Run the version manager with the virtual environment Python."""
    script_dir = Path(__file__).parent
    venv_python = script_dir / ".venv" / "bin" / "python"
    version_manager = script_dir / "version_manager.py"
    
    if not venv_python.exists():
        print("Error: Virtual environment not found. Please create it first.")
        sys.exit(1)
    
    if not version_manager.exists():
        print("Error: version_manager.py not found.")
        sys.exit(1)
    
    # Run the version manager with the virtual environment Python
    cmd = [str(venv_python), str(version_manager)] + list(args)
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    run_version_manager(*sys.argv[1:])
