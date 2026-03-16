"""
FastAPI integration example for iot-logging-schemas.

This example shows how to configure and use the logging library in a FastAPI app.
Context fields (request_id, request_method, request_path, task_id, task_name) are
automatically injected by StructuredJsonFormatter - no need to pass them manually.
"""

import logging

from fastapi import FastAPI
from iot_logging import FastAPIRequestContextMiddleware, StructuredJsonFormatter

# Configure logging with JSON formatter
logging.basicConfig(level=logging.INFO)
for handler in logging.root.handlers:
    handler.setFormatter(StructuredJsonFormatter())

logger = logging.getLogger(__name__)

# ===== Create FastAPI app =====

app = FastAPI()

# ===== Add request context middleware from logging-lib =====
# This middleware automatically:
# - Extracts or generates request ID from x-request-id header
# - Binds request context (request_id, method, path)
# - Logs request completion with status_code and duration_ms
# - Sets x-request-id response header
# - Clears context after response (with exception handling)
app.add_middleware(FastAPIRequestContextMiddleware)


# ===== Example endpoints =====


@app.get("/api/devices")
async def list_devices():
    """Get list of devices."""
    logger.info(
        "Querying devices",
        extra={
            "operation": "list_devices",
            "event": "devices_queried",
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
            "event": "device_created",
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
            "event": "device_retrieved",
        },
    )
    return {"id": device_id, "name": f"Device {device_id}", "status": "online"}


# ===== Example background task =====

from concurrent.futures import ThreadPoolExecutor  # noqa: E402
import asyncio  # noqa: E402

executor = ThreadPoolExecutor(max_workers=2)


async def background_task(task_name: str):
    """Example background task."""
    task_logger = logging.getLogger(__name__)

    task_logger.info(
        "Background task started",
        extra={
            "task_name": task_name,
            "event": "task_started",
        },
    )

    # Simulate work
    await asyncio.sleep(1)

    task_logger.info(
        "Background task completed",
        extra={
            "task_name": task_name,
            "status": "success",
            "event": "task_completed",
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
            "event": "sync_scheduled",
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
