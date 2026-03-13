"""Tests for Django integration helpers."""

import pytest

from iot_logging.django_helpers import (
    bind_request_context,
    clear_request_context,
    RequestContextMiddleware,
)
from iot_logging.context import context


class MockRequest:
    """Mock Django request object."""

    def __init__(self, method="GET", path="/test"):
        self.method = method
        self.path = path
        self.META = {}


class TestDjangoHelpers:
    """Tests for Django helper functions."""

    def setup_method(self):
        """Clear context before each test."""
        clear_request_context()
        context.clear_request()

    def test_bind_request_context_with_explicit_id(self):
        """Test binding request context with explicit request ID."""
        request = MockRequest(method="GET", path="/api/users")
        request_id = bind_request_context(request, request_id="req-123")

        assert request_id == "req-123"
        assert context.request_id.get() == "req-123"
        assert context.request_method.get() == "GET"
        assert context.request_path.get() == "/api/users"

    def test_bind_request_context_generates_id(self):
        """Test binding request context generates UUID if no ID provided."""
        request = MockRequest(method="POST", path="/api/devices")
        request_id = bind_request_context(request)

        assert request_id is not None
        assert len(request_id) > 0
        assert context.request_id.get() == request_id
        assert context.request_method.get() == "POST"

    def test_clear_request_context(self):
        """Test clearing request context."""
        request = MockRequest()
        bind_request_context(request, request_id="req-123")
        clear_request_context()

        assert context.request_id.get() is None
        assert context.request_method.get() is None
        assert context.request_path.get() is None

    def test_bind_multiple_requests_sequentially(self):
        """Test binding multiple requests clears previous context."""
        req1 = MockRequest(method="GET", path="/api/users")
        req2 = MockRequest(method="POST", path="/api/devices")

        bind_request_context(req1, request_id="req-1")
        assert context.request_id.get() == "req-1"

        bind_request_context(req2, request_id="req-2")
        assert context.request_id.get() == "req-2"
        assert context.request_method.get() == "POST"
        assert context.request_path.get() == "/api/devices"


class TestRequestContextMiddleware:
    """Tests for RequestContextMiddleware."""

    def setup_method(self):
        """Clear context before each test."""
        clear_request_context()
        context.clear_request()

    def test_middleware_adds_request_id_to_response(self):
        """Test middleware adds request ID to response headers."""

        def mock_get_response(request):
            class MockResponse:
                def __init__(self):
                    self.headers = {}

                def __setitem__(self, key, value):
                    self.headers[key] = value

            return MockResponse()

        request = MockRequest(method="GET", path="/api/test")
        middleware = RequestContextMiddleware(mock_get_response)

        response = middleware(request)

        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] is not None

    def test_middleware_extracts_request_id_from_header(self):
        """Test middleware extracts request ID from X-Request-ID header."""

        def mock_get_response(request):
            class MockResponse:
                def __init__(self):
                    self.headers = {}

                def __setitem__(self, key, value):
                    self.headers[key] = value

            return MockResponse()

        request = MockRequest(method="GET", path="/api/test")
        request.META["HTTP_X_REQUEST_ID"] = "external-req-123"

        middleware = RequestContextMiddleware(mock_get_response)
        response = middleware(request)

        assert response.headers["X-Request-ID"] == "external-req-123"

    def test_middleware_binds_request_context(self):
        """Test middleware binds request to context."""

        def mock_get_response(request):
            class MockResponse:
                def __init__(self):
                    self.headers = {}

                def __setitem__(self, key, value):
                    self.headers[key] = value

            return MockResponse()

        request = MockRequest(method="POST", path="/api/devices")
        middleware = RequestContextMiddleware(mock_get_response)

        # Context should be set during middleware execution
        middleware(request)

        # After middleware, context should be cleared
        assert context.request_id.get() is None
        assert context.request_method.get() is None

    def test_middleware_clears_context_after_response(self):
        """Test middleware clears context after generating response."""

        call_count = [0]

        def mock_get_response(request):
            # Check that context is set while processing request
            call_count[0] = 1
            assert context.request_id.get() is not None
            assert context.request_method.get() == "GET"

            class MockResponse:
                def __init__(self):
                    self.headers = {}

                def __setitem__(self, key, value):
                    self.headers[key] = value

            return MockResponse()

        request = MockRequest(method="GET", path="/api/test")
        middleware = RequestContextMiddleware(mock_get_response)

        middleware(request)

        # Verify get_response was called
        assert call_count[0] == 1

        # Verify context is cleared after response
        assert context.request_id.get() is None
