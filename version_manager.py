#!/usr/bin/env python3
"""
Version management utility for Deep Research Agent.
This script helps manage version numbers across the project.
"""

import re
import sys
import argparse
from pathlib import Path
from typing import Tuple, Optional


class VersionManager:
    """Manages version numbers across the project."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent
        self.version_files = {
            '__init__.py': self.project_root / '__init__.py',
        }
    
    def get_current_version(self) -> str:
        """Get the current version from __init__.py."""
        init_file = self.version_files['__init__.py']
        if not init_file.exists():
            raise FileNotFoundError(f"__init__.py not found at {init_file}")
        
        content = init_file.read_text()
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            raise ValueError("Version not found in __init__.py")
        
        return match.group(1)
    
    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse semantic version string into components."""
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$', version)
        if not match:
            raise ValueError(f"Invalid semantic version: {version}")
        
        major, minor, patch = match.groups()[:3]
        return int(major), int(minor), int(patch)
    
    def format_version(self, major: int, minor: int, patch: int, prerelease: str = None, build: str = None) -> str:
        """Format version components into semantic version string."""
        version = f"{major}.{minor}.{patch}"
        if prerelease:
            version += f"-{prerelease}"
        if build:
            version += f"+{build}"
        return version
    
    def bump_version(self, component: str, prerelease: str = None) -> str:
        """
        Bump version component and return new version.
        
        Args:
            component: 'major', 'minor', or 'patch'
            prerelease: Optional prerelease identifier (e.g., 'alpha', 'beta', 'rc')
        """
        current = self.get_current_version()
        major, minor, patch = self.parse_version(current)
        
        if component == 'major':
            major += 1
            minor = 0
            patch = 0
        elif component == 'minor':
            minor += 1
            patch = 0
        elif component == 'patch':
            patch += 1
        else:
            raise ValueError(f"Invalid component: {component}. Use 'major', 'minor', or 'patch'")
        
        return self.format_version(major, minor, patch, prerelease)
    
    def update_version_in_file(self, file_path: Path, new_version: str, pattern: str, replacement: str) -> None:
        """Update version in a specific file."""
        if not file_path.exists():
            print(f"Warning: {file_path} not found, skipping...")
            return
        
        content = file_path.read_text()
        new_content = re.sub(pattern, replacement.format(version=new_version), content)
        
        if content != new_content:
            file_path.write_text(new_content)
            print(f"Updated version in {file_path.relative_to(self.project_root)}")
        else:
            print(f"No changes needed in {file_path.relative_to(self.project_root)}")
    
    def update_all_versions(self, new_version: str) -> None:
        """Update version in __init__.py."""
        print(f"Updating version to {new_version}...")
        
        # Update __init__.py
        self.update_version_in_file(
            self.version_files['__init__.py'],
            new_version,
            r'__version__\s*=\s*["\'][^"\']+["\']',
            '__version__ = "{version}"'
        )
        
        print(f"Version update complete: {new_version}")
    
    def show_current_version(self) -> None:
        """Display current version information."""
        try:
            version = self.get_current_version()
            major, minor, patch = self.parse_version(version)
            
            print(f"Current version: {version}")
            print(f"  Major: {major}")
            print(f"  Minor: {minor}")
            print(f"  Patch: {patch}")
            
            # Show next possible versions
            print("\nNext versions:")
            print(f"  Patch: {self.bump_version('patch')}")
            print(f"  Minor: {self.bump_version('minor')}")
            print(f"  Major: {self.bump_version('major')}")
            
        except Exception as e:
            print(f"Error reading version: {e}")
            sys.exit(1)


def main():
    """Main entry point for version management."""
    parser = argparse.ArgumentParser(description="Deep Research Agent Version Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Show current version
    show_parser = subparsers.add_parser('show', help='Show current version')
    
    # Bump version
    bump_parser = subparsers.add_parser('bump', help='Bump version')
    bump_parser.add_argument('component', choices=['major', 'minor', 'patch'], 
                           help='Version component to bump')
    bump_parser.add_argument('--prerelease', help='Prerelease identifier (alpha, beta, rc)')
    bump_parser.add_argument('--dry-run', action='store_true', 
                           help='Show what would be changed without making changes')
    
    # Set specific version
    set_parser = subparsers.add_parser('set', help='Set specific version')
    set_parser.add_argument('version', help='Version to set (e.g., 1.2.3)')
    set_parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be changed without making changes')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    vm = VersionManager()
    
    if args.command == 'show':
        vm.show_current_version()
    
    elif args.command == 'bump':
        try:
            new_version = vm.bump_version(args.component, args.prerelease)
            if args.dry_run:
                print(f"Would update version to: {new_version}")
            else:
                vm.update_all_versions(new_version)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif args.command == 'set':
        try:
            # Validate version format
            vm.parse_version(args.version)
            if args.dry_run:
                print(f"Would update version to: {args.version}")
            else:
                vm.update_all_versions(args.version)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()
