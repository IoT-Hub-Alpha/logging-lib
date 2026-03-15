# IoT Logging Schemas - Library Structure

## Overview

**iot-logging-schemas** is a unified, framework-agnostic log schema library for IoT microservices. It provides:

- **5 Pydantic v2 log schemas** with type-safe field definitions
- **Structured JSON formatter** that automatically injects context and excludes null values
- **Thread-safe context management** using Python contextvars
- **Framework integrations** for Django, FastAPI, and Celery
- **Kafka consumer logging** support
- **95% test coverage** with comprehensive test suite

The library ensures all services (Django, FastAPI, Kafka consumers) produce **consistent, queryable structured logs** without manual configuration.

---

## Directory Structure

```
logging-lib/
├── src/iot_logging/                    # Main library source
│   ├── __init__.py                     # Public API exports
│   ├── context.py                      # Thread-safe context management
│   ├── django_helpers.py               # Django middleware & helpers
│   ├── celery_helpers.py               # Celery signal handlers & helpers
│   ├── formatters/
│   │   ├── __init__.py
│   │   └── json_formatter.py           # JSON formatter with context injection
│   └── schemas/
│       ├── __init__.py
│       ├── base.py                     # BaseLogSchema, LogLevel enum
│       ├── http_request.py             # HttpRequestLog schema
│       ├── celery_task.py              # CeleryTaskLog schema
│       ├── kafka_consumer.py           # KafkaConsumerLog schema
│       └── generic_service.py          # GenericServiceLog schema
├── tests/                              # Test suite (95% coverage)
│   ├── test_schemas.py                 # Schema validation tests
│   ├── test_formatter.py               # Formatter tests
│   ├── test_context.py                 # Context isolation tests
│   ├── test_django_helpers.py          # Django integration tests
│   └── test_celery_helpers.py          # Celery integration tests
├── examples/                           # Usage examples
│   ├── django_example.py               # Django setup & usage
│   ├── fastapi_example.py              # FastAPI setup & usage
│   └── kafka_example.py                # Kafka consumer setup
├── pyproject.toml                      # Project metadata, dependencies
├── README.md                           # User documentation
├── CONTRIBUTING.md                     # Development guidelines
└── Library-structure.md                # This file
```

---

## Architecture & Workflow

### Core Flow

```
User Code
    ↓
Logger.info("message", extra={...})
    ↓
StructuredJsonFormatter
    ├─ Injects context variables (from contextvars)
    ├─ Removes None values
    └─ Outputs clean JSON
    ↓
JSON Log Output
```

### Context Flow (Request Lifecycle)

```
HTTP Request arrives
    ↓
RequestContextMiddleware.__call__()
    ├─ Extract/generate request_id
    ├─ Bind to LoggingContext (contextvars)
    ├─ Process request
    ├─ Log response with context
    └─ Clear context
    ↓
Response sent with X-Request-ID header
```

### Context Flow (Celery Task)

```
Celery Task queued
    ↓
task_prerun signal fires
    ├─ Bind task context to LoggingContext
    ↓
Task executes (all logs auto-inject task context)
    ↓
task_postrun signal fires
    ├─ Clear task context
```

### Why This Architecture?

- **contextvars**: Provides thread-safe, async-safe context isolation
- **Automatic injection**: Formatter injects context into every log automatically
- **No manual extra={}**: Context is always available, reducing boilerplate
- **Clean JSON**: Null values are removed, keeping log output lean
- **Framework agnostic**: Works with Django, FastAPI, FastAPI async, threaded Celery, etc.

---

## Core Modules

### 1. `src/iot_logging/__init__.py`

**Purpose**: Public API entry point. Exports all schemas, formatters, context, and helpers.

**Exports**:
- Schemas: `BaseLogSchema`, `LogLevel`, `HttpRequestLog`, `CeleryTaskLog`, `KafkaConsumerLog`, `GenericServiceLog`
- Formatter: `StructuredJsonFormatter`
- Context: `LoggingContext`, `context` (global instance)
- Django helpers: `RequestContextMiddleware`, `bind_request_context`, `clear_request_context`
- Celery helpers: `setup_celery_logging_context`, `bind_task_context`, `clear_task_context`, `get_task_context`

```python
from iot_logging import HttpRequestLog, context, RequestContextMiddleware
```

---

### 2. `src/iot_logging/context.py`

**Purpose**: Thread-safe context management using contextvars for request/task/service tracking.

#### Class: `LoggingContext`

Stores context variables in contextvars for thread-safe, async-safe isolation.

**Attributes**:
- `request_id` (ContextVar[Optional[str]]): Unique HTTP request identifier
- `request_method` (ContextVar[Optional[str]]): HTTP method (GET, POST, etc.)
- `request_path` (ContextVar[Optional[str]]): Request endpoint path
- `task_id` (ContextVar[Optional[str]]): Celery task UUID
- `task_name` (ContextVar[Optional[str]]): Full task function name
- `service_name` (ContextVar[Optional[str]]): Background service/component name

**Methods**:

##### `__init__(self) -> None`
Initializes all context variables with default=None.

##### `set_request(self, request_id: str, method: str, path: str) -> None`
Sets request context (request_id, method, path). Called by Django middleware or manually.

**Args**:
- `request_id`: Unique request identifier
- `method`: HTTP method
- `path`: Request endpoint

##### `clear_request(self) -> None`
Clears all request context variables (sets to None). Called after request completes.

##### `set_task(self, task_id: str, task_name: str) -> None`
Sets Celery task context (task_id, task_name). Called by Celery signal or manually.

**Args**:
- `task_id`: Celery task UUID
- `task_name`: Full task function name (e.g., "apps.tasks.process_data")

##### `clear_task(self) -> None`
Clears all task context variables (sets to None). Called after task completes.

##### `set_service(self, service_name: str) -> None`
Sets background service context (service_name). For batch jobs, cron tasks, etc.

**Args**:
- `service_name`: Name of the service/component

##### `clear_service(self) -> None`
Clears service context variable (sets to None).

##### `get_all(self) -> Dict[str, Optional[str]]`
Returns all context variables (including None values).

**Returns**: Dictionary with keys: request_id, request_method, request_path, task_id, task_name, service_name

##### `get_all_non_null(self) -> Dict[str, str]`
Returns only non-None context variables.

**Returns**: Filtered dictionary (no None values)

**Global Instance**:
```python
context = LoggingContext()
```
Use this singleton for all context operations.

---

### 3. `src/iot_logging/formatters/json_formatter.py`

**Purpose**: Structured JSON formatter that injects context and removes None values.

#### Class: `StructuredJsonFormatter(JsonFormatter)`

Extends pythonjsonlogger.JsonFormatter to automatically inject context variables and exclude null values.

**How it works**:
1. Parent class converts log record to JSON
2. Injects non-null context variables (if not already in extra={})
3. Removes all None values from output
4. Returns clean, queryable JSON

**Methods**:

##### `add_fields(self, log_record: dict, record: LogRecord, message_dict: dict) -> None`
Called by parent class. Injects context and removes nulls.

**Process**:
1. Call parent's `add_fields()` to populate log_record
2. Iterate context.get_all_non_null() and add to log_record
3. Delete all keys with None values
4. Result: clean JSON with only meaningful fields

**Example output**:
```json
{
  "timestamp": "2026-01-27T13:30:00.123456",
  "level": "INFO",
  "logger": "request.lifecycle",
  "message": "GET /api/devices/ completed",
  "request_id": "a1b2c3d4-e5f6-4789",
  "method": "GET",
  "path": "/api/devices/",
  "status_code": 200,
  "duration_ms": 45.67
}
```

Note: All None values are automatically excluded, so logs are never cluttered with null fields.

---

### 4. `src/iot_logging/django_helpers.py`

**Purpose**: Django integration for automatic request context binding.

#### Function: `bind_request_context(request, request_id: Optional[str] = None) -> str`

Binds HTTP request to logging context.

**Args**:
- `request`: Django HttpRequest object
- `request_id`: Optional request ID. If None, generates UUID.

**Returns**: The request_id (for setting in response headers)

**Process**:
1. If request_id not provided, generate UUID
2. Call `context.set_request(request_id, request.method, request.path)`
3. Return request_id

**Usage**:
```python
@view
def my_view(request):
    request_id = bind_request_context(request)
    response = HttpResponse(...)
    response["X-Request-ID"] = request_id
    clear_request_context()
    return response
```

#### Function: `clear_request_context() -> None`

Clears request context. Calls `context.clear_request()`.

---

#### Class: `RequestContextMiddleware`

Django middleware that automatically binds request context to every HTTP request.

**Purpose**: Eliminates boilerplate by automatically:
- Extracting/generating request ID
- Binding to context
- Logging response with duration
- Setting X-Request-ID header
- Clearing context

**Methods**:

##### `__init__(self, get_response) -> None`
Initializes middleware. Called once at Django startup.

**Args**:
- `get_response`: Django's next middleware/view callable

##### `__call__(self, request) -> HttpResponse`
Processes HTTP request and response.

**Process**:
1. Extract request_id from X-Request-ID header, or generate UUID
2. Call `bind_request_context(request, request_id)`
3. Record start_time
4. Call `self.get_response(request)` to execute view
5. Calculate duration_ms
6. Log "HTTP request completed" with status_code and duration_ms
7. Set X-Request-ID response header
8. Call `clear_request_context()`
9. Return response

**Django setup** (settings.py):
```python
MIDDLEWARE = [
    ...
    'iot_logging.django_helpers.RequestContextMiddleware',
    ...
]
```

**Logger**: Uses logger named "request.lifecycle"

---

### 5. `src/iot_logging/celery_helpers.py`

**Purpose**: Celery integration for automatic task context binding via signals.

#### Function: `setup_celery_logging_context() -> None`

Connects Celery signals to logging context. Call once at Celery app startup.

**Behavior**:
- Connects to `task_prerun` signal: binds task context before execution
- Connects to `task_postrun` signal: clears task context after execution

**Process**:
1. Attempts to import Celery signals
2. If ImportError, raises with installation hint
3. Registers signal handlers with weak=False (ensures execution)

**Raises**: ImportError if Celery not installed

**Usage**:
```python
from celery import Celery
from iot_logging.celery_helpers import setup_celery_logging_context

app = Celery(__name__)
setup_celery_logging_context()
```

---

#### Function: `bind_task_context(task_id: str, task_name: str) -> None`

Manually bind task context. Use if not using signals or need explicit control.

**Args**:
- `task_id`: Celery task UUID
- `task_name`: Full task function name

**Usage**:
```python
def my_task(arg1, arg2):
    bind_task_context(
        task_id="abc-123-def",
        task_name="myapp.tasks.my_task"
    )
    # ... task code ...
    clear_task_context()
```

---

#### Function: `clear_task_context() -> None`

Manually clear task context. Calls `context.clear_task()`.

---

#### Function: `get_task_context() -> dict`

Retrieve current task context.

**Returns**: Dictionary with keys task_id and task_name (both may be None)

**Usage**:
```python
ctx = get_task_context()
print(f"Current task: {ctx['task_name']} ({ctx['task_id']})")
```

---

## Schema Modules

All schemas inherit from `BaseLogSchema` and use Pydantic v2 with ConfigDict.

### 6. `src/iot_logging/schemas/base.py`

**Purpose**: Base schema with common fields for all log types.

#### Enum: `LogLevel(str, Enum)`

Standard log levels as string enum.

**Values**:
- `DEBUG = "DEBUG"`
- `INFO = "INFO"`
- `WARNING = "WARNING"`
- `ERROR = "ERROR"`
- `CRITICAL = "CRITICAL"`

#### Class: `BaseLogSchema(BaseModel)`

Base Pydantic model for all log schemas.

**Configuration**: `ConfigDict(use_enum_values=True)` - enums serialized as strings

**Fields**:
- `timestamp: datetime` - Log timestamp (ISO 8601)
- `level: LogLevel` - Log level enum
- `logger: str` - Logger name (e.g., "request.lifecycle")
- `message: str` - Log message text
- `metadata: Optional[Dict[str, Any]] = None` - Custom fields from logger.info(extra={...})

**Inherited by**: HttpRequestLog, CeleryTaskLog, KafkaConsumerLog, GenericServiceLog

---

### 7. `src/iot_logging/schemas/http_request.py`

**Purpose**: HTTP request/response logging for Django, FastAPI, etc.

#### Class: `HttpRequestLog(BaseLogSchema)`

Schema for logging HTTP requests and responses.

**Required Fields**:
- `request_id: str` - Unique request ID for tracing
- `method: str` - HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)
- `path: str` - Request path/endpoint (e.g., "/api/devices/")

**Optional Fields**:
- `status_code: Optional[int]` - HTTP response status (100-599)
- `duration_ms: Optional[float]` - Request duration in milliseconds (≥ 0)
- `user_id: Optional[str]` - Authenticated user ID
- `ip_address: Optional[str]` - Client IP address
- `content_length: Optional[int]` - Response body size in bytes
- `error_type: Optional[str]` - Exception type if error (e.g., "ValueError")
- `error_message: Optional[str]` - Exception message
- `traceback: Optional[str]` - Full stack trace for debugging

**Validation**:
- `status_code`: 100 ≤ value ≤ 599
- `duration_ms`: value ≥ 0

**Example**:
```python
log = HttpRequestLog(
    timestamp=datetime.now(),
    level=LogLevel.INFO,
    logger="request.lifecycle",
    message="GET /api/devices/ completed",
    request_id="a1b2c3d4-e5f6-4789",
    method="GET",
    path="/api/devices/",
    status_code=200,
    duration_ms=45.67,
)
```

---

### 8. `src/iot_logging/schemas/celery_task.py`

**Purpose**: Celery task execution logging.

#### Class: `CeleryTaskLog(BaseLogSchema)`

Schema for logging Celery task execution.

**Required Fields**:
- `task_name: str` - Full task function name (e.g., "apps.core.tasks.process_device_data")
- `task_id: str` - Celery task UUID (auto-generated by Celery)

**Optional Fields**:
- `status: Optional[str]` - Task status (started, success, failure, retry, revoked)
- `request_id: Optional[str]` - Related HTTP request ID if task triggered by request
- `queue: Optional[str]` - Celery queue name (e.g., "default", "high_priority")
- `args: Optional[list]` - Task positional arguments
- `kwargs: Optional[Dict[str, Any]]` - Task keyword arguments
- `duration_ms: Optional[float]` - Task execution time (≥ 0)
- `result: Optional[str]` - Task result/output summary
- `error_type: Optional[str]` - Exception type if failed
- `error_message: Optional[str]` - Exception message
- `retry_count: Optional[int]` - Number of retries (≥ 0)

**Validation**:
- `duration_ms`: value ≥ 0
- `retry_count`: value ≥ 0

**Example**:
```python
log = CeleryTaskLog(
    timestamp=datetime.now(),
    level=LogLevel.INFO,
    logger="celery.task",
    message="Task completed",
    task_name="apps.core.tasks.process_device_data",
    task_id="f1e2d3c4-b5a6-4789-a012-bc3456789abc",
    status="success",
    queue="default",
    duration_ms=1234.56,
)
```

---

### 9. `src/iot_logging/schemas/kafka_consumer.py`

**Purpose**: Kafka consumer message processing logging.

#### Class: `KafkaConsumerLog(BaseLogSchema)`

Schema for logging Kafka message consumption and processing.

**Required Fields**:
- `topic: str` - Kafka topic name (e.g., "telemetry.clean")
- `consumer_group: str` - Consumer group ID (e.g., "iot-hub-db-writer")

**Optional Fields**:
- `partition: Optional[int]` - Partition number (≥ 0)
- `offset: Optional[int]` - Message offset in partition (≥ 0)
- `message_key: Optional[str]` - Kafka message key
- `processing_duration_ms: Optional[float]` - Time to process message (≥ 0)
- `status: Optional[str]` - Processing status (success, error, skipped, dlq)
- `error_type: Optional[str]` - Exception type if error
- `error_message: Optional[str]` - Exception message
- `downstream_latency_ms: Optional[float]` - Time in downstream systems (≥ 0)

**Validation**:
- `partition`: value ≥ 0
- `offset`: value ≥ 0
- `processing_duration_ms`: value ≥ 0
- `downstream_latency_ms`: value ≥ 0

**Example**:
```python
log = KafkaConsumerLog(
    timestamp=datetime.now(),
    level=LogLevel.INFO,
    logger="kafka.consumer",
    message="Message processed",
    topic="telemetry.clean",
    consumer_group="iot-hub-db-writer",
    partition=0,
    offset=12345,
    status="success",
    processing_duration_ms=25.5,
)
```

---

### 10. `src/iot_logging/schemas/generic_service.py`

**Purpose**: Generic logging for background services, cron jobs, batch processes.

#### Class: `GenericServiceLog(BaseLogSchema)`

Schema for logging any service operation (batch jobs, cron tasks, background workers).

**Required Fields**:
- `service_name: str` - Name of the service/component (e.g., "metrics_aggregator")

**Optional Fields**:
- `component: Optional[str]` - Sub-component or module (e.g., "prometheus_exporter")
- `operation: Optional[str]` - Operation being performed (e.g., "export_metrics")
- `duration_ms: Optional[float]` - Operation duration in milliseconds (≥ 0)
- `item_count: Optional[int]` - Items processed/affected (≥ 0)
- `metadata: Optional[Dict[str, Any]]` - Additional metadata (different from base metadata)
- `error_type: Optional[str]` - Exception type if error
- `error_message: Optional[str]` - Exception message

**Validation**:
- `duration_ms`: value ≥ 0
- `item_count`: value ≥ 0

**Example**:
```python
log = GenericServiceLog(
    timestamp=datetime.now(),
    level=LogLevel.INFO,
    logger="service.background",
    message="Batch processing completed",
    service_name="metrics_aggregator",
    component="prometheus_exporter",
    operation="export_metrics",
    duration_ms=1234.56,
    item_count=150,
    metadata={"retention_hours": 24},
)
```

---

## Test Suite

Located in `tests/` directory. 51 passing tests with 95% coverage.

### Test Files

#### `test_schemas.py` (34 tests)
Tests all 5 schema types:
- Field presence and validation
- Required vs optional fields
- Constraint validation (status_code 100-599, duration_ms ≥ 0, etc.)
- JSON serialization
- None field handling

#### `test_formatter.py` (5 tests)
Tests StructuredJsonFormatter:
- None value exclusion
- Custom field injection
- Nested object handling
- Falsy value preservation (0, False, empty strings)

#### `test_context.py` (13 tests)
Tests LoggingContext:
- Context isolation between threads
- get_all() includes None values
- get_all_non_null() filters None values
- Clear operations
- Independent request/task/service contexts

#### `test_django_helpers.py` (8 tests)
Tests Django integration:
- RequestContextMiddleware binds context
- Request ID generation/extraction
- Context cleanup
- Response header injection

#### `test_celery_helpers.py` (8 tests)
Tests Celery integration:
- Signal handler registration
- Task context binding
- Task context independence from request context

---

## Examples

Located in `examples/` directory. Runnable examples for each framework.

### `django_example.py`

Shows Django setup with:
- LOGGING configuration with StructuredJsonFormatter
- RequestContextMiddleware setup
- View logging
- Celery task logging
- Signal handlers

### `fastapi_example.py`

Shows FastAPI setup with:
- Custom middleware for context binding
- Endpoint logging
- Background task context preservation
- Async-safe context management

### `kafka_example.py`

Shows Kafka consumer with:
- Consumer configuration
- Message processing with logging
- Error handling and status tracking
- Topic-specific handling (telemetry vs events)

---

## Development & Testing

### Run All Tests
```bash
pytest                    # Run all tests with coverage
pytest tests/test_context.py -v   # Run specific test file
pytest -k test_middleware          # Run tests matching pattern
```

### Check Code Quality
```bash
flake8 src/ tests/ examples/       # Linting
black --check src/ tests/          # Format check
black src/ tests/                  # Auto-format
```

### Pre-commit Hooks

Automatic checks on git commit:
```bash
git add src/iot_logging/django_helpers.py
git commit -m "Update Django helpers"
# Pre-commit hook automatically runs:
# - flake8 on staged files
# - black format check
# - full pytest suite
```

---

## Usage Summary

### Basic Setup (Django)

```python
# settings.py
LOGGING = {
    'version': 1,
    'formatters': {
        'json': {
            '()': 'iot_logging.StructuredJsonFormatter',
        },
    },
    'handlers': {
        'default': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['default'],
        'level': 'INFO',
    },
}

MIDDLEWARE = [
    'iot_logging.RequestContextMiddleware',
    ...
]
```

### Logging HTTP Requests

```python
from iot_logging import HttpRequestLog
from datetime import datetime

log = HttpRequestLog(
    timestamp=datetime.now(),
    level="INFO",
    logger="request.lifecycle",
    message="Request processed",
    request_id="...",
    method="GET",
    path="/api/devices/",
    status_code=200,
    duration_ms=45.67,
)
```

### Logging Celery Tasks

```python
from celery import Celery
from iot_logging import setup_celery_logging_context

app = Celery(__name__)
setup_celery_logging_context()  # Call once at startup

@app.task
def process_data(device_id):
    logger.info("Processing device", extra={
        "device_id": device_id,
        "status": "started",
    })
```

### Logging Kafka Messages

```python
from kafka import KafkaConsumer
from iot_logging import KafkaConsumerLog

consumer = KafkaConsumer('telemetry.clean', group_id='my-group')

for msg in consumer:
    log = KafkaConsumerLog(
        timestamp=datetime.now(),
        level="INFO",
        logger="kafka.consumer",
        message="Message processed",
        topic="telemetry.clean",
        consumer_group="my-group",
        partition=msg.partition,
        offset=msg.offset,
        status="success",
        processing_duration_ms=25.5,
    )
```

---

## Key Design Decisions

1. **Pydantic v2**: Type-safe schemas with validation
2. **contextvars**: Thread-safe, async-safe context isolation
3. **Automatic injection**: Formatter injects context into all logs
4. **None exclusion**: Removes null values for clean JSON
5. **Optional dependencies**: Celery integration only loaded when needed
6. **Framework agnostic**: Works with any Python logging-compatible framework
7. **100% serializable**: All schemas serialize to JSON without custom encoders
