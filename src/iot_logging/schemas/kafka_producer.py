"""Kafka producer log schema."""

from typing import Optional

from pydantic import ConfigDict, Field

from iot_logging.schemas.base import BaseLogSchema


class KafkaProducerLog(BaseLogSchema):
    """Kafka producer message logging."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2026-01-27T13:30:18.345678",
                "level": "INFO",
                "logger": "kafka.producer",
                "message": "Message sent",
                "topic": "telemetry.raw",
                "partition": 0,
                "message_key": "device_123",
                "status": "success",
                "duration_ms": 15.5,
            }
        }
    )

    topic: str = Field(description="Kafka topic name")

    # Optional fields
    partition: Optional[int] = Field(None, description="Target partition number", ge=0)
    message_key: Optional[str] = Field(None, description="Message key")
    duration_ms: Optional[float] = Field(
        None, description="Time to send message in milliseconds", ge=0
    )
    status: Optional[str] = Field(
        None, description="Send status (success, error, timeout)"
    )
    error_type: Optional[str] = Field(None, description="Exception type if error")
    error_message: Optional[str] = Field(None, description="Exception message")
