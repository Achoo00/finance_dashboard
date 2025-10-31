# Test Suite Documentation

## Overview
This directory contains the comprehensive test suite for the Finance Dashboard application.

## Structure
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── README.md               # This file
├── unit/                   # Unit tests for individual components
│   ├── test_database.py   # Database layer tests ✅ (First test implemented)
│   ├── test_data_collector.py  # Data collection tests (TODO)
│   ├── test_analysis.py   # Analysis tests (TODO)
│   └── test_yaml_exporter.py  # YAML export tests (TODO)
├── integration/            # Integration tests
│   ├── test_data_pipeline.py  # End-to-end data flow (TODO)
│   └── test_api_integration.py  # API integration tests (TODO)
└── functional/            # Functional tests
    └── test_portfolio_management.py  # Portfolio CRUD workflows (TODO)
```

## Running Tests

### Prerequisites
Install test dependencies:
```bash
pip install -r requirements-test.txt
```

### Run All Tests
```bash
pytest
```

### Run Specific Test Suite
```bash
# Database tests
pytest tests/unit/test_database.py

# All unit tests
pytest tests/unit/

# With coverage report
pytest --cov=. --cov-report=html
```

### Run Specific Test
```bash
pytest tests/unit/test_database.py::TestPortfolioManagement::test_create_portfolio_valid -v
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Output
```bash
pytest -s
```

## Test Implementation Status

### ✅ Completed
- **Test 1.1.1**: Create portfolio with valid data
- Test infrastructure setup (pytest, fixtures, conftest.py)

### 🚧 In Progress
- Database layer tests (Test Suite 1) - Partially implemented

### 📋 TODO
- Complete remaining database tests
- Data collector tests
- Analysis tests
- YAML exporter tests
- Integration tests
- Functional tests

## Test Coverage Goals
- **Unit Tests**: 80%+ code coverage
- **Integration Tests**: Critical paths 100%
- **Functional Tests**: All user workflows covered

## Fixtures

### test_db
Provides an in-memory SQLite database for each test. Automatically cleaned up after each test.

### sample_portfolio_data
Sample portfolio data dictionary with default values.

### sample_position_data
Sample position data dictionary with default values.

### sample_market_data
Sample market data dictionary including JSON-serialized quarterly data.

### portfolio_with_positions
Creates a complete test scenario with a portfolio and one position.

## Writing New Tests

1. **Follow the naming convention**: `test_<feature>_<scenario>`
2. **Use descriptive docstrings**: Include test ID from TEST_PLAN.md
3. **Use fixtures**: Leverage existing fixtures from `conftest.py`
4. **Keep tests independent**: Each test should be able to run in isolation
5. **Mock external dependencies**: Use `pytest-mock` for API calls, etc.
6. **Clean up**: Tests automatically clean up via fixtures, but ensure no side effects

### Example Test
```python
def test_create_portfolio_valid(self, test_db, sample_portfolio_data):
    """
    Test 1.1.1: Create portfolio with valid data
    
    Expected: Portfolio is created successfully with all attributes set correctly
    """
    portfolio = test_db.create_portfolio(**sample_portfolio_data)
    
    assert portfolio is not None
    assert portfolio.id is not None
    assert portfolio.name == sample_portfolio_data['name']
```

## Troubleshooting

### Import Errors
If you see import errors, ensure the parent directory is in your Python path. The `conftest.py` handles this automatically.

### Database Locked Errors
The in-memory database should prevent this, but if you see it, ensure all tests properly close database connections via fixtures.

### Test Failures
- Check that fixtures are properly set up
- Verify test data matches expected schema
- Ensure no test pollution (tests should be independent)

## Continuous Integration

Tests should be run:
- Before committing code
- In CI/CD pipeline
- Before releases
- After refactoring

