"""Unified log schemas for IoT microservices."""

__version__ = "0.1.0"

# Export main schemas
from iot_logging.schemas.base import BaseLogSchema, LogLevel
from iot_logging.schemas.http_request import HttpRequestLog
from iot_logging.schemas.celery_task import CeleryTaskLog
from iot_logging.schemas.kafka_consumer import KafkaConsumerLog
from iot_logging.schemas.generic_service import GenericServiceLog
from iot_logging.formatters.json_formatter import ExcludingNullJsonFormatter

# Export context and helpers
from iot_logging.context import LoggingContext, context
from iot_logging.django_helpers import (
    RequestContextMiddleware,
    bind_request_context,
    clear_request_context,
)
from iot_logging.celery_helpers import (
    setup_celery_logging_context,
    bind_task_context,
    clear_task_context,
    get_task_context,
)

__all__ = [
    # Schemas
    "BaseLogSchema",
    "LogLevel",
    "HttpRequestLog",
    "CeleryTaskLog",
    "KafkaConsumerLog",
    "GenericServiceLog",
    # Formatters
    "ExcludingNullJsonFormatter",
    # Context
    "LoggingContext",
    "context",
    # Django helpers
    "RequestContextMiddleware",
    "bind_request_context",
    "clear_request_context",
    # Celery helpers
    "setup_celery_logging_context",
    "bind_task_context",
    "clear_task_context",
    "get_task_context",
]
