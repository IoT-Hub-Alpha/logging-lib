"""FastAPI integration helpers for logging context."""

import logging
import time
import uuid
from typing import Callable, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from iot_logging.context import context

logger = logging.getLogger("request.lifecycle")


def bind_request_context(
    request: Request,
    request_id: Optional[str] = None,
) -> str:
    """
    Bind HTTP request to logging context.

    Extracts request details and stores them in the global logging context.
    Returns the request_id for use in response headers.

    Args:
        request: FastAPI/Starlette Request object
        request_id: Optional request ID; generates UUID if not provided

    Returns:
        str: The request ID being used (for setting in response headers)
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    context.set_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    return request_id


def clear_request_context() -> None:
    """Clear request context."""
    context.clear_request()


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to automatically bind request context.

    Adds a request ID to incoming requests and binds it to the logging context.

    Usage in FastAPI app:
        from fastapi import FastAPI
        from iot_logging.fastapi_helpers import RequestContextMiddleware

        app = FastAPI()
        app.add_middleware(RequestContextMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> any:
        """Process request and response."""
        # Generate or extract request ID from header
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        # Bind to context
        bind_request_context(request, request_id=request_id)

        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)
        except Exception as e:
            # Log error with context
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "HTTP request failed",
                extra={
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            raise
        finally:
            # Clear context after response
            clear_request_context()

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
        response.headers["x-request-id"] = request_id

        return response
