import uuid
from unittest.mock import patch, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Scope

from app.middleware.request_id import RequestIdMiddleware


# This module contains unit tests for the `RequestIdMiddleware`.
# It verifies that the middleware correctly handles `X-Request-ID` headers,
# generates new IDs when needed, sets them in the request state and context,
# and ensures proper cleanup, even in the event of exceptions.


# --- Mocks and Test Setup ---


async def mock_call_next(request: Request) -> Response:
    """
    A mock application endpoint that simulates a successful request.
    It captures the `request_id` from the request state, which the middleware sets.
    """
    request.state.request_id_in_context_during_call = request.state.request_id
    return Response("OK", status_code=200)


async def mock_call_next_raises_exception(request: Request) -> Response:
    """
    A mock application endpoint that simulates an exception during request processing.
    It also captures the `request_id` from the request state before raising.
    """
    request.state.request_id_in_context_during_call = request.state.request_id
    raise ValueError("Something went wrong downstream")


@pytest.fixture
def mock_scope() -> Scope:
    """Provides a basic ASGI scope dictionary, representing an incoming HTTP request."""
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "server": ("127.0.0.1", 8000),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
        "method": "GET",
        "root_path": "",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
    }


@pytest.fixture
def middleware() -> RequestIdMiddleware:
    """Fixture to create an instance of the `RequestIdMiddleware` for testing."""
    # A dummy ASGI app is provided as the 'next' handler.
    dummy_app: ASGIApp = lambda scope, receive, send: None
    return RequestIdMiddleware(app=dummy_app)


# --- Test Cases ---


@pytest.mark.asyncio
@patch("uuid.uuid4")
async def test_generates_request_id_if_none_provided(
    mock_uuid4: MagicMock, middleware: RequestIdMiddleware, mock_scope: Scope
):
    """
    Verifies that the middleware generates a new UUID for `X-Request-ID`
    when no header is provided in the incoming request.
    It asserts the ID is set in the request state, context variable, and response header.
    """
    # Define a predictable UUID for consistent test results.
    test_hex = "12345678123456781234567812345678"
    generated_uuid_obj = uuid.UUID(hex=test_hex)
    expected_request_id = str(generated_uuid_obj)
    mock_uuid4.return_value = generated_uuid_obj

    # Configure the request without an `X-Request-ID` header.
    mock_scope["headers"] = []
    request = Request(mock_scope)

    # Patch the `request_id_var` to observe its interactions with the context variable.
    with patch("app.middleware.request_id.request_id_var") as mock_request_id_var:
        mock_request_id_var.set = MagicMock(return_value="dummy_token")
        mock_request_id_var.reset = MagicMock()
        mock_request_id_var.get = MagicMock(return_value=expected_request_id)

        # Dispatch the request through the middleware.
        response = await middleware.dispatch(request, mock_call_next)

        # Assertions for generation and setting.
        mock_uuid4.assert_called_once()
        mock_request_id_var.set.assert_called_once_with(expected_request_id)
        assert request.state.request_id_in_context_during_call == expected_request_id
        mock_request_id_var.reset.assert_called_once_with("dummy_token")
        assert request.state.request_id == expected_request_id
        assert response.headers.get("X-Request-ID") == expected_request_id
        assert response.status_code == 200
        assert response.body == b"OK"


@pytest.mark.asyncio
@patch("uuid.uuid4")
async def test_uses_existing_request_id_if_provided(
    mock_uuid4: MagicMock, middleware: RequestIdMiddleware, mock_scope: Scope
):
    """
    Verifies that the middleware correctly uses an existing `X-Request-ID` header
    from the incoming request instead of generating a new one.
    It also checks the context variable, request state, and response header.
    """
    # Define an existing request ID.
    existing_request_id = "existing-test-id-123"
    # Configure the request with an `X-Request-ID` header.
    mock_scope["headers"] = [(b"x-request-id", existing_request_id.encode())]
    request = Request(mock_scope)

    # Patch the `request_id_var` to observe its interactions.
    with patch("app.middleware.request_id.request_id_var") as mock_request_id_var:
        mock_request_id_var.set = MagicMock(return_value="dummy_token")
        mock_request_id_var.reset = MagicMock()
        mock_request_id_var.get = MagicMock(return_value=existing_request_id)

        # Dispatch the request through the middleware.
        response = await middleware.dispatch(request, mock_call_next)

        # Assertions for using the existing ID.
        mock_uuid4.assert_not_called() # No new UUID should be generated.
        mock_request_id_var.set.assert_called_once_with(existing_request_id)
        assert request.state.request_id_in_context_during_call == existing_request_id
        mock_request_id_var.reset.assert_called_once_with("dummy_token")
        assert request.state.request_id == existing_request_id
        assert response.headers.get("X-Request-ID") == existing_request_id
        assert response.status_code == 200
        assert response.body == b"OK"


@pytest.mark.asyncio
@patch("uuid.uuid4")
async def test_context_var_reset_on_exception(
    mock_uuid4: MagicMock, middleware: RequestIdMiddleware, mock_scope: Scope
):
    """
    Verifies that the `request_id` context variable is correctly reset
    even when the downstream application raises an exception.
    """
    # Define a predictable UUID for generation.
    test_hex = "abcdef9876543210abcdef9876543210"
    generated_uuid_obj = uuid.UUID(hex=test_hex)
    expected_request_id = str(generated_uuid_obj)
    mock_uuid4.return_value = generated_uuid_obj

    # Configure the request without an `X-Request-ID` header.
    mock_scope["headers"] = []
    request = Request(mock_scope)

    # Patch the `request_id_var` to observe its interactions.
    with patch("app.middleware.request_id.request_id_var") as mock_request_id_var:
        mock_request_id_var.set = MagicMock(return_value="dummy_token")
        mock_request_id_var.reset = MagicMock()
        mock_request_id_var.get = MagicMock(return_value=expected_request_id)

        # Expect the exception from `mock_call_next_raises_exception` to propagate.
        with pytest.raises(ValueError, match="Something went wrong downstream"):
            await middleware.dispatch(request, mock_call_next_raises_exception)

        # Assertions for context variable handling during an exception.
        mock_request_id_var.set.assert_called_once_with(expected_request_id)
        assert request.state.request_id_in_context_during_call == expected_request_id
        # Crucially, `reset` must be called to clean up the context variable.
        mock_request_id_var.reset.assert_called_once_with("dummy_token")
        assert request.state.request_id == expected_request_id