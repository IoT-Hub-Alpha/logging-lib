# Contributing to iot-logging-schemas

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the library.

## Development Setup

### Prerequisites

- Python 3.13+
- pip
- pytest

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourorg/iot-logging-schemas.git
cd iot-logging-schemas
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Install the library in editable mode:
```bash
pip install -e .
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/iot_logging --cov-report=html

# Run specific test file
pytest tests/test_schemas.py -v

# Run specific test
pytest tests/test_schemas.py::TestBaseLogSchema::test_base_log_schema_creation -v
```

## Code Style

We use Black for code formatting and Flake8 for linting.

```bash
# Format code
black src/ tests/

# Check linting
flake8 src/ tests/

# Run mypy type checking
mypy src/
```

## Architecture

The library is organized into these modules:

### `/src/iot_logging/schemas/`
Pydantic models for different log types:
- `base.py` - BaseLogSchema with common fields
- `http_request.py` - HttpRequestLog for HTTP requests
- `celery_task.py` - CeleryTaskLog for Celery tasks
- `kafka_consumer.py` - KafkaConsumerLog for Kafka messages
- `generic_service.py` - GenericServiceLog for background services

### `/src/iot_logging/formatters/`
Log formatters for output:
- `json_formatter.py` - StructuredJsonFormatter

### `/src/iot_logging/`
Core modules:
- `context.py` - LoggingContext for thread-safe context management
- `django_helpers.py` - Django integration
- `celery_helpers.py` - Celery integration

### `/tests/`
Test suites:
- `test_schemas.py` - Schema validation and serialization
- `test_formatter.py` - JSON formatter tests
- `test_context.py` - Context management tests
- `test_django_helpers.py` - Django integration tests
- `test_celery_helpers.py` - Celery integration tests

## Adding New Features

### Adding a New Log Schema

1. Create a new schema in `/src/iot_logging/schemas/`:

```python
# src/iot_logging/schemas/custom_service.py
from pydantic import ConfigDict, Field
from iot_logging.schemas.base import BaseLogSchema

class CustomServiceLog(BaseLogSchema):
    """Custom service logging."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2026-01-27T13:30:00",
                "level": "INFO",
                "logger": "service.custom",
                "message": "Operation completed",
                "service_name": "my_service",
                "status": "success",
            }
        }
    )

    service_name: str = Field(description="Service name")
    status: str = Field(description="Operation status")
```

2. Add tests in `/tests/test_schemas.py`:

```python
def test_custom_service_log_required_fields():
    """Test CustomServiceLog with required fields."""
    log = CustomServiceLog(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        logger="service.custom",
        message="Operation completed",
        service_name="my_service",
        status="success",
    )
    assert log.service_name == "my_service"
```

3. Export from `__init__.py`:

```python
# src/iot_logging/__init__.py
from iot_logging.schemas.custom_service import CustomServiceLog

__all__ = [
    # ... existing exports ...
    "CustomServiceLog",
]
```

### Adding a New Integration

1. Create integration module (e.g., `fastapi_helpers.py`)
2. Add helper functions for setup and context management
3. Add tests in `/tests/test_fastapi_helpers.py`
4. Create example in `/examples/fastapi_example.py`
5. Update README with usage instructions

## Testing Guidelines

### Schema Tests

- Test required fields
- Test optional fields
- Test field constraints (min/max values)
- Test serialization and deserialization
- Test enum values

### Integration Tests

- Test context binding
- Test context clearing
- Test context isolation between requests/tasks
- Test middleware behavior

### Example Tests

- Ensure examples are runnable
- Test example scenarios
- Include comments explaining the example

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def bind_request_context(
    request,
    request_id: Optional[str] = None,
) -> str:
    """
    Bind HTTP request to logging context.

    Extracts request details and stores them in the global logging context.
    Returns the request_id for use in response headers.

    Args:
        request: Django HTTP request object
        request_id: Optional request ID; generates UUID if not provided

    Returns:
        str: The request ID being used
    """
```

### README Updates

- Add examples of new features
- Update API reference section
- Include migration path if replacing old functionality

## Commit Messages

Follow conventional commit format:

```
feat: add new schema for gRPC logging
fix: exclude None values from JSON formatter
docs: add FastAPI integration example
test: add tests for KafkaConsumerLog
chore: update dependencies
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make changes and add tests
4. Run tests: `pytest`
5. Format code: `black src/ tests/`
6. Check linting: `flake8 src/ tests/`
7. Commit with conventional messages
8. Push to your fork
9. Create a pull request with:
   - Clear description of changes
   - Link to related issues
   - Justification for changes

## Versioning

We follow Semantic Versioning (SemVer):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

Update version in `pyproject.toml` before releasing.

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions should automatically publish to PyPI

## Common Issues

### Import Errors

Ensure the library is installed in editable mode:
```bash
pip install -e .
```

### Test Failures

1. Check Python version: `python --version` (should be 3.13+)
2. Reinstall dependencies: `pip install -r requirements-dev.txt`
3. Run tests with verbose output: `pytest -v`

### Formatting Issues

Run Black to auto-format:
```bash
black src/ tests/
```

## Questions?

- Check existing GitHub issues
- Review examples in `/examples/`
- Look at tests for usage patterns
- Open a discussion if unclear

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

Thank you for contributing!