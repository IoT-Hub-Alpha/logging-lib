# iot-logging-schemas

**Unified, framework-agnostic log schemas for Django, FastAPI, and Java microservices**

A Python library providing strict, Pydantic-based log schemas that eliminate null fields and enable clean, structured logging across IoT microservices.

## 📋 Features

- ✅ **No null fields** - Only relevant fields are serialized to JSON
- ✅ **Framework-agnostic** - Pure Python, works with Django, FastAPI, custom services
- ✅ **Type-safe schemas** - Pydantic v2 models with validation and IDE support
- ✅ **Context management** - Thread-safe contextvars for request/task tracing
- ✅ **Django integration** - Middleware + signal handlers for automatic context binding
- ✅ **Celery integration** - Signal handlers for task pre/post-run context
- ✅ **Flexible metadata** - Support for custom fields via `extra={}` dict
- ✅ **JSON formatter** - Excludes None values for clean log output

## 🚀 Quick Start

### Installation

```bash
pip install git+https://github.com/yourorg/iot-logging-schemas.git
```

### Django Setup

1. Add middleware to `settings.py`:

```python
MIDDLEWARE = [
    # ... other middleware ...
    'iot_logging.django_helpers.RequestContextMiddleware',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'iot_logging.ExcludingNullJsonFormatter',
            'fmt': '%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(method)s %(path)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

2. Use in views:

```python
import logging
from iot_logging import HttpRequestLog

logger = logging.getLogger(__name__)

logger.info(
    "User login successful",
    extra={
        "request_id": "abc-123",
        "method": "POST",
        "path": "/api/auth/login",
        "status_code": 200,
        "duration_ms": 45.5,
        "user_id": "user_456",
    }
)
```

### FastAPI Setup

```python
from fastapi import FastAPI
from iot_logging import ExcludingNullJsonFormatter
import logging

app = FastAPI()

@app.middleware("http")
async def log_requests(request, call_next):
    request_id = request.headers.get("x-request-id", "")
    response = await call_next(request)

    logger = logging.getLogger("request.lifecycle")
    logger.info(
        "HTTP request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": 45.5,
        }
    )
    return response
```

### Celery Setup

```python
from celery import Celery
from iot_logging import setup_celery_logging_context

app = Celery(__name__)
setup_celery_logging_context()

@app.task
def process_data(device_id):
    logger = logging.getLogger("celery.task")
    logger.info(
        "Processing device data",
        extra={
            "task_name": "process_data",
            "task_id": "task-123",
            "device_id": device_id,
            "status": "started",
        }
    )
    # ... process ...
```

## 📦 Log Schemas

### Base Schema

All schemas inherit from `BaseLogSchema`:

```python
from iot_logging import BaseLogSchema, LogLevel
from datetime import datetime

log = BaseLogSchema(
    timestamp=datetime.now(),
    level=LogLevel.INFO,
    logger="request.lifecycle",
    message="Request processed",
)
```

### HTTP Request Log

```python
from iot_logging import HttpRequestLog

log = HttpRequestLog(
    timestamp=datetime.now(),
    level=LogLevel.INFO,
    logger="request.lifecycle",
    message="GET /api/devices completed",
    request_id="req-123",
    method="GET",
    path="/api/devices",
    status_code=200,
    duration_ms=45.67,
    user_id="user_456",  # Optional
)
```

### Celery Task Log

```python
from iot_logging import CeleryTaskLog

log = CeleryTaskLog(
    timestamp=datetime.now(),
    level=LogLevel.INFO,
    logger="celery.task",
    message="Task completed",
    task_name="apps.tasks.process_data",
    task_id="celery-abc-123",
    status="success",
    duration_ms=1234.5,
    request_id="req-123",  # Optional, if triggered by request
)
```

### Kafka Consumer Log

```python
from iot_logging import KafkaConsumerLog

log = KafkaConsumerLog(
    timestamp=datetime.now(),
    level=LogLevel.INFO,
    logger="kafka.consumer",
    message="Message processed",
    topic="telemetry.raw",
    consumer_group="analytics-processor",
    partition=0,
    offset=12345,
    status="success",
    processing_duration_ms=25.5,
)
```

### Generic Service Log

```python
from iot_logging import GenericServiceLog

log = GenericServiceLog(
    timestamp=datetime.now(),
    level=LogLevel.INFO,
    logger="service.background",
    message="Batch processing completed",
    service_name="metrics_aggregator",
    component="exporter",
    operation="export_metrics",
    duration_ms=1234.56,
    item_count=150,
)
```

## 🔧 Context Management

### Automatic (Django Middleware)

The `RequestContextMiddleware` automatically binds request context:

```python
# In settings.py
MIDDLEWARE = [
    'iot_logging.django_helpers.RequestContextMiddleware',
]

# Automatically available in all logs
from iot_logging import context
request_id = context.request_id.get()  # Available in all logging calls
```

### Manual Binding

```python
from iot_logging import context

# Request context
context.set_request(
    request_id="req-123",
    method="GET",
    path="/api/users",
)

# Task context
context.set_task(
    task_id="celery-123",
    task_name="tasks.process_data",
)

# Service context
context.set_service("metrics_processor")

# Get all context
all_ctx = context.get_all()  # Returns dict with all values
non_null = context.get_all_non_null()  # Returns only non-None values

# Clear context
context.clear_request()
context.clear_task()
context.clear_service()
```

## 💡 Key Benefits

### 1. No Null Fields in JSON

**Before:**
```json
{
  "timestamp": "2026-01-27T13:30:00",
  "level": "INFO",
  "logger": "request.lifecycle",
  "message": "GET /api/devices completed",
  "request_id": "req-123",
  "method": "GET",
  "path": "/api/devices",
  "task_id": null,
  "task_name": null
}
```

**After:**
```json
{
  "timestamp": "2026-01-27T13:30:00",
  "level": "INFO",
  "logger": "request.lifecycle",
  "message": "GET /api/devices completed",
  "request_id": "req-123",
  "method": "GET",
  "path": "/api/devices"
}
```

### 2. Type Safety

```python
from iot_logging import HttpRequestLog

# IDE autocomplete works
log = HttpRequestLog(
    timestamp=datetime.now(),
    level="INFO",  # Type-checked
    logger="...",
    message="...",
    request_id="...",
    method="GET",
    path="/",
    status_code=200,  # Validated: must be 100-599
    duration_ms=45.5,  # Validated: must be >= 0
)
```

### 3. Framework Independence

Same schemas work across Django, FastAPI, Celery, Kafka:

```python
# Django
logger.info("Event", extra={"status_code": 200})

# FastAPI
logger.info("Event", extra={"status_code": 200})

# Celery
logger.info("Event", extra={"status_code": 200})

# All produce clean, consistent JSON
```

## 📚 Examples

See `/examples/` directory:

- `django_example.py` - Django views, middleware, and Celery tasks
- `fastapi_example.py` - FastAPI endpoints and background tasks
- `kafka_example.py` - Kafka consumer message processing

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/iot_logging

# Specific test file
pytest tests/test_schemas.py -v
```

## 📖 API Reference

### Schemas

- `BaseLogSchema` - Base for all log schemas
- `HttpRequestLog` - HTTP request/response logging
- `CeleryTaskLog` - Celery task execution logging
- `KafkaConsumerLog` - Kafka consumer processing logging
- `GenericServiceLog` - Background service/cron job logging

### Formatters

- `ExcludingNullJsonFormatter` - JSON formatter that excludes None values

### Context

- `LoggingContext` - Thread-safe context variables
- `context` - Global context instance
- `bind_request_context()` - Manually bind request
- `clear_request_context()` - Clear request context
- `bind_task_context()` - Manually bind task
- `clear_task_context()` - Clear task context
- `setup_celery_logging_context()` - Connect Celery signals

### Django Integration

- `RequestContextMiddleware` - Auto-bind request context

## 🔄 Migration from Custom Logging

If you have custom logging setup:

**Before:**
```python
# Custom context handling
context_vars = {}
def bind_request(...):
    context_vars['request_id'] = ...

# Custom formatting logic
def format_log(...):
    ...
```

**After:**
```python
# Use library context
from iot_logging import context
context.set_request(...)

# Use library formatter
from iot_logging import ExcludingNullJsonFormatter
```

## 🚀 Future Plans

- Java schemas (via JSON Schema export)
- Go schemas
- OpenTelemetry integration
- Structured field validation profiles
- Log sampling strategies

## 📜 License

See LICENSE file.

## 👥 Contributing

Pull requests welcome! Please run tests before submitting:

```bash
pytest
black src/ tests/
flake8 src/ tests/
```

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing examples in `/examples/`
- Review test cases in `/tests/`