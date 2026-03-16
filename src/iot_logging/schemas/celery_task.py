"""Celery task log schema."""

from typing import Any, Dict, Optional

from pydantic import ConfigDict, Field

from iot_logging.schemas.base import BaseLogSchema


class CeleryTaskLog(BaseLogSchema):
    """Celery task execution logging."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2026-01-27T13:30:15.234567",
                "level": "INFO",
                "logger": "celery.task",
                "message": "Task started",
                "task_name": "apps.core.tasks.process_device_data",
                "task_id": "f1e2d3c4-b5a6-4789-a012-bc3456789abc",
                "status": "started",
                "request_id": "a1b2c3d4-e5f6-4789",
                "queue": "default",
                "args": ["device_123"],
                "kwargs": {},
            }
        }
    )

    task_name: str = Field(description="Full task function name")
    task_id: str = Field(description="Celery task UUID")

    # Optional fields
    status: Optional[str] = Field(
        None,
        description="Task status (started, success, failure, retry, revoked)",
    )
    request_id: Optional[str] = Field(
        None, description="Related HTTP request ID (if triggered by request)"
    )
    queue: Optional[str] = Field(None, description="Celery queue name")
    args: Optional[list] = Field(None, description="Task positional arguments")
    kwargs: Optional[Dict[str, Any]] = Field(None, description="Task keyword arguments")
    duration_ms: Optional[float] = Field(None, description="Task execution time", ge=0)
    result: Optional[str] = Field(None, description="Task result/output")
    error_type: Optional[str] = Field(None, description="Exception type if failed")
    error_message: Optional[str] = Field(None, description="Exception message")
    retry_count: Optional[int] = Field(None, description="Number of retries", ge=0)
