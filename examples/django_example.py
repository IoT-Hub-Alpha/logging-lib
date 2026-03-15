"""
Django integration example for iot-logging-schemas.

This example shows how to configure and use the logging library in a Django app.
"""

import logging

# ===== Django settings.py =====
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "iot_logging.formatters.json_formatter.StructuredJsonFormatter",
            "fmt": (
                "%(asctime)s %(levelname)s %(name)s %(message)s "
                "%(request_id)s %(method)s %(path)s %(status_code)s %(duration_ms)s"
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# Configure middleware in settings.py
MIDDLEWARE = [
    # ... other middleware ...
    "iot_logging.django_helpers.RequestContextMiddleware",
    # ... rest of middleware ...
]

# ===== Usage in views.py =====

logger = logging.getLogger("request.lifecycle")


def device_list_view(request):
    """Example view that logs request details."""
    from django.http import JsonResponse
    from iot_logging.context import context

    # Context is automatically bound by middleware
    # Log request start
    logger.info(
        "Listing devices",
        extra={
            "method": request.method,
            "path": request.path,
        },
    )

    # Simulate processing
    devices = [{"id": "dev-1", "name": "Device 1"}]

    # Log response
    logger.info(
        "Device list response",
        extra={
            "status_code": 200,
            "item_count": len(devices),
            "duration_ms": 45.5,
        },
    )

    return JsonResponse({"devices": devices})


# ===== Usage in tasks.py (Celery) =====

from celery import shared_task  # noqa: E402
from iot_logging.context import context  # noqa: E402

logger = logging.getLogger("celery.task")


@shared_task
def process_device_data(device_id):
    """Example Celery task."""
    logger.info(
        "Processing device data",
        extra={
            "device_id": device_id,
            "status": "started",
        },
    )

    # Get request context if this was triggered by a request
    request_id = context.request_id.get()

    try:
        # Process data
        logger.info(
            "Device data processed",
            extra={
                "device_id": device_id,
                "status": "success",
                "duration_ms": 125.5,
                "request_id": request_id,
            },
        )
    except Exception as e:
        logger.error(
            "Device data processing failed",
            extra={
                "device_id": device_id,
                "status": "failure",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "request_id": request_id,
            },
        )
        raise


# ===== Setup Celery logging context =====

# In your celery.py or __init__.py
from iot_logging.celery_helpers import setup_celery_logging_context  # noqa: E402

setup_celery_logging_context()
