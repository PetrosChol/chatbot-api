import pytest
from unittest.mock import MagicMock
import instructor

# The module under test, which contains the client instance and its getter.
from app.agent import client as agent_client_module


# --- Tests for the client retrieval function ---


def test_get_instructor_client_success(monkeypatch):
    """
    Verifies that `get_instructor_client` returns the correctly initialized
    Instructor client when available.
    """
    # Create a mock Instructor client instance.
    mock_instructor_client = MagicMock(spec=instructor.Instructor)
    # Simulate a successfully initialized module-level client.
    monkeypatch.setattr(agent_client_module, "client", mock_instructor_client)

    # Attempt to retrieve the client.
    retrieved_client = agent_client_module.get_instructor_client()
    # Assert that the retrieved client is indeed our mock instance.
    assert retrieved_client is mock_instructor_client


def test_get_instructor_client_not_initialized(monkeypatch):
    """
    Verifies that `get_instructor_client` raises a RuntimeError
    when the Instructor client has not been successfully initialized.
    """
    # Force the module-level client to be None, simulating an initialization failure.
    monkeypatch.setattr(agent_client_module, "client", None)

    # Expect a RuntimeError when attempting to retrieve the client.
    with pytest.raises(RuntimeError) as exc_info:
        agent_client_module.get_instructor_client()

    # Confirm the error message indicates the client is not initialized.
    assert "Instructor client is not initialized" in str(exc_info.value)


# --- Rationale for omitted initialization tests ---
# Direct testing of module-level initialization logic (which runs on import)
# can be brittle and difficult to manage reliably with standard mocking techniques
# like `importlib.reload`.
#
# Our current test suite adequately covers the critical paths by:
# 1. Directly asserting the functionality of `get_instructor_client`
#    when the client is expected to be available.
# 2. Explicitly testing the error handling of `get_instructor_client`
#    when the client is `None`, which is the outcome of a failed initialization.
# This approach focuses on the observable behavior and reliability of the
# `get_instructor_client` function, rather than the intricate details of
# module import side-effects.