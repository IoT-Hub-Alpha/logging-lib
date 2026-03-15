"""Tests for JSON formatter."""

import json
import logging
from io import StringIO

import pytest

from iot_logging.formatters.json_formatter import StructuredJsonFormatter


class TestStructuredJsonFormatter:
    """Tests for StructuredJsonFormatter."""

    def test_formatter_excludes_none_values(self):
        """Test that None values are excluded from JSON output."""
        # Create logger with string buffer
        logger = logging.getLogger("test.exclude_none")
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = StructuredJsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Log with extra fields
        logger.info("Test message", extra={"request_id": "req-123", "method": "GET"})

        output = stream.getvalue()
        log_dict = json.loads(output)

        assert "request_id" in log_dict
        assert log_dict["request_id"] == "req-123"
        assert log_dict["method"] == "GET"

    def test_formatter_with_custom_fields(self):
        """Test formatter with custom metadata fields."""
        logger = logging.getLogger("test.custom")
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = StructuredJsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info(
            "Device updated",
            extra={
                "device_id": "dev-456",
                "temperature": 25.5,
                "connection_type": "mqtt",
            },
        )

        output = stream.getvalue()
        log_dict = json.loads(output)

        assert log_dict["device_id"] == "dev-456"
        assert log_dict["temperature"] == 25.5
        assert log_dict["connection_type"] == "mqtt"
        assert log_dict["message"] == "Device updated"

    def test_formatter_with_falsy_values(self):
        """Test that False and 0 values are preserved (not treated as None)."""
        logger = logging.getLogger("test.falsy")
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = StructuredJsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info(
            "Test",
            extra={
                "count": 0,
                "is_active": False,
                "status_code": 200,
            },
        )

        output = stream.getvalue()
        log_dict = json.loads(output)

        assert log_dict["count"] == 0
        assert log_dict["is_active"] is False
        assert log_dict["status_code"] == 200

    def test_formatter_with_dict_values(self):
        """Test formatter with nested dict values."""
        logger = logging.getLogger("test.dicts")
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = StructuredJsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info(
            "Config applied",
            extra={
                "config": {"nested": {"field": "value"}},
                "settings": {"timeout": 30},
            },
        )

        output = stream.getvalue()
        log_dict = json.loads(output)

        assert log_dict["config"]["nested"]["field"] == "value"
        assert log_dict["settings"]["timeout"] == 30

    def test_formatter_multiple_messages(self):
        """Test formatter handles multiple log messages."""
        logger = logging.getLogger("test.multiple")
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = StructuredJsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info("First message", extra={"request_id": "req-1"})
        logger.info(
            "Second message", extra={"request_id": "req-2", "status": "success"}
        )

        output = stream.getvalue()
        lines = [line.strip() for line in output.strip().split("\n") if line]

        assert len(lines) == 2

        log1 = json.loads(lines[0])
        log2 = json.loads(lines[1])

        assert log1["message"] == "First message"
        assert log1["request_id"] == "req-1"
        assert log2["message"] == "Second message"
        assert log2["status"] == "success"
