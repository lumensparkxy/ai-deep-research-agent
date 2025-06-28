# Unit Tests for Deep Research Agent

This directory contains comprehensive unit tests for the Deep Research Agent project.

## 🎯 Test Coverage

### Current Tests
- **`test_session_manager.py`** - Complete test suite for SessionManager functionality
  - Session creation and validation
  - File persistence operations  
  - Session metadata management
  - Error handling and edge cases

### Test Structure
```
tests/
├── __init__.py              # Tests package
├── conftest.py              # Shared pytest fixtures
├── test_session_manager.py  # SessionManager tests
├── fixtures/                # Test data
│   └── sample_sessions.json # Sample session data
└── README.md               # This file
```

## 🚀 Running Tests

### Quick Start
```bash
# Run all tests
.venv/bin/python -m pytest tests/ -v

# Run specific test file
.venv/bin/python -m pytest tests/test_session_manager.py -v

# Run with coverage
.venv/bin/python -m pytest tests/ --cov=. --cov-report=html
```

### Using the Test Runner Script
```bash
# Run all tests
.venv/bin/python run_tests.py --all --verbose

# Run SessionManager tests only
.venv/bin/python run_tests.py --session --verbose

# Run with coverage report
.venv/bin/python run_tests.py --all --coverage
```

## 📊 Test Results Summary

### SessionManager Tests (18 tests)
✅ **All 18 tests passing**

**Test Categories:**
- **Initialization (2 tests)** - Constructor and settings handling
- **Session ID Generation (1 test)** - Format validation 
- **Session Creation (3 tests)** - Success cases and validation
- **Session Persistence (3 tests)** - Save/load operations
- **Session Updates (2 tests)** - Stage and conclusion updates  
- **Session Listing (3 tests)** - Directory scanning and metadata
- **Error Handling (4 tests)** - Invalid inputs and file errors

**Coverage:** 69% of SessionManager code is covered by tests

## 🧪 Test Features

### Mock Objects and Fixtures
- **Settings mocking** - Isolated test environment
- **Temporary directories** - Clean test isolation
- **Sample data** - Realistic test scenarios
- **DateTime mocking** - Consistent timestamps

### Validation Testing
- **Input sanitization** - Security-focused validation
- **Error conditions** - Comprehensive error handling
- **Edge cases** - Boundary condition testing
- **File operations** - I/O error simulation

### Test Quality
- **Descriptive names** - Self-documenting test cases
- **Isolated tests** - No interdependencies  
- **Fast execution** - Sub-second test runs
- **Clear assertions** - Readable test logic

## 🛠 Writing New Tests

### Test Naming Convention
```python
def test_[component]_[action]_[expected_result](self):
    """Test [description of what is being tested]."""
```

### Using Fixtures
```python
def test_example(self, mock_settings, temp_dir, sample_session_data):
    """Example test using fixtures."""
    session_manager = SessionManager(mock_settings)
    # ... test implementation
```

### Adding Test Data
Add new sample data to `tests/fixtures/` and create fixtures in `conftest.py`.

## 📈 Future Test Plans

### Planned Test Suites
1. **`test_validators.py`** - Input validation and sanitization
2. **`test_conversation.py`** - User interaction and flow control
3. **`test_research_engine.py`** - Core research functionality (with API mocks)
4. **`test_report_generator.py`** - Report generation and formatting
5. **`test_integration.py`** - End-to-end workflow testing

### Testing Strategy
- **Unit tests** - Individual component testing
- **Integration tests** - Component interaction testing  
- **Mock external APIs** - Isolated testing without real API calls
- **Performance tests** - Scalability and response time validation

## 🔧 Dependencies

### Required Packages
- `pytest>=8.4.1` - Test framework
- `pytest-cov>=6.2.1` - Coverage reporting
- Standard library: `unittest.mock`, `tempfile`, `pathlib`

### Configuration
Tests are configured via `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*" 
python_functions = "test_*"
addopts = "--verbose --cov=. --cov-report=term-missing"
```

## 🎉 Success Metrics

### Current Status
- ✅ **18/18 tests passing** (100% success rate)
- ✅ **69% SessionManager coverage** 
- ✅ **Sub-second execution time**
- ✅ **Zero test dependencies**
- ✅ **Comprehensive error testing**

The testing foundation is now solid and ready for expansion as the project grows!
