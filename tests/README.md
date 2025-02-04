# PyFed Tests

This directory contains the test suite for the PyFed library. The tests are written using pytest and are organized into different categories.

## Directory Structure

```
tests/
├── unit_tests/           # Unit tests for individual components
│   ├── models/          # Tests for ActivityPub models
│   ├── serializers/     # Tests for serialization/deserialization
└── pytest.ini           # Pytest configuration
```

## Running Tests

### Prerequisites

- Python 3.9+
- pytest
- pytest-asyncio
- pytest-cov

### Installation

```bash
pip install .  # Install packages
```

### Running All Tests

From the project root directory:

```bash
pytest
```

### Running Specific Test Categories

```bash
pytest tests/unit_tests/models/         # Run model tests only
pytest tests/unit_tests/serializers/    # Run serializer tests only
pytest tests/integration_tests/         # Run integration tests only
```

### Running with Coverage

```bash
pytest --cov=pyfed tests/
```

### Test Configuration

The test suite uses the following configuration from `pytest.ini`:

- `asyncio_mode = auto`: Enables automatic async test detection
- `pythonpath = ../src`: Adds source directory to Python path
- `addopts = --import-mode=importlib`: Uses importlib for imports

## Writing Tests

### Test Organization

- Place unit tests in the appropriate subdirectory under `unit_tests/`
- Use descriptive test names that indicate what is being tested
- Follow the pattern: `test_<what>_<expected_behavior>`

### Example Test

```python
def test_serialize_note():
    """Test serialization of a basic Note object."""
    note = APNote(
        id="https://example.com/notes/123",
        content="Hello, World!"
    )
    serialized = note.serialize()
    assert serialized["type"] == "Note"
    assert serialized["content"] == "Hello, World!"
```

## Debugging Tests

- Use `pytest -v` for verbose output
- Use `pytest -s` to see print statements
- Use `pytest --pdb` to drop into debugger on failures

## Adding New Tests

1. Create test files in the appropriate directory
2. Follow existing naming conventions
3. Add necessary imports and fixtures
4. Document test purpose with docstrings