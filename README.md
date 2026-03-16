# iot-logging-schemas

[![CI](https://github.com/IoT-Hub-Alpha/logging-lib/actions/workflows/ci.yaml/badge.svg?branch=dev)](https://github.com/IoT-Hub-Alpha/logging-lib/actions/workflows/ci.yaml)

**Unified, framework-agnostic log schemas for Django, FastAPI, and Java microservices**

A Python library providing strict, Pydantic-based log schemas that eliminate null fields and enable clean, structured logging across IoT microservices.

## 📋 Features

- ✅ **Automatic context injection** - `request_id`, `request_method`, `request_path`, `task_id`, `task_name` auto-injected into every log
- ✅ **No null fields** - Only relevant fields are serialized to JSON
- ✅ **Framework-agnostic** - Pure Python, works with Django, FastAPI, Celery
- ✅ **Context management** - Thread-safe contextvars for request/task tracing
- ✅ **Django integration** - Middleware + signal handlers for automatic context binding
- ✅ **Celery integration** - Signal handlers for task pre/post-run context binding
- ✅ **Flexible metadata** - Support for custom fields via `extra={}` dict
- ✅ **JSON formatter** - Excludes None values for clean log output

## 🚀 Quick Start

### Installation

```bash
pip install git+https://github.com/IoT-Hub-Alpha/logging-lib.git@dev
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
            '()': 'iot_logging.StructuredJsonFormatter',
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

2. Use in views (context is auto-injected by formatter):

```python
import logging

logger = logging.getLogger(__name__)

logger.info(
    "User login successful",
    extra={
        "status_code": 200,
        "duration_ms": 45.5,
        "user_id": "user_456",
    }
)
# request_id, method, path are automatically injected by StructuredJsonFormatter
```

### FastAPI Setup

```python
from fastapi import FastAPI
from iot_logging import FastAPIRequestContextMiddleware, StructuredJsonFormatter
import logging

app = FastAPI()

# Configure logging with JSON formatter
logging.basicConfig(level=logging.INFO)
for handler in logging.root.handlers:
    handler.setFormatter(StructuredJsonFormatter())

# Add request context middleware (auto-injects request_id, method, path, status_code, duration_ms)
app.add_middleware(FastAPIRequestContextMiddleware)
```

The middleware automatically:
- Extracts or generates request ID from `x-request-id` header
- Binds request context (request_id, method, path)
- Logs request completion with status_code and duration_ms
- Sets `x-request-id` response header
- Injects context into all logs via StructuredJsonFormatter
- Handles exceptions with proper cleanup

### Celery Setup

```python
from celery import Celery
from iot_logging import StructuredJsonFormatter, setup_celery_logging_context
import logging

app = Celery(__name__, include=['myapp.tasks'])

# Configure logging
logging.basicConfig(level=logging.INFO)
for handler in logging.root.handlers:
    handler.setFormatter(StructuredJsonFormatter())

# Setup Celery context binding (task_id and task_name auto-injected)
setup_celery_logging_context()

@app.task
def process_data(device_id):
    logger = logging.getLogger("celery.task")
    logger.info(
        "Processing device data",
        extra={
            "device_id": device_id,
            "status": "started",
        }
    )
    # task_id and task_name are automatically injected by StructuredJsonFormatter
```

### Kafka Consumer Setup

```python
from confluent_kafka import Consumer
from iot_logging import StructuredJsonFormatter
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
for handler in logging.root.handlers:
    handler.setFormatter(StructuredJsonFormatter())

logger = logging.getLogger("kafka.consumer")

# Create consumer
consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'telemetry-processor',
    'auto.offset.reset': 'earliest'
})

consumer.subscribe(['telemetry.raw'])

for msg in consumer:
    start_time = time.time()

    try:
        # Process message
        data = json.loads(msg.value().decode('utf-8'))
        process_telemetry(data)
        status = "success"
        error_msg = None
    except Exception as e:
        status = "error"
        error_msg = str(e)

    # Log consumption (topic, consumer_group, partition, offset auto-validated)
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "Message processed",
        extra={
            "topic": msg.topic(),
            "consumer_group": "telemetry-processor",
            "partition": msg.partition(),
            "offset": msg.offset(),
            "status": status,
            "processing_duration_ms": round(duration_ms, 2),
            "error_message": error_msg,
        }
    )
```

### Kafka Producer Setup

```python
from confluent_kafka import Producer
from iot_logging import StructuredJsonFormatter
import logging
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
for handler in logging.root.handlers:
    handler.setFormatter(StructuredJsonFormatter())

logger = logging.getLogger("kafka.producer")

producer = Producer({
    'bootstrap.servers': 'localhost:9092',
})

def on_delivery(err, msg):
    if err:
        logger.error(
            "Message delivery failed",
            extra={
                "topic": msg.topic(),
                "error_type": str(type(err).__name__),
                "error_message": str(err),
                "status": "error",
            }
        )
    else:
        logger.info(
            "Message delivered",
            extra={
                "topic": msg.topic(),
                "partition": msg.partition(),
                "offset": msg.offset(),
                "status": "success",
            }
        )

# Send message
data = {"device_id": "dev-123", "temperature": 25.5}
producer.produce(
    'telemetry.raw',
    key=b"dev-123",
    value=json.dumps(data).encode('utf-8'),
    callback=on_delivery
)
producer.flush()
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

### Kafka Producer Log

```python
from iot_logging import KafkaProducerLog

log = KafkaProducerLog(
    timestamp=datetime.now(),
    level=LogLevel.INFO,
    logger="kafka.producer",
    message="Message sent",
    topic="telemetry.raw",
    partition=0,
    message_key="device_123",
    status="success",
    duration_ms=15.5,
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

The `RequestContextMiddleware` automatically binds request context and injects it into all logs:

```python
# In settings.py
MIDDLEWARE = [
    'iot_logging.django_helpers.RequestContextMiddleware',
]

# In views - context fields are auto-injected by StructuredJsonFormatter
logger.info("Event", extra={"user_id": 123})
# Output includes: request_id, request_method, request_path (auto-injected)
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

See [examples/](/examples/) directory for complete working examples:

- [django_example.py](examples/django_example.py) - Django views, middleware, and Celery tasks
- [fastapi_example.py](examples/fastapi_example.py) - FastAPI endpoints and background tasks
- [kafka_example.py](examples/kafka_example.py) - Kafka consumer message processing

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

### Formatters

- `StructuredJsonFormatter` - JSON formatter that auto-injects context and excludes None values

### Context Management

- `LoggingContext` - Thread-safe context variables with contextvars
- `context` - Global context instance
- `context.set_request(request_id, method, path)` - Set request context
- `context.clear_request()` - Clear request context
- `context.set_task(task_id, task_name)` - Set task context
- `context.clear_task()` - Clear task context
- `context.get_all()` - Get all context (including None)
- `context.get_all_non_null()` - Get non-None context only

### Django Integration

- `RequestContextMiddleware` - Auto-bind request context, auto-clear after response
- `bind_request_context(request, request_id)` - Manually bind request context
- `clear_request_context()` - Manually clear request context

### FastAPI Integration

- `FastAPIRequestContextMiddleware` - Auto-bind request context, auto-clear after response
- `bind_request_context(request, request_id)` - Manually bind request context
- `clear_request_context()` - Manually clear request context

### Kafka Integration

Kafka consumer and producer logging are handled via structured log schemas:
- `KafkaConsumerLog` - Log message consumption and processing (topic, partition, offset, status)
- `KafkaProducerLog` - Log message production and delivery (topic, partition, status)

Usage: Log via `extra={}` dict with message details. The StructuredJsonFormatter automatically validates fields against the schema.

```python
logger.info("Message processed", extra={
    "topic": msg.topic(),
    "partition": msg.partition(),
    "offset": msg.offset(),
    "status": "success",
    "processing_duration_ms": 25.5,
})
```

### Celery Integration

- `setup_celery_logging_context()` - Connect task_prerun/task_postrun signals
- `bind_task_context(task_id, task_name)` - Manually bind task context
- `clear_task_context()` - Manually clear task context
- `get_task_context()` - Get current task context

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
from iot_logging import StructuredJsonFormatter
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