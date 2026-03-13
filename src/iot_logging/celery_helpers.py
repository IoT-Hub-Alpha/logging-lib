"""Celery integration helpers for logging context."""

from typing import Optional

from iot_logging.context import context


def setup_celery_logging_context() -> None:
    """
    Connect Celery signals to logging context.

    This should be called once at Celery app initialization.
    Automatically binds task context before task execution and clears it after.

    Usage:
        from celery import Celery
        from iot_logging.celery_helpers import setup_celery_logging_context

        app = Celery(__name__)
        setup_celery_logging_context()
    """
    try:
        from celery.signals import task_postrun, task_prerun
    except ImportError:
        raise ImportError("Celery is not installed. Install with: pip install celery")

    @task_prerun.connect(weak=False)
    def _task_prerun(task_id: str = None, task=None, **kwargs) -> None:
        """Bind task context before execution."""
        context.set_task(
            task_id=task_id,
            task_name=getattr(task, "name", "unknown"),
        )

    @task_postrun.connect(weak=False)
    def _task_postrun(**kwargs) -> None:
        """Clear task context after execution."""
        context.clear_task()


def bind_task_context(task_id: str, task_name: str) -> None:
    """
    Manually bind task context.

    Use this if you're not using Celery signals or need more control.

    Args:
        task_id: Celery task UUID
        task_name: Full task function name
    """
    context.set_task(task_id=task_id, task_name=task_name)


def clear_task_context() -> None:
    """Manually clear task context."""
    context.clear_task()


def get_task_context() -> dict:
    """
    Get current task context.

    Returns:
        dict: Dictionary with task_id and task_name (both may be None)
    """
    return {
        "task_id": context.task_id.get(),
        "task_name": context.task_name.get(),
    }
