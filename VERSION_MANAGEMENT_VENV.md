# Version Management Guide

This guide explains how to maintain version numbering for the Deep Research Agent project using the virtual environment setup.

## Current Setup

Your project uses semantic versioning (MAJOR.MINOR.PATCH) with the following configuration:

- **Version Source**: `__init__.py` (single source of truth)
- **Settings Integration**: `config/settings.py` reads from `__init__.py` automatically  
- **Python Environment**: `.venv` virtual environment
- **Current Version**: 0.1.0

## Tools Available

### 1. Version Manager Script (`version_manager.py`)
Direct access to version management functionality:

```bash
# Show current version
.venv/bin/python version_manager.py show

# Bump versions
.venv/bin/python version_manager.py bump patch    # 0.1.0 -> 0.1.1
.venv/bin/python version_manager.py bump minor    # 0.1.0 -> 0.2.0
.venv/bin/python version_manager.py bump major    # 0.1.0 -> 1.0.0

# Set specific version
.venv/bin/python version_manager.py set 1.0.0

# Dry run (see what would happen)
.venv/bin/python version_manager.py bump patch --dry-run
```

### 2. Simple Version Wrapper (`manage_version.py`)
Simplified interface that automatically uses the virtual environment:

```bash
# Show current version
./manage_version.py show

# Bump versions
./manage_version.py bump patch
./manage_version.py bump minor
./manage_version.py bump major

# Set specific version
./manage_version.py set 1.0.0
```

### 3. Release Script (`release.sh`)
Complete release automation with git integration:

```bash
# Show current version
./release.sh show

# Bump version only
./release.sh bump patch [--dry-run]

# Full release (bump + changelog + git tag)
./release.sh release patch

# Set specific version
./release.sh set 1.0.0 [--dry-run]
```

## Semantic Versioning Guide

Follow these guidelines for version bumps:

### Patch Version (0.1.0 → 0.1.1)
- Bug fixes
- Small improvements
- Documentation updates
- Internal refactoring

### Minor Version (0.1.0 → 0.2.0)
- New features
- New functionality
- Backwards-compatible changes
- Significant improvements

### Major Version (0.1.0 → 1.0.0)
- Breaking changes
- Major architecture changes
- API changes that break backwards compatibility
- Major milestones

## Recommended Workflow

### For Development
1. Make your changes
2. Test thoroughly
3. Update CHANGELOG.md manually if needed
4. Use the simple wrapper for quick version checks:
   ```bash
   ./manage_version.py show
   ```

### For Releases
1. Ensure all changes are committed
2. Use the full release process:
   ```bash
   ./release.sh release patch  # or minor/major
   ```
3. Push to repository:
   ```bash
   git push origin main --tags
   ```

### For Quick Version Bumps
```bash
# Quick patch bump
./manage_version.py bump patch

# Check what would happen first
./release.sh bump minor --dry-run
```

## Virtual Environment Integration

All tools are configured to use your `.venv` virtual environment automatically:

- **Python Executable**: `.venv/bin/python`
- **Environment Type**: venv
- **Python Version**: 3.13.3

The tools will automatically use the correct Python interpreter, so you don't need to activate the virtual environment manually.

## Files That Get Updated

When you change the version, these files are automatically updated:

1. `__init__.py` - Version definition (single source of truth)
2. `CHANGELOG.md` - Release history (during full release)

The `config/settings.py` automatically reads the version from `__init__.py` at runtime.

## Best Practices

1. **Always use dry-run first** for major changes:
   ```bash
   ./release.sh bump major --dry-run
   ```

2. **Keep CHANGELOG.md updated** between releases by adding entries under `[Unreleased]`

3. **Use descriptive commit messages** when the release script commits changes

4. **Test after version bumps** to ensure everything still works:
   ```bash
   ./manage_version.py bump patch
   .venv/bin/python main.py --help  # Test that version displays correctly
   ```

5. **Use appropriate version bumps** based on the semantic versioning guide above

## Troubleshooting

### Virtual Environment Issues
If you get errors about missing Python executable:
```bash
# Recreate virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Permission Issues
Make scripts executable:
```bash
chmod +x release.sh manage_version.py
```

### Git Issues
Ensure git is configured and working directory is clean before releases.

## Examples

### Simple Version Check
```bash
$ ./manage_version.py show
Current version: 0.1.0
  Major: 0
  Minor: 1
  Patch: 0

Next versions:
  Patch: 0.1.1
  Minor: 0.2.0
  Major: 1.0.0
```

### Full Release Process
```bash
$ ./release.sh release patch
[INFO] Starting full release process for patch version bump
[INFO] Current version: 0.1.0
[INFO] Bumping patch version
[SUCCESS] Version bumped from 0.1.0 to 0.1.1
[INFO] Updating CHANGELOG.md for version 0.1.1
[SUCCESS] Updated CHANGELOG.md
[INFO] Staging changes for commit
[INFO] Committing version bump
[INFO] Creating git tag v0.1.1
[SUCCESS] Created tag v0.1.1
[SUCCESS] Release 0.1.1 completed successfully!
[INFO] To publish, run: git push origin main --tags
```

This system gives you complete control over version management while ensuring consistency across all project files and integration with your virtual environment.
