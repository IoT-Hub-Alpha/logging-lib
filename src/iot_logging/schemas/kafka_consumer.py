"""Kafka consumer log schema."""

from typing import Optional

from pydantic import ConfigDict, Field

from iot_logging.schemas.base import BaseLogSchema


class KafkaConsumerLog(BaseLogSchema):
    """Kafka consumer processing logging."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2026-01-27T13:30:20.456789",
                "level": "INFO",
                "logger": "kafka.consumer",
                "message": "Message processed",
                "topic": "telemetry.clean",
                "consumer_group": "iot-hub-db-writer",
                "partition": 0,
                "offset": 12345,
                "status": "success",
                "processing_duration_ms": 25.5,
            }
        }
    )

    topic: str = Field(description="Kafka topic name")
    consumer_group: str = Field(description="Consumer group ID")

    # Optional fields
    partition: Optional[int] = Field(None, description="Partition number", ge=0)
    offset: Optional[int] = Field(None, description="Message offset in partition", ge=0)
    message_key: Optional[str] = Field(None, description="Message key")
    processing_duration_ms: Optional[float] = Field(
        None, description="Time to process message", ge=0
    )
    status: Optional[str] = Field(
        None, description="Processing status (success, error, skipped, dlq)"
    )
    error_type: Optional[str] = Field(None, description="Exception type if error")
    error_message: Optional[str] = Field(None, description="Exception message")
    downstream_latency_ms: Optional[float] = Field(
        None, description="Time taken in downstream systems", ge=0
    )
