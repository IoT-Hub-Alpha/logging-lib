"""Tests for Celery integration helpers."""

import pytest

from iot_logging.celery_helpers import (
    bind_task_context,
    clear_task_context,
    get_task_context,
)
from iot_logging.context import context


class TestCeleryHelpers:
    """Tests for Celery helper functions."""

    def setup_method(self):
        """Clear context before each test."""
        clear_task_context()
        context.clear_task()

    def test_bind_task_context(self):
        """Test binding task context."""
        bind_task_context(
            task_id="celery-123",
            task_name="tasks.process_data",
        )

        assert context.task_id.get() == "celery-123"
        assert context.task_name.get() == "tasks.process_data"

    def test_clear_task_context(self):
        """Test clearing task context."""
        bind_task_context(task_id="celery-123", task_name="tasks.process")
        clear_task_context()

        assert context.task_id.get() is None
        assert context.task_name.get() is None

    def test_get_task_context(self):
        """Test getting task context."""
        bind_task_context(
            task_id="celery-456",
            task_name="tasks.send_email",
        )

        task_ctx = get_task_context()

        assert task_ctx["task_id"] == "celery-456"
        assert task_ctx["task_name"] == "tasks.send_email"

    def test_get_task_context_when_empty(self):
        """Test getting task context when nothing is set."""
        task_ctx = get_task_context()

        assert task_ctx["task_id"] is None
        assert task_ctx["task_name"] is None

    def test_bind_multiple_tasks_sequentially(self):
        """Test binding multiple tasks overwrites previous context."""
        bind_task_context(task_id="task-1", task_name="tasks.task1")
        assert context.task_id.get() == "task-1"

        bind_task_context(task_id="task-2", task_name="tasks.task2")
        assert context.task_id.get() == "task-2"
        assert context.task_name.get() == "tasks.task2"

    def test_setup_celery_logging_context_not_installed(self):
        """Test setup_celery_logging_context raises error if Celery not installed."""
        # Note: Celery should be installed in the test environment,
        # so we're testing the import error handling
        from iot_logging.celery_helpers import setup_celery_logging_context

        # Celery should be available in test environment
        try:
            setup_celery_logging_context()
        except ImportError:
            pytest.skip("Celery not installed")

    def test_task_context_with_full_paths(self):
        """Test task context with full module paths."""
        bind_task_context(
            task_id="abc-def-ghi-jkl",
            task_name="myapp.tasks.notifications.send_email",
        )

        assert context.task_id.get() == "abc-def-ghi-jkl"
        assert context.task_name.get() == "myapp.tasks.notifications.send_email"

    def test_task_context_isolated_from_request_context(self):
        """Test that task and request contexts are independent."""
        from iot_logging.django_helpers import bind_request_context

        # Clear both contexts
        context.clear_request()
        context.clear_task()

        # Create a mock request
        class MockRequest:
            method = "POST"
            path = "/api/trigger-task"
            META = {}

        request = MockRequest()
        bind_request_context(request, request_id="req-123")
        bind_task_context(task_id="task-456", task_name="tasks.async_task")

        # Both should be set independently
        assert context.request_id.get() == "req-123"
        assert context.task_id.get() == "task-456"

        # Clear task context
        clear_task_context()

        # Request context should still be intact
        assert context.request_id.get() == "req-123"
        assert context.task_id.get() is None

    def test_setup_celery_logging_context_signal_handlers(self):
        """Test that setup_celery_logging_context connects signal handlers."""
        try:
            from celery.signals import task_prerun, task_postrun
        except ImportError:
            pytest.skip("Celery not installed")

        from iot_logging.celery_helpers import setup_celery_logging_context

        # Clear context
        context.clear_task()

        # Setup signal handlers
        setup_celery_logging_context()

        # Create a mock task object
        class MockTask:
            name = "test_task"

        # Simulate task_prerun signal
        task_prerun.send(sender=None, task_id="signal-task-123", task=MockTask(), **{})

        # Context should be set by signal handler
        assert context.task_id.get() == "signal-task-123"
        assert context.task_name.get() == "test_task"

        # Simulate task_postrun signal
        task_postrun.send(sender=None, **{})

        # Context should be cleared by signal handler
        assert context.task_id.get() is None
        assert context.task_name.get() is None
