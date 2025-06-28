#!/bin/bash
# Version release script for Deep Research Agent
# This script automates the release process including version bumping,
# changelog updates, and git tagging.

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
PYTHON_EXE="$PROJECT_ROOT/.venv/bin/python"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  show                    Show current version"
    echo "  bump <major|minor|patch> [--dry-run]  Bump version"
    echo "  set <version> [--dry-run]             Set specific version"
    echo "  release <major|minor|patch>           Full release process"
    echo ""
    echo "Options:"
    echo "  --dry-run              Show what would be done without making changes"
    echo "  --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 show                 # Show current version"
    echo "  $0 bump patch           # Bump patch version (0.1.0 -> 0.1.1)"
    echo "  $0 bump minor --dry-run # Show what minor bump would do"
    echo "  $0 set 1.0.0           # Set version to 1.0.0"
    echo "  $0 release patch       # Full release: bump + tag + push"
}

# Function to check if git is clean
check_git_status() {
    if ! git diff-index --quiet HEAD --; then
        print_error "Git working directory is not clean. Please commit or stash changes."
        exit 1
    fi
}

# Function to update changelog
update_changelog() {
    local version="$1"
    local date=$(date +%Y-%m-%d)
    
    print_status "Updating CHANGELOG.md for version $version"
    
    # Create a temporary file
    temp_file=$(mktemp)
    
    # Read the changelog and update it
    if [[ -f "CHANGELOG.md" ]]; then
        # Replace [Unreleased] with the new version
        sed "s/## \[Unreleased\]/## [$version] - $date/" CHANGELOG.md > "$temp_file"
        
        # Add new [Unreleased] section at the top
        {
            head -n 7 "$temp_file"  # Keep header and unreleased line
            echo ""
            echo "## [Unreleased]"
            echo ""
            echo "### Added"
            echo ""
            echo "### Changed"
            echo ""
            echo "### Fixed"
            echo ""
            tail -n +8 "$temp_file"  # Add rest of file
        } > CHANGELOG.md
        
        rm "$temp_file"
        print_success "Updated CHANGELOG.md"
    else
        print_warning "CHANGELOG.md not found, skipping changelog update"
    fi
}

# Function to create git tag
create_git_tag() {
    local version="$1"
    local tag_name="v$version"
    
    print_status "Creating git tag $tag_name"
    
    # Check if tag already exists
    if git tag -l | grep -q "^$tag_name$"; then
        print_error "Tag $tag_name already exists"
        exit 1
    fi
    
    # Create annotated tag
    git tag -a "$tag_name" -m "Release version $version"
    print_success "Created tag $tag_name"
}

# Function to show current version
show_version() {
    print_status "Getting current version information..."
    "$PYTHON_EXE" "$PROJECT_ROOT/version_manager.py" show
}

# Function to bump version
bump_version() {
    local component="$1"
    local dry_run="$2"
    
    if [[ "$dry_run" == "--dry-run" ]]; then
        print_status "DRY RUN: Would bump $component version"
        "$PYTHON_EXE" "$PROJECT_ROOT/version_manager.py" bump "$component" --dry-run
    else
        print_status "Bumping $component version"
        "$PYTHON_EXE" "$PROJECT_ROOT/version_manager.py" bump "$component"
        print_success "Version bumped successfully"
    fi
}

# Function to set specific version
set_version() {
    local version="$1"
    local dry_run="$2"
    
    if [[ "$dry_run" == "--dry-run" ]]; then
        print_status "DRY RUN: Would set version to $version"
        "$PYTHON_EXE" "$PROJECT_ROOT/version_manager.py" set "$version" --dry-run
    else
        print_status "Setting version to $version"
        "$PYTHON_EXE" "$PROJECT_ROOT/version_manager.py" set "$version"
        print_success "Version set successfully"
    fi
}

# Function to perform full release
full_release() {
    local component="$1"
    
    print_status "Starting full release process for $component version bump"
    
    # Check git status
    check_git_status
    
    # Get current version for comparison
    current_version=$("$PYTHON_EXE" "$PROJECT_ROOT/version_manager.py" show | grep "Current version:" | cut -d' ' -f3)
    print_status "Current version: $current_version"
    
    # Bump version
    print_status "Bumping $component version"
    "$PYTHON_EXE" "$PROJECT_ROOT/version_manager.py" bump "$component"
    
    # Get new version
    new_version=$("$PYTHON_EXE" "$PROJECT_ROOT/version_manager.py" show | grep "Current version:" | cut -d' ' -f3)
    print_success "Version bumped from $current_version to $new_version"
    
    # Update changelog
    update_changelog "$new_version"
    
    # Stage changes
    print_status "Staging changes for commit"
    git add __init__.py CHANGELOG.md
    
    # Commit changes
    print_status "Committing version bump"
    git commit -m "Bump version to $new_version"
    
    # Create tag
    create_git_tag "$new_version"
    
    print_success "Release $new_version completed successfully!"
    print_status "To publish, run: git push origin main --tags"
}

# Main script logic
main() {
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check if Python script exists
    if [[ ! -f "version_manager.py" ]]; then
        print_error "version_manager.py not found. Please run this script from the project root."
        exit 1
    fi
    
    # Parse command line arguments
    case "${1:-}" in
        "show")
            show_version
            ;;
        "bump")
            if [[ -z "${2:-}" ]]; then
                print_error "Please specify component to bump: major, minor, or patch"
                show_usage
                exit 1
            fi
            bump_version "$2" "${3:-}"
            ;;
        "set")
            if [[ -z "${2:-}" ]]; then
                print_error "Please specify version to set"
                show_usage
                exit 1
            fi
            set_version "$2" "${3:-}"
            ;;
        "release")
            if [[ -z "${2:-}" ]]; then
                print_error "Please specify component to bump for release: major, minor, or patch"
                show_usage
                exit 1
            fi
            full_release "$2"
            ;;
        "--help"|"-h"|"help")
            show_usage
            ;;
        "")
            print_error "No command specified"
            show_usage
            exit 1
            ;;
        *)
            print_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
