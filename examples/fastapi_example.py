"""
FastAPI integration example for iot-logging-schemas.

This example shows how to configure and use the logging library in a FastAPI app.
"""

import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from iot_logging.formatters.json_formatter import StructuredJsonFormatter
from iot_logging.context import context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("request.lifecycle")

# Set up JSON formatter
handler = logging.StreamHandler()
formatter = StructuredJsonFormatter()
handler.setFormatter(formatter)
logger.handlers = [handler]

# ===== Create FastAPI app =====

app = FastAPI()


# ===== Middleware for request logging =====


@app.middleware("http")
async def log_request_context(request: Request, call_next):
    """
    Middleware to bind request context and log request details.
    """
    # Generate or extract request ID
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

    # Bind to context
    context.set_request(
        request_id=request_id,
        method=request.method,
        path=request.path,
    )

    # Start timing
    start_time = time.time()

    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.path,
        },
    )

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        # Add request ID to response headers
        response.headers["x-request-id"] = request_id

        return response

    except Exception as e:
        # Log error
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            "Request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.path,
                "status_code": 500,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        raise

    finally:
        # Clear context
        context.clear_request()


# ===== Example endpoints =====


@app.get("/api/devices")
async def list_devices():
    """Get list of devices."""
    logger.info(
        "Querying devices",
        extra={
            "operation": "list_devices",
            "query_params": {"limit": 100},
        },
    )
    return {"devices": [{"id": "dev-1", "name": "Device 1"}]}


@app.post("/api/devices")
async def create_device(device_data: dict):
    """Create a new device."""
    logger.info(
        "Creating device",
        extra={
            "operation": "create_device",
            "device_name": device_data.get("name"),
        },
    )
    return {"id": "dev-123", "name": device_data.get("name"), "status": "created"}


@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """Get a specific device."""
    logger.info(
        "Retrieving device",
        extra={
            "operation": "get_device",
            "device_id": device_id,
        },
    )
    return {"id": device_id, "name": f"Device {device_id}", "status": "online"}


# ===== Example background task =====

from concurrent.futures import ThreadPoolExecutor  # noqa: E402
import asyncio  # noqa: E402

executor = ThreadPoolExecutor(max_workers=2)


async def background_task(task_name: str):
    """Example background task."""
    task_logger = logging.getLogger("background.task")

    # Get current request context if available
    request_id = context.request_id.get()

    task_logger.info(
        "Background task started",
        extra={
            "task_name": task_name,
            "request_id": request_id,
        },
    )

    # Simulate work
    await asyncio.sleep(1)

    task_logger.info(
        "Background task completed",
        extra={
            "task_name": task_name,
            "request_id": request_id,
            "status": "success",
        },
    )


@app.post("/api/devices/{device_id}/sync")
async def sync_device(device_id: str):
    """Sync device data in background."""
    logger.info(
        "Scheduling device sync",
        extra={
            "device_id": device_id,
            "operation": "schedule_sync",
        },
    )

    # Schedule background task
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        executor, lambda: asyncio.run(background_task(f"sync_{device_id}"))
    )

    return {"message": "Sync scheduled", "device_id": device_id}


# ===== Run app =====

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
