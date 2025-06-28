import logging
import uuid
from contextlib import contextmanager

import pytest

from app.core.logging_filters import (
    EndpointFilter,
    RequestIdFilter,
    request_id_var,
)


# --- Test Fixtures ---

@pytest.fixture
def log_record():
    """Provides a basic `logging.LogRecord` instance for testing filters."""
    return logging.LogRecord(
        name="testlogger",
        level=logging.INFO,
        pathname="/fake/path",
        lineno=123,
        msg="Test message",
        args=(),
        exc_info=None,
        func="test_func",
    )


@contextmanager
def set_request_id(req_id: str | None):
    """
    A context manager to temporarily set the `request_id_var` (ContextVar)
    for testing `RequestIdFilter` behavior.
    """
    token = request_id_var.set(req_id)
    try:
        yield
    finally:
        request_id_var.reset(token)


# --- Tests for RequestIdFilter ---

def test_request_id_filter_adds_id_when_set(log_record):
    """
    Verifies that `RequestIdFilter` correctly attaches a `request_id`
    to the log record when `request_id_var` is set in the current context.
    """
    filter_instance = RequestIdFilter()
    test_uuid = str(uuid.uuid4())

    with set_request_id(test_uuid):
        result = filter_instance.filter(log_record)

    assert result is True
    assert hasattr(log_record, "request_id")
    assert log_record.request_id == test_uuid


def test_request_id_filter_adds_default_when_not_set(log_record):
    """
    Verifies that `RequestIdFilter` assigns a default "N/A" `request_id`
    to the log record when `request_id_var` is explicitly `None`.
    """
    filter_instance = RequestIdFilter()

    with set_request_id(None):
        result = filter_instance.filter(log_record)

    assert result is True
    assert hasattr(log_record, "request_id")
    assert log_record.request_id == "N/A"


def test_request_id_filter_adds_default_when_context_missing(log_record):
    """
    Verifies that `RequestIdFilter` assigns a default "N/A" `request_id`
    when `request_id_var` has not been set at all in the current context.
    """
    filter_instance = RequestIdFilter()
    # No context manager used here, simulating a truly unset state.
    result = filter_instance.filter(log_record)

    assert result is True
    assert hasattr(log_record, "request_id")
    assert log_record.request_id == "N/A"


# --- Tests for EndpointFilter ---

@pytest.fixture
def health_check_record():
    """Provides a `LogRecord` simulating a uvicorn access log for the `/health` endpoint."""
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="/fake/path",
        lineno=123,
        msg='%s - "%s" %s',
        args=("127.0.0.1:12345", "GET /health HTTP/1.1", 200),
        exc_info=None,
        func="test_func",
    )


@pytest.fixture
def other_endpoint_record():
    """Provides a `LogRecord` simulating a uvicorn access log for a different API endpoint."""
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="/fake/path",
        lineno=123,
        msg='%s - "%s" %s',
        args=("192.168.1.10:54321", "POST /api/data HTTP/1.1", 201),
        exc_info=None,
        func="test_func",
    )


@pytest.fixture
def non_access_log_record():
    """Provides a `LogRecord` that is not a uvicorn access log."""
    return logging.LogRecord(
        name="myapp.module",
        level=logging.WARNING,
        pathname="/app/module.py",
        lineno=50,
        msg="Something went wrong with args %s and %s",
        args=("value1", 123),
        exc_info=None,
        func="process_data",
    )


def test_endpoint_filter_blocks_matching_path(health_check_record):
    """
    Verifies that `EndpointFilter` blocks (returns `False` for) `LogRecord`s
    whose message matches the specified filtering path.
    """
    filter_instance = EndpointFilter(path="/health")
    result = filter_instance.filter(health_check_record)
    assert result is False


def test_endpoint_filter_allows_non_matching_path(other_endpoint_record):
    """
    Verifies that `EndpointFilter` allows (returns `True` for) `LogRecord`s
    whose message does not match the specified filtering path.
    """
    filter_instance = EndpointFilter(path="/health")
    result = filter_instance.filter(other_endpoint_record)
    assert result is True


def test_endpoint_filter_allows_non_access_log_record(non_access_log_record):
    """
    Verifies that `EndpointFilter` allows `LogRecord`s that are not formatted
    as uvicorn access logs, regardless of content.
    """
    filter_instance = EndpointFilter(path="/health")
    result = filter_instance.filter(non_access_log_record)
    assert result is True


def test_endpoint_filter_allows_record_with_insufficient_args(log_record):
    """
    Verifies that `EndpointFilter` allows `LogRecord`s that do not have
    enough arguments to extract the endpoint path.
    """
    filter_instance = EndpointFilter(path="/health")
    log_record.args = ("only one arg",)
    result = filter_instance.filter(log_record)
    assert result is True


def test_endpoint_filter_allows_record_with_non_string_arg(log_record):
    """
    Verifies that `EndpointFilter` allows `LogRecord`s where the argument
    expected to contain the path is not a string.
    """
    filter_instance = EndpointFilter(path="/health")
    log_record.args = ("client_ip", 12345, 200)
    result = filter_instance.filter(log_record)
    assert result is True