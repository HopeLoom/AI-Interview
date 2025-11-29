# Tests Documentation

This directory contains comprehensive tests for the interview simulation backend, including unit tests, integration tests, and testing utilities.

## Directory Structure

```
tests/
├── __init__.py                    # Test package initialization
├── conftest.py                    # Pytest configuration and shared fixtures
├── pytest.ini                    # Pytest configuration file
├── README.md                      # This file
├── examples/                      # Example scripts and usage demonstrations
│   └── database_examples.py       # Database abstraction usage examples
├── integration/                   # Integration tests
│   ├── __init__.py
│   ├── test_database_operations.py # Cross-database operation tests
│   └── test_migrations.py         # Database migration tests
├── unit/                          # Unit tests
│   ├── __init__.py
│   ├── test_database_base.py      # Database interface and base class tests
│   └── test_config_manager.py     # Configuration management tests
└── utils/                         # Test utilities and helpers
    ├── __init__.py
    └── test_helpers.py            # Test helper functions and fixtures
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Scope**: Database interfaces, configuration models, utility functions
- **Dependencies**: Minimal external dependencies, uses mocks where needed
- **Speed**: Fast execution (< 1 second per test)

### Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions and real database operations
- **Scope**: Database operations, migrations, configuration loading
- **Dependencies**: May require external services (PostgreSQL, Firebase)
- **Speed**: Slower execution (1-10 seconds per test)

### Example Scripts (`tests/examples/`)
- **Purpose**: Demonstrate usage patterns and provide working examples
- **Scope**: Complete workflows, configuration examples, migration examples
- **Usage**: Can be run independently to test functionality

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov pytest-timeout
```

### Basic Test Execution

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=core --cov-report=html
```

Run specific test categories:
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Exclude slow tests
pytest -m "not slow"

# Exclude tests requiring external services
pytest -m "not postgresql and not firebase"
```

### Test Markers

Tests are marked with the following markers:

- `unit`: Unit tests (fast, isolated)
- `integration`: Integration tests (slower, may need external services)
- `slow`: Tests that take longer to execute
- `postgresql`: Tests requiring PostgreSQL database
- `firebase`: Tests requiring Firebase credentials
- `database`: Tests related to database functionality
- `config`: Tests related to configuration management

### Environment-Specific Testing

#### SQLite (Default)
No additional setup required. Uses in-memory databases for testing.

#### PostgreSQL Testing
Set up PostgreSQL and configure environment variables:
```bash
export TEST_POSTGRES_AVAILABLE=true
export TEST_POSTGRES_HOST=localhost
export TEST_POSTGRES_PORT=5432
export TEST_POSTGRES_DB=interview_sim_test
export TEST_POSTGRES_USER=test_user
export TEST_POSTGRES_PASSWORD=test_password
```

#### Firebase Testing
Place Firebase credentials file in the backend directory:
```bash
# Ensure interview-simulation-firebase.json exists
ls interview-simulation-firebase.json
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Test discovery patterns
- Coverage reporting
- Timeout settings
- Async test support
- Warning filters

### Shared Fixtures (`conftest.py`)
- Database configurations for different backends
- Sample data fixtures (users, sessions, configs)
- Temporary file and directory fixtures
- Mock objects and test utilities

## Test Utilities

### DatabaseTestHelper
Provides utilities for database testing:
- `create_test_user()`: Generate test user profiles
- `create_test_session()`: Generate test session data
- `create_test_simulation_config()`: Generate test configurations
- `populate_test_data()`: Fill database with test data
- `cleanup_test_data()`: Clean up test data

### ConfigTestHelper
Provides utilities for configuration testing:
- `create_test_config_data()`: Generate test configuration data
- `create_temp_config_file()`: Create temporary config files

### MockDatabaseFactory
Creates mock database instances for unit testing without real database dependencies.

### TestDataGenerator
Generates realistic test data:
- Interview transcripts
- Evaluation data
- User profiles with various scenarios

## Writing New Tests

### Unit Test Example
```python
import pytest
from core.database.base import UserProfile

class TestUserProfile:
    def test_user_creation(self):
        user = UserProfile(
            user_id="test_123",
            name="Test User",
            email="test@example.com",
            company_name="Test Company",
            location="Test City"
        )
        assert user.user_id == "test_123"
        assert user.role == "candidate"  # Default value
```

### Integration Test Example
```python
import pytest

@pytest.mark.integration
class TestDatabaseIntegration:
    @pytest.mark.asyncio
    async def test_user_workflow(self, sqlite_db, sample_user_profile):
        # Create user
        success = await sqlite_db.create_user(sample_user_profile)
        assert success
        
        # Verify user exists
        user_id = await sqlite_db.get_user_id_by_email(sample_user_profile.email)
        assert user_id == sample_user_profile.user_id
```

### Test Fixtures
```python
@pytest.fixture
def custom_test_data():
    return {
        "key": "value",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@pytest.mark.asyncio
async def test_with_custom_fixture(sqlite_db, custom_test_data):
    # Use the fixture in your test
    pass
```

## Continuous Integration

### GitHub Actions
Tests can be integrated into CI/CD pipelines:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=core --cov-report=xml
```

### Test Matrix
Run tests against multiple Python versions and database backends:
```yaml
strategy:
  matrix:
    python-version: [3.8, 3.9, 3.10, 3.11]
    database: [sqlite, postgresql]
```

## Performance Testing

### Database Performance
```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_bulk_operations(sqlite_db):
    # Test performance with large datasets
    users = [create_test_user() for _ in range(1000)]
    
    start_time = time.time()
    for user in users:
        await sqlite_db.create_user(user)
    duration = time.time() - start_time
    
    assert duration < 10  # Should complete within 10 seconds
```

### Memory Usage
```python
import psutil
import os

def test_memory_usage():
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Perform memory-intensive operations
    # ...
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
```

## Debugging Tests

### Verbose Output
```bash
pytest -v -s  # Verbose with print statements
```

### Debug Specific Test
```bash
pytest tests/unit/test_database_base.py::TestUserProfile::test_user_creation -v
```

### PDB Debugging
```bash
pytest --pdb  # Drop into debugger on failure
```

### Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

def test_with_logging():
    logging.debug("Debug information")
    # Test code
```

## Best Practices

### Test Naming
- Use descriptive test names: `test_user_creation_with_valid_data`
- Group related tests in classes: `TestUserProfile`, `TestDatabaseOperations`
- Use consistent naming patterns

### Test Structure
- **Arrange**: Set up test data and conditions
- **Act**: Execute the functionality being tested
- **Assert**: Verify the results

### Test Data
- Use fixtures for reusable test data
- Keep test data minimal but realistic
- Clean up test data after tests complete

### Async Testing
- Use `@pytest.mark.asyncio` for async tests
- Properly await async operations
- Handle async context managers correctly

### Mocking
- Mock external dependencies in unit tests
- Use real services in integration tests when possible
- Keep mocks simple and focused

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure test databases are properly configured
   - Check environment variables
   - Verify database servers are running

2. **Async Test Failures**
   - Ensure proper use of `await` keywords
   - Check event loop configuration
   - Use `pytest-asyncio` plugin

3. **Import Errors**
   - Check Python path configuration
   - Ensure all dependencies are installed
   - Verify module structure

4. **Fixture Scope Issues**
   - Understand fixture scopes (function, class, module, session)
   - Use appropriate scope for your needs
   - Be aware of fixture cleanup

### Getting Help

- Check pytest documentation: https://docs.pytest.org/
- Review test logs for detailed error information
- Use `pytest --tb=long` for detailed tracebacks
- Consider using `pytest --lf` to run only failed tests
