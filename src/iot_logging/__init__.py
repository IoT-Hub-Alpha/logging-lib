"""Unified log schemas for IoT microservices."""

__version__ = "0.1.0"

# Export main schemas
from iot_logging.schemas.base import BaseLogSchema, LogLevel
from iot_logging.schemas.http_request import HttpRequestLog
from iot_logging.schemas.celery_task import CeleryTaskLog
from iot_logging.schemas.kafka_consumer import KafkaConsumerLog
from iot_logging.schemas.kafka_producer import KafkaProducerLog
from iot_logging.schemas.generic_service import GenericServiceLog
from iot_logging.formatters.json_formatter import StructuredJsonFormatter

# Export context and helpers
from iot_logging.context import LoggingContext, context
from iot_logging.django_helpers import (
    RequestContextMiddleware,
    bind_request_context as django_bind_request_context,
    clear_request_context as django_clear_request_context,
)
from iot_logging.celery_helpers import (
    setup_celery_logging_context,
    bind_task_context,
    clear_task_context,
    get_task_context,
)

# FastAPI helpers (optional import)
try:
    from iot_logging.fastapi_helpers import (
        RequestContextMiddleware as FastAPIRequestContextMiddleware,
        bind_request_context,  # FastAPI-specific: uses request.url.path
        clear_request_context,  # FastAPI-specific
    )
except ImportError:
    # FastAPI not installed - provide placeholders
    FastAPIRequestContextMiddleware = None
    bind_request_context = None
    clear_request_context = None

__all__ = [
    # Schemas
    "BaseLogSchema",
    "LogLevel",
    "HttpRequestLog",
    "CeleryTaskLog",
    "KafkaConsumerLog",
    "KafkaProducerLog",
    "GenericServiceLog",
    # Formatters
    "StructuredJsonFormatter",
    # Context
    "LoggingContext",
    "context",
    # Django helpers (backward compatible)
    "RequestContextMiddleware",
    "django_bind_request_context",
    "django_clear_request_context",
    # FastAPI helpers
    "FastAPIRequestContextMiddleware",
    "bind_request_context",
    "clear_request_context",
    # Celery helpers
    "setup_celery_logging_context",
    "bind_task_context",
    "clear_task_context",
    "get_task_context",
]
