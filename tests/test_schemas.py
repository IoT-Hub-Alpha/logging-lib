"""Tests for log schemas."""

from datetime import datetime

import pytest

from iot_logging.schemas.base import BaseLogSchema, LogLevel
from iot_logging.schemas.celery_task import CeleryTaskLog
from iot_logging.schemas.generic_service import GenericServiceLog
from iot_logging.schemas.http_request import HttpRequestLog
from iot_logging.schemas.kafka_consumer import KafkaConsumerLog


class TestBaseLogSchema:
    """Tests for BaseLogSchema."""

    def test_base_log_schema_creation(self):
        """Test creating a base log schema."""
        log = BaseLogSchema(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            logger="test.logger",
            message="Test message",
        )
        assert log.level == LogLevel.INFO
        assert log.message == "Test message"

    def test_base_log_schema_with_metadata(self):
        """Test base schema with custom metadata."""
        log = BaseLogSchema(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            logger="test.logger",
            message="Error occurred",
            metadata={"custom_field": "value", "count": 42},
        )
        assert log.metadata["custom_field"] == "value"
        assert log.metadata["count"] == 42

    def test_log_level_enum(self):
        """Test LogLevel enum values."""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"

    def test_timestamp_serialization(self):
        """Test timestamp serialization to JSON format."""
        now = datetime.now()
        log = BaseLogSchema(
            timestamp=now,
            level=LogLevel.INFO,
            logger="test",
            message="test",
        )
        # When using model_dump_json, timestamps are serialized to ISO strings
        log_json = log.model_dump_json()
        assert "T" in log_json  # ISO format present in JSON
        # model_dump returns datetime objects, which is expected in Pydantic v2
        log_dict = log.model_dump()
        assert isinstance(log_dict["timestamp"], datetime)


class TestHttpRequestLog:
    """Tests for HttpRequestLog."""

    def test_http_request_log_required_fields(self):
        """Test HTTP request log with required fields."""
        log = HttpRequestLog(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            logger="request.lifecycle",
            message="GET /api/users completed",
            request_id="req-123",
            method="GET",
            path="/api/users",
        )
        assert log.request_id == "req-123"
        assert log.method == "GET"
        assert log.path == "/api/users"

    def test_http_request_log_with_optional_fields(self):
        """Test HTTP request log with optional fields."""
        log = HttpRequestLog(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            logger="request.lifecycle",
            message="POST /api/users completed",
            request_id="req-123",
            method="POST",
            path="/api/users",
            status_code=201,
            duration_ms=45.5,
            user_id="user-456",
        )
        assert log.status_code == 201
        assert log.duration_ms == 45.5
        assert log.user_id == "user-456"

    def test_http_request_log_exclude_none(self):
        """Test that None fields are excluded from serialization."""
        log = HttpRequestLog(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            logger="request.lifecycle",
            message="GET /api/users completed",
            request_id="req-123",
            method="GET",
            path="/api/users",
            status_code=200,
        )
        log_dict = log.model_dump(exclude_none=True)
        # These should not be present
        assert "duration_ms" not in log_dict
        assert "user_id" not in log_dict
        assert "ip_address" not in log_dict
        assert "error_type" not in log_dict
        # These should be present
        assert "request_id" in log_dict
        assert "method" in log_dict


class TestCeleryTaskLog:
    """Tests for CeleryTaskLog."""

    def test_celery_task_log_required_fields(self):
        """Test Celery task log with required fields."""
        log = CeleryTaskLog(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            logger="celery.task",
            message="Task started",
            task_name="tasks.process_data",
            task_id="celery-123-abc",
        )
        assert log.task_name == "tasks.process_data"
        assert log.task_id == "celery-123-abc"

    def test_celery_task_log_with_status(self):
        """Test Celery task log with status tracking."""
        log = CeleryTaskLog(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            logger="celery.task",
            message="Task completed",
            task_name="tasks.process_data",
            task_id="celery-123-abc",
            status="success",
            duration_ms=1234.5,
        )
        assert log.status == "success"
        assert log.duration_ms == 1234.5

    def test_celery_task_log_with_error(self):
        """Test Celery task log with error tracking."""
        log = CeleryTaskLog(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            logger="celery.task",
            message="Task failed",
            task_name="tasks.process_data",
            task_id="celery-123-abc",
            status="failure",
            error_type="ValueError",
            error_message="Invalid input",
        )
        assert log.status == "failure"
        assert log.error_type == "ValueError"


class TestKafkaConsumerLog:
    """Tests for KafkaConsumerLog."""

    def test_kafka_consumer_log_required_fields(self):
        """Test Kafka consumer log with required fields."""
        log = KafkaConsumerLog(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            logger="kafka.consumer",
            message="Message processed",
            topic="telemetry.raw",
            consumer_group="analytics-group",
        )
        assert log.topic == "telemetry.raw"
        assert log.consumer_group == "analytics-group"

    def test_kafka_consumer_log_with_partition_offset(self):
        """Test Kafka consumer log with partition and offset."""
        log = KafkaConsumerLog(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            logger="kafka.consumer",
            message="Message processed",
            topic="telemetry.raw",
            consumer_group="analytics-group",
            partition=0,
            offset=12345,
            processing_duration_ms=25.5,
        )
        assert log.partition == 0
        assert log.offset == 12345
        assert log.processing_duration_ms == 25.5


class TestGenericServiceLog:
    """Tests for GenericServiceLog."""

    def test_generic_service_log_required_fields(self):
        """Test generic service log with required fields."""
        log = GenericServiceLog(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            logger="service.background",
            message="Batch processing started",
            service_name="metrics_processor",
        )
        assert log.service_name == "metrics_processor"

    def test_generic_service_log_with_metadata(self):
        """Test generic service log with operation metadata."""
        log = GenericServiceLog(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            logger="service.background",
            message="Batch processing completed",
            service_name="metrics_processor",
            component="exporter",
            operation="export_metrics",
            item_count=150,
            duration_ms=1234.5,
        )
        assert log.component == "exporter"
        assert log.item_count == 150
        assert log.duration_ms == 1234.5


class TestSchemaValidation:
    """Tests for schema validation constraints."""

    def test_duration_ms_must_be_non_negative(self):
        """Test that duration_ms cannot be negative."""
        with pytest.raises(ValueError):
            HttpRequestLog(
                timestamp=datetime.now(),
                level=LogLevel.INFO,
                logger="request.lifecycle",
                message="test",
                request_id="req-123",
                method="GET",
                path="/api/test",
                duration_ms=-1.5,  # Invalid
            )

    def test_status_code_must_be_valid_http(self):
        """Test HTTP status code constraints."""
        with pytest.raises(ValueError):
            HttpRequestLog(
                timestamp=datetime.now(),
                level=LogLevel.INFO,
                logger="request.lifecycle",
                message="test",
                request_id="req-123",
                method="GET",
                path="/api/test",
                status_code=999,  # Invalid HTTP status
            )

    def test_kafka_offset_must_be_non_negative(self):
        """Test that Kafka offset cannot be negative."""
        with pytest.raises(ValueError):
            KafkaConsumerLog(
                timestamp=datetime.now(),
                level=LogLevel.INFO,
                logger="kafka.consumer",
                message="test",
                topic="test.topic",
                consumer_group="test-group",
                offset=-1,  # Invalid
            )

    def test_item_count_must_be_non_negative(self):
        """Test that item_count cannot be negative."""
        with pytest.raises(ValueError):
            GenericServiceLog(
                timestamp=datetime.now(),
                level=LogLevel.INFO,
                logger="service",
                message="test",
                service_name="test_service",
                item_count=-5,  # Invalid
            )
