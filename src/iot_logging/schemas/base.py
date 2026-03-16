"""Base log schema with common fields."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class LogLevel(str, Enum):
    """Standard log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BaseLogSchema(BaseModel):
    """Base for all log schemas - only common fields."""

    model_config = ConfigDict(use_enum_values=True)

    timestamp: datetime = Field(description="Log timestamp (ISO 8601)")
    level: LogLevel = Field(description="Log level")
    logger: str = Field(description="Logger name (e.g., 'request.lifecycle')")
    message: str = Field(description="Log message")

    # Optional: Custom metadata (extra={} from logging.Logger.info())
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Custom fields from logger.info(extra={...})"
    )
