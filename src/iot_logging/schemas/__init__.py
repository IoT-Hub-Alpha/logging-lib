"""Log schema definitions for different microservice patterns."""

from iot_logging.schemas.base import BaseLogSchema, LogLevel
from iot_logging.schemas.http_request import HttpRequestLog
from iot_logging.schemas.celery_task import CeleryTaskLog
from iot_logging.schemas.kafka_consumer import KafkaConsumerLog
from iot_logging.schemas.kafka_producer import KafkaProducerLog
from iot_logging.schemas.generic_service import GenericServiceLog

__all__ = [
    "BaseLogSchema",
    "LogLevel",
    "HttpRequestLog",
    "CeleryTaskLog",
    "KafkaConsumerLog",
    "KafkaProducerLog",
    "GenericServiceLog",
]
