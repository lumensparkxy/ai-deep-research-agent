#!/usr/bin/env python3
"""
Documentation Builder for Deep Research Agent

This script generates HTML documentation using pdoc from all Python modules
with proper docstrings. The documentation is created as static HTML files
that can be served by any web server.

Usage:
    python build_docs.py [--open] [--serve] [--clean]
    
Options:
    --open    Open the documentation in browser after building
    --serve   Start a local web server to view docs (port 8080)
    --clean   Clean existing documentation before building
"""

import argparse
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time


def clean_docs(docs_dir: Path):
    """Remove existing documentation directory."""
    if docs_dir.exists():
        print(f"🧹 Cleaning existing documentation in {docs_dir}")
        shutil.rmtree(docs_dir)
        

def build_documentation(project_root: Path, docs_dir: Path):
    """Build HTML documentation using pdoc."""
    print("📚 Building documentation with pdoc...")
    
    # Ensure we're in the project directory
    os.chdir(project_root)
    
    # Set Python path for proper imports
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    # Build command
    cmd = [
        str(project_root / '.venv' / 'bin' / 'pdoc'),
        'core',          # Document the core package
        'config',        # Document the config package  
        'utils',         # Document the utils package
        '-o', str(docs_dir),
        '--favicon', 'https://raw.githubusercontent.com/python/cpython/main/Lib/test/test_email/data/PyBanner048.gif',
        '--footer-text', 'Deep Research Agent API Documentation',
        '--logo', 'https://via.placeholder.com/150x75/3776ab/ffffff?text=DRA',
        '--logo-link', 'https://github.com/yourusername/deep-research-agent',
        '--search',      # Enable search functionality
        '--show-source', # Show source code
        '--math'         # Enable math rendering
    ]
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Documentation built successfully in {docs_dir}")
            print(f"   Main page: {docs_dir / 'index.html'}")
            return True
        else:
            print(f"❌ Documentation build failed:")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running pdoc: {e}")
        return False


def serve_docs(docs_dir: Path, port: int = 8080):
    """Start a local web server to serve documentation."""
    if not docs_dir.exists():
        print(f"❌ Documentation directory {docs_dir} not found")
        return
        
    os.chdir(docs_dir)
    
    class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
        """HTTP handler that doesn't log every request."""
        def log_message(self, format, *args):
            pass  # Suppress logging
    
    try:
        server = HTTPServer(('localhost', port), QuietHTTPRequestHandler)
        print(f"🌐 Serving documentation at http://localhost:{port}")
        print("   Press Ctrl+C to stop the server")
        
        # Open browser
        webbrowser.open(f"http://localhost:{port}")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use")
            print(f"   Try a different port or stop the existing server")
        else:
            print(f"❌ Server error: {e}")


def create_readme(docs_dir: Path):
    """Create a README file for the documentation."""
    readme_content = """# Deep Research Agent - API Documentation

This directory contains the auto-generated API documentation for the Deep Research Agent project.

## 📁 Structure

- `index.html` - Main documentation page
- `core/` - Core module documentation
- `config/` - Configuration module documentation  
- `utils/` - Utility module documentation
- `search.js` - Search functionality

## 🌐 Viewing Documentation

### Local File
Simply open `index.html` in your web browser.

### Local Server
For best experience with search and navigation:

```bash
# Using Python's built-in server
python -m http.server 8080

# Or use the build script
python build_docs.py --serve
```

Then visit: http://localhost:8080

## 🔄 Rebuilding

To regenerate the documentation:

```bash
python build_docs.py --clean
```

## 📝 Documentation Coverage

The documentation includes:

- ✅ **Classes**: All major classes with complete docstrings
- ✅ **Methods**: Public methods with parameters and return types
- ✅ **Examples**: Usage examples where applicable  
- ✅ **Type Hints**: Full type annotation support
- ✅ **Source Code**: Viewable source for all modules

---

*Generated with [pdoc](https://pdoc.dev) - Python API documentation generator*
"""
    
    readme_path = docs_dir / 'README.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"📄 Created documentation README: {readme_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Build API documentation for Deep Research Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--open', action='store_true',
        help='Open documentation in browser after building'
    )
    parser.add_argument(
        '--serve', action='store_true',
        help='Start local web server to view documentation'
    )
    parser.add_argument(
        '--clean', action='store_true',
        help='Clean existing documentation before building'
    )
    parser.add_argument(
        '--port', type=int, default=8080,
        help='Port for web server (default: 8080)'
    )
    
    args = parser.parse_args()
    
    # Get project paths
    project_root = Path(__file__).parent.absolute()
    docs_dir = project_root / 'html_docs'
    
    print("🚀 Deep Research Agent Documentation Builder")
    print(f"   Project: {project_root}")
    print(f"   Output:  {docs_dir}")
    print()
    
    # Clean if requested
    if args.clean:
        clean_docs(docs_dir)
    
    # Build documentation
    success = build_documentation(project_root, docs_dir)
    
    if success:
        # Create README
        create_readme(docs_dir)
        
        # Open browser if requested
        if args.open and not args.serve:
            index_path = docs_dir / 'index.html'
            if index_path.exists():
                print(f"🌐 Opening {index_path} in browser...")
                webbrowser.open(f"file://{index_path}")
        
        # Serve if requested
        if args.serve:
            serve_docs(docs_dir, args.port)
            
        print("\n✨ Documentation build completed!")
        print(f"   📂 Location: {docs_dir}")
        print(f"   🌐 Open: file://{docs_dir / 'index.html'}")
        print(f"   🖥️  Serve: python build_docs.py --serve")
        
    else:
        print("\n❌ Documentation build failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
