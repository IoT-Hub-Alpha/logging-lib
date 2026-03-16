"""Tests for logging context."""

import pytest

from iot_logging.context import LoggingContext, context


class TestLoggingContext:
    """Tests for LoggingContext."""

    def test_context_creation(self):
        """Test creating a new logging context."""
        ctx = LoggingContext()
        assert ctx.request_id.get() is None
        assert ctx.task_id.get() is None

    def test_set_and_get_request_context(self):
        """Test setting and getting request context."""
        ctx = LoggingContext()
        ctx.set_request(
            request_id="req-123",
            method="GET",
            path="/api/users",
        )

        assert ctx.request_id.get() == "req-123"
        assert ctx.request_method.get() == "GET"
        assert ctx.request_path.get() == "/api/users"

    def test_clear_request_context(self):
        """Test clearing request context."""
        ctx = LoggingContext()
        ctx.set_request(
            request_id="req-123",
            method="POST",
            path="/api/users",
        )
        ctx.clear_request()

        assert ctx.request_id.get() is None
        assert ctx.request_method.get() is None
        assert ctx.request_path.get() is None

    def test_set_and_get_task_context(self):
        """Test setting and getting task context."""
        ctx = LoggingContext()
        ctx.set_task(
            task_id="celery-123",
            task_name="tasks.process_data",
        )

        assert ctx.task_id.get() == "celery-123"
        assert ctx.task_name.get() == "tasks.process_data"

    def test_clear_task_context(self):
        """Test clearing task context."""
        ctx = LoggingContext()
        ctx.set_task(task_id="celery-123", task_name="tasks.process")
        ctx.clear_task()

        assert ctx.task_id.get() is None
        assert ctx.task_name.get() is None

    def test_set_and_get_service_context(self):
        """Test setting and getting service context."""
        ctx = LoggingContext()
        ctx.set_service("metrics_processor")

        assert ctx.service_name.get() == "metrics_processor"

    def test_clear_service_context(self):
        """Test clearing service context."""
        ctx = LoggingContext()
        ctx.set_service("metrics_processor")
        ctx.clear_service()

        assert ctx.service_name.get() is None

    def test_get_all_context(self):
        """Test getting all context variables."""
        ctx = LoggingContext()
        ctx.set_request("req-123", "GET", "/api/test")
        ctx.set_task("task-123", "tasks.process")
        ctx.set_service("service-name")

        all_ctx = ctx.get_all()

        assert all_ctx["request_id"] == "req-123"
        assert all_ctx["request_method"] == "GET"
        assert all_ctx["request_path"] == "/api/test"
        assert all_ctx["task_id"] == "task-123"
        assert all_ctx["task_name"] == "tasks.process"
        assert all_ctx["service_name"] == "service-name"

    def test_get_all_non_null(self):
        """Test getting only non-null context variables."""
        ctx = LoggingContext()
        ctx.set_request("req-123", "GET", "/api/test")
        # Don't set task or service

        all_ctx = ctx.get_all_non_null()

        assert "request_id" in all_ctx
        assert "request_method" in all_ctx
        assert "request_path" in all_ctx
        assert "task_id" not in all_ctx
        assert "task_name" not in all_ctx
        assert "service_name" not in all_ctx

    def test_context_isolation(self):
        """Test that separate context instances are isolated."""
        ctx1 = LoggingContext()
        ctx2 = LoggingContext()

        ctx1.set_request("req-1", "GET", "/path1")
        ctx2.set_request("req-2", "POST", "/path2")

        assert ctx1.request_id.get() == "req-1"
        assert ctx2.request_id.get() == "req-2"

    def test_global_context_instance(self):
        """Test the global context instance."""
        # Clear first
        context.clear_request()
        context.clear_task()
        context.clear_service()

        context.set_request("req-global", "PUT", "/global")

        assert context.request_id.get() == "req-global"

        context.clear_request()

    def test_request_and_task_context_together(self):
        """Test that request and task context can coexist."""
        ctx = LoggingContext()
        ctx.set_request("req-123", "POST", "/api/task")
        ctx.set_task("task-456", "tasks.async_process")

        ctx_dict = ctx.get_all()
        assert ctx_dict["request_id"] == "req-123"
        assert ctx_dict["task_id"] == "task-456"

    def test_overwrite_context(self):
        """Test that context can be overwritten."""
        ctx = LoggingContext()
        ctx.set_request("req-1", "GET", "/path1")
        assert ctx.request_id.get() == "req-1"

        ctx.set_request("req-2", "POST", "/path2")
        assert ctx.request_id.get() == "req-2"
        assert ctx.request_method.get() == "POST"
