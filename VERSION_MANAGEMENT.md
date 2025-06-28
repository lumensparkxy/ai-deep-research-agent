# Version Management Guide

This guide explains how to maintain version numbering for the Deep Research Agent project.

## Overview

The project uses [Semantic Versioning (SemVer)](https://semver.org/) with the format `MAJOR.MINOR.PATCH`:

- **MAJOR**: Breaking changes that are not backward compatible
- **MINOR**: New features that are backward compatible
- **PATCH**: Bug fixes that are backward compatible

## Single Source of Truth

Version information is maintained in `__init__.py` as the single source of truth:

```python
__version__ = "0.1.0"
```

All other files read the version from this location:
- `config/settings.py` reads from `__init__.py`
- `pyproject.toml` references the version dynamically
- `config/settings.yaml` serves as a fallback

## Tools Available

### 1. Python Version Manager (`version_manager.py`)

A comprehensive Python script for version management:

```bash
# Show current version information
python version_manager.py show

# Bump version components
python version_manager.py bump patch      # 0.1.0 -> 0.1.1
python version_manager.py bump minor      # 0.1.0 -> 0.2.0
python version_manager.py bump major      # 0.1.0 -> 1.0.0

# Set specific version
python version_manager.py set 1.2.3

# Dry run (preview changes)
python version_manager.py bump minor --dry-run
python version_manager.py set 2.0.0 --dry-run
```

### 2. Release Script (`release.sh`)

An automated release script that handles the complete release process:

```bash
# Show current version
./release.sh show

# Bump version only
./release.sh bump patch
./release.sh bump minor --dry-run

# Set specific version
./release.sh set 1.0.0

# Full release process (bump + changelog + commit + tag)
./release.sh release patch
./release.sh release minor
./release.sh release major
```

## Release Process

### Quick Version Bump

For simple version updates:

```bash
# Bump patch version (bug fixes)
python version_manager.py bump patch

# Bump minor version (new features)
python version_manager.py bump minor

# Bump major version (breaking changes)
python version_manager.py bump major
```

### Full Release Process

For complete releases with changelog and git tagging:

```bash
# Make sure working directory is clean
git status

# Perform full release (example for patch release)
./release.sh release patch
```

This will:
1. Check that git working directory is clean
2. Bump the version number
3. Update `CHANGELOG.md` with the new version
4. Commit the changes
5. Create a git tag
6. Provide instructions for pushing

### Manual Release Steps

If you prefer manual control:

1. **Update version**:
   ```bash
   python version_manager.py bump minor
   ```

2. **Update CHANGELOG.md**:
   - Move items from `[Unreleased]` to new version section
   - Add new `[Unreleased]` section

3. **Commit changes**:
   ```bash
   git add __init__.py config/settings.yaml CHANGELOG.md
   git commit -m "Bump version to 0.2.0"
   ```

4. **Create and push tag**:
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin main --tags
   ```

## Version Numbering Guidelines

### When to Bump MAJOR (1.0.0 -> 2.0.0)
- Breaking API changes
- Removing deprecated features
- Major architectural changes
- Changes that require user action to upgrade

### When to Bump MINOR (0.1.0 -> 0.2.0)
- New features
- New research capabilities
- New configuration options
- Backward-compatible improvements

### When to Bump PATCH (0.1.1 -> 0.1.2)
- Bug fixes
- Security patches
- Documentation updates
- Internal refactoring without functional changes

## Pre-release Versions

For pre-release versions, you can use:

```bash
# Alpha release
python version_manager.py bump minor --prerelease alpha
# Results in: 0.2.0-alpha

# Beta release  
python version_manager.py bump patch --prerelease beta
# Results in: 0.1.1-beta

# Release candidate
python version_manager.py bump major --prerelease rc
# Results in: 1.0.0-rc
```

## File Locations

The version management system updates these files:

- `__init__.py` - Primary version definition
- `config/settings.yaml` - Fallback version reference
- `CHANGELOG.md` - Release history and notes
- `pyproject.toml` - Package metadata

## Best Practices

1. **Always test before releasing**: Run your test suite before bumping versions
2. **Update changelog**: Keep `CHANGELOG.md` current with each release
3. **Use semantic versioning**: Follow SemVer principles consistently
4. **Tag releases**: Always create git tags for releases
5. **Clean working directory**: Ensure no uncommitted changes before releasing

## Verification

After version updates, verify the change worked:

```bash
# Check version is consistent across files
python version_manager.py show

# Verify application reports correct version
python main.py --version  # (if implemented)

# Check settings load correctly
python -c "from config.settings import Settings; print(Settings().app_version)"
```

## Troubleshooting

### Version Not Updating
- Ensure `__init__.py` exists with correct format
- Check file permissions
- Verify you're in the correct directory

### Git Issues
- Ensure working directory is clean: `git status`
- Check you're on the correct branch
- Verify you have push permissions for tags

### Import Errors
- Ensure the project structure is correct
- Check that `__init__.py` contains valid Python syntax
- Verify all required files exist

## Integration with CI/CD

The version management system is designed to work with automated CI/CD pipelines:

- Version numbers are automatically read from `__init__.py`
- `pyproject.toml` supports dynamic versioning
- Git tags can trigger automated deployments
- Changelog format supports automated release notes

This system provides flexibility for both manual and automated release processes while maintaining consistency across all project files.
