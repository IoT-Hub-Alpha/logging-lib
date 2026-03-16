"""HTTP request log schema for Django, FastAPI, etc."""

from typing import Optional

from pydantic import ConfigDict, Field

from iot_logging.schemas.base import BaseLogSchema


class HttpRequestLog(BaseLogSchema):
    """HTTP request/response logging - for Django, FastAPI, etc."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2026-01-27T13:30:00.123456",
                "level": "INFO",
                "logger": "request.lifecycle",
                "message": "GET /api/devices/ completed",
                "request_id": "a1b2c3d4-e5f6-4789",
                "method": "GET",
                "path": "/api/devices/",
                "status_code": 200,
                "duration_ms": 45.67,
            }
        }
    )

    request_id: str = Field(description="Unique request ID for tracing")
    method: str = Field(description="HTTP method (GET, POST, etc)")
    path: str = Field(description="Request path/endpoint")

    # Optional fields - only include when relevant
    status_code: Optional[int] = Field(
        None, description="HTTP response status", ge=100, le=599
    )
    duration_ms: Optional[float] = Field(
        None, description="Request duration in milliseconds", ge=0
    )
    user_id: Optional[str] = Field(None, description="Authenticated user ID")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    content_length: Optional[int] = Field(None, description="Response body size")
    error_type: Optional[str] = Field(None, description="Exception type if error")
    error_message: Optional[str] = Field(None, description="Exception message")
    traceback: Optional[str] = Field(None, description="Full stack trace")
