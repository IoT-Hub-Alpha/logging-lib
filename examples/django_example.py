"""
Django integration example for iot-logging-schemas.

This example shows how to configure and use the logging library in a Django app.
Context fields (request_id, request_method, request_path, task_id, task_name) are
automatically injected by StructuredJsonFormatter - no need to pass them manually.
"""

import logging

# ===== Django settings.py =====
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "iot_logging.StructuredJsonFormatter",
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

logger = logging.getLogger(__name__)


def device_list_view(request):
    """Example view that logs request details."""
    from django.http import JsonResponse

    # Context (request_id, request_method, request_path) is automatically bound by middleware
    # and auto-injected by StructuredJsonFormatter
    logger.info(
        "Listing devices",
        extra={
            "operation": "list",
            "event": "devices_fetched",
        },
    )

    # Simulate processing
    devices = [{"id": "dev-1", "name": "Device 1"}]

    # Log response - status_code and duration_ms are logged by middleware
    logger.info(
        "Device list response",
        extra={
            "item_count": len(devices),
            "event": "list_complete",
        },
    )

    return JsonResponse({"devices": devices})


# ===== Usage in tasks.py (Celery) =====

from celery import shared_task  # noqa: E402

logger = logging.getLogger(__name__)


@shared_task
def process_device_data(device_id):
    """Example Celery task."""
    logger.info(
        "Processing device data",
        extra={
            "device_id": device_id,
            "status": "started",
            "event": "device_processing_start",
        },
    )

    try:
        # Process data
        logger.info(
            "Device data processed",
            extra={
                "device_id": device_id,
                "status": "success",
                "duration_ms": 125.5,
                "event": "device_processing_complete",
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
                "event": "device_processing_error",
            },
            exc_info=True,
        )
        raise


# ===== Setup Celery logging context =====

# In your celery.py or __init__.py
from iot_logging import setup_celery_logging_context  # noqa: E402

# This connects Celery signals to automatically bind task_id and task_name to context
setup_celery_logging_context()
