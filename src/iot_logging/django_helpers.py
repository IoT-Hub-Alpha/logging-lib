"""Django integration helpers for logging context."""

import logging
import time
import uuid
from typing import Optional

from iot_logging.context import context

logger = logging.getLogger("request.lifecycle")


def bind_request_context(
    request,
    request_id: Optional[str] = None,
) -> str:
    """
    Bind HTTP request to logging context.

    Extracts request details and stores them in the global logging context.
    Returns the request_id for use in response headers.

    Args:
        request: Django HTTP request object
        request_id: Optional request ID; generates UUID if not provided

    Returns:
        str: The request ID being used (for setting in response headers)
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    context.set_request(
        request_id=request_id,
        method=request.method,
        path=request.path,
    )
    return request_id


def clear_request_context() -> None:
    """Clear request context."""
    context.clear_request()


class RequestContextMiddleware:
    """
    Django middleware to automatically bind request context.

    Adds a request ID to incoming requests and binds it to the logging context.

    Usage in settings.py:
        MIDDLEWARE = [
            ...
            'iot_logging.django_helpers.RequestContextMiddleware',
            ...
        ]
    """

    def __init__(self, get_response):
        """Initialize middleware."""
        self.get_response = get_response

    def __call__(self, request):
        """Process request and response."""
        # Generate or extract request ID from header
        request_id = request.META.get("HTTP_X_REQUEST_ID", str(uuid.uuid4()))

        # Bind to context
        bind_request_context(request, request_id=request_id)

        start_time = time.time()

        # Process request
        response = self.get_response(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Log HTTP request (context already injected by formatter)
        logger.info(
            "HTTP request completed",
            extra={
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        # Add request ID to response headers
        response["X-Request-ID"] = request_id

        # Clear context after response
        clear_request_context()

        return response
