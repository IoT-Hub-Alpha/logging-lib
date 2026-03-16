"""Generic service log schema."""

from typing import Any, Dict, Optional

from pydantic import ConfigDict, Field

from iot_logging.schemas.base import BaseLogSchema


class GenericServiceLog(BaseLogSchema):
    """Generic logging for background services, cron jobs, etc."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2026-01-27T13:30:25.567890",
                "level": "INFO",
                "logger": "service.background",
                "message": "Batch processing completed",
                "service_name": "metrics_aggregator",
                "component": "prometheus_exporter",
                "operation": "export_metrics",
                "duration_ms": 1234.56,
                "item_count": 150,
                "metadata": {"retention_hours": 24},
            }
        }
    )

    service_name: str = Field(description="Name of the service/component")

    # Optional fields
    component: Optional[str] = Field(None, description="Sub-component or module")
    operation: Optional[str] = Field(None, description="Operation being performed")
    duration_ms: Optional[float] = Field(None, description="Operation duration", ge=0)
    item_count: Optional[int] = Field(
        None, description="Items processed/affected", ge=0
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    error_type: Optional[str] = Field(None, description="Exception type if error")
    error_message: Optional[str] = Field(None, description="Exception message")
