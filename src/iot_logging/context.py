"""Thread-safe context management for logging."""

import contextvars
from typing import Dict, Optional


class LoggingContext:
    """
    Thread-safe context for storing request/task/service context.

    Uses contextvars to maintain isolation across async and threaded contexts.
    """

    def __init__(self):
        """Initialize context variables."""
        self.request_id = contextvars.ContextVar("request_id", default=None)
        self.request_method = contextvars.ContextVar("request_method", default=None)
        self.request_path = contextvars.ContextVar("request_path", default=None)
        self.task_id = contextvars.ContextVar("task_id", default=None)
        self.task_name = contextvars.ContextVar("task_name", default=None)
        self.service_name = contextvars.ContextVar("service_name", default=None)

    def set_request(self, request_id: str, method: str, path: str) -> None:
        """
        Set request context variables.

        Args:
            request_id: Unique request identifier
            method: HTTP method
            path: Request endpoint
        """
        self.request_id.set(request_id)
        self.request_method.set(method)
        self.request_path.set(path)

    def clear_request(self) -> None:
        """Clear request context variables."""
        self.request_id.set(None)
        self.request_method.set(None)
        self.request_path.set(None)

    def set_task(self, task_id: str, task_name: str) -> None:
        """
        Set task context variables.

        Args:
            task_id: Celery task UUID
            task_name: Full task function name
        """
        self.task_id.set(task_id)
        self.task_name.set(task_name)

    def clear_task(self) -> None:
        """Clear task context variables."""
        self.task_id.set(None)
        self.task_name.set(None)

    def set_service(self, service_name: str) -> None:
        """
        Set service context variable.

        Args:
            service_name: Name of the service/component
        """
        self.service_name.set(service_name)

    def clear_service(self) -> None:
        """Clear service context variable."""
        self.service_name.set(None)

    def get_all(self) -> Dict[str, Optional[str]]:
        """
        Get all context variables as a dictionary.

        Returns:
            Dictionary with all context variable values (including None)
        """
        return {
            "request_id": self.request_id.get(),
            "request_method": self.request_method.get(),
            "request_path": self.request_path.get(),
            "task_id": self.task_id.get(),
            "task_name": self.task_name.get(),
            "service_name": self.service_name.get(),
        }

    def get_all_non_null(self) -> Dict[str, str]:
        """
        Get all non-null context variables as a dictionary.

        Returns:
            Dictionary with only non-None context variable values
        """
        return {k: v for k, v in self.get_all().items() if v is not None}


# Global context instance
context = LoggingContext()
