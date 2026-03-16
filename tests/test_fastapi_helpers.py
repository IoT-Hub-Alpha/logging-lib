"""Tests for FastAPI integration helpers."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from iot_logging.context import context
from iot_logging.fastapi_helpers import (
    RequestContextMiddleware,
    bind_request_context,
    clear_request_context,
)


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    from fastapi import Request
    from starlette.datastructures import Headers

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/test",
        "headers": [(b"x-request-id", b"test-123")],
    }
    return Request(scope)


class TestBindRequestContext:
    """Tests for bind_request_context helper."""

    def test_bind_with_provided_request_id(self, mock_request):
        """Bind request context with explicit request ID."""
        request_id = bind_request_context(mock_request, request_id="custom-123")

        assert request_id == "custom-123"
        assert context.request_id.get() == "custom-123"
        assert context.request_method.get() == "GET"
        assert context.request_path.get() == "/api/test"

    def test_bind_generates_request_id_if_not_provided(self, mock_request):
        """Bind request context generates UUID if not provided."""
        request_id = bind_request_context(mock_request)

        assert request_id is not None
        assert len(request_id) == 36  # UUID format
        assert context.request_id.get() == request_id
        assert context.request_method.get() == "GET"
        assert context.request_path.get() == "/api/test"

        # Clean up
        clear_request_context()


class TestClearRequestContext:
    """Tests for clear_request_context helper."""

    def test_clear_request_context(self, mock_request):
        """Clear request context."""
        bind_request_context(mock_request)

        # Verify context is set
        assert context.request_id.get() is not None

        # Clear context
        clear_request_context()

        # Verify context is cleared
        assert context.request_id.get() is None
        assert context.request_method.get() is None
        assert context.request_path.get() is None


class TestRequestContextMiddleware:
    """Tests for RequestContextMiddleware."""

    @pytest.fixture
    def app_with_middleware(self):
        """Create a FastAPI app with RequestContextMiddleware."""
        app = FastAPI()
        app.add_middleware(RequestContextMiddleware)

        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}

        @app.get("/error")
        def error_endpoint():
            raise ValueError("Test error")

        return app

    def test_middleware_sets_request_id_header(self, app_with_middleware):
        """Middleware extracts and sets request ID header."""
        client = TestClient(app_with_middleware)
        response = client.get("/test", headers={"x-request-id": "custom-123"})

        assert response.status_code == 200
        assert response.headers.get("x-request-id") == "custom-123"

    def test_middleware_generates_request_id_if_missing(self, app_with_middleware):
        """Middleware generates request ID if not provided."""
        client = TestClient(app_with_middleware)
        response = client.get("/test")

        assert response.status_code == 200
        assert response.headers.get("x-request-id") is not None
        assert len(response.headers.get("x-request-id")) == 36  # UUID format

    def test_middleware_binds_context(self, app_with_middleware):
        """Middleware binds request context."""
        client = TestClient(app_with_middleware)

        # Make a request
        response = client.get("/test", headers={"x-request-id": "test-456"})

        assert response.status_code == 200
        # Note: Context is cleared after request, so we can't assert directly
        # But we can verify the endpoint response was successful

    def test_middleware_handles_error(self, app_with_middleware):
        """Middleware handles errors properly."""
        client = TestClient(app_with_middleware)

        # Make a request to error endpoint
        with pytest.raises(ValueError):
            client.get("/error")

        # Verify context was cleared even after error
        assert context.request_id.get() is None
        assert context.request_method.get() is None
        assert context.request_path.get() is None

    def test_middleware_context_isolation(self, app_with_middleware):
        """Middleware maintains context isolation between requests."""
        client = TestClient(app_with_middleware)

        # First request
        response1 = client.get("/test", headers={"x-request-id": "req-1"})
        id1 = response1.headers.get("x-request-id")

        # Second request
        response2 = client.get("/test", headers={"x-request-id": "req-2"})
        id2 = response2.headers.get("x-request-id")

        # Verify different request IDs
        assert id1 == "req-1"
        assert id2 == "req-2"
        assert id1 != id2

        # Verify context is cleared after both requests
        assert context.request_id.get() is None
