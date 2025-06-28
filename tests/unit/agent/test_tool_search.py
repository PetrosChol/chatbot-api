import warnings
import pytest
from app.agent.tool_search import search_for_tools
from app.agent.schemas import ResponseSchema

# This module contains tests for the `search_for_tools` function,
# which is responsible for analyzing user queries and determining if tools are needed.
# It uses a mock Instructor client to simulate AI responses.

# Filter out specific DeprecationWarnings originating from Google's internal protobuf
# messages. These are not actionable issues for our application code and are
# suppressed to keep test logs clean.
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="Type google._upb._message.MessageMapContainer uses PyType_Spec with a metaclass that has custom tp_new. This is deprecated and will no longer be allowed in Python 3.14.",
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="Type google._upb._message.ScalarMapContainer uses PyType_Spec with a metaclass that has custom tp_new. This is deprecated and will no longer be allowed in Python 3.14.",
)


class DummyClient:
    """
    A mock class simulating the behavior of the `instructor` client.
    It's designed to return a predefined `ResponseSchema` or raise an exception,
    mimicking the `chat.completions.create` method for testing purposes.
    """
    def __init__(self, response=None, raise_exc=False):
        self._response = response or ResponseSchema(
            reasoning="ok", direct_response="Hello"
        )
        self._raise = raise_exc

        class Completions:
            async def create(inner_self, messages, response_model):
                if self._raise:
                    raise Exception("Simulated client failure")
                return self._response

        self.chat = type("Chat", (), {"completions": Completions()})


@pytest.mark.asyncio
async def test_search_for_tools_success(monkeypatch):
    """
    Verifies that `search_for_tools` correctly processes a successful AI response.
    It ensures the function returns the expected `ResponseSchema` without errors.
    """
    # Define a dummy response that the mock client will return.
    dummy_response = ResponseSchema(reasoning="test", direct_response="Test")
    # Patch `get_instructor_client` to return our `DummyClient` configured for success.
    monkeypatch.setattr(
        "app.agent.tool_search.get_instructor_client",
        lambda: DummyClient(response=dummy_response),
    )

    # Call the function under test with sample input.
    history = [{"type": "user", "message": "hi"}]
    result = await search_for_tools("hello", history)

    # Assert the type and content of the returned result.
    assert isinstance(result, ResponseSchema)
    assert result.reasoning == "test"
    assert result.direct_response == "Test"


@pytest.mark.asyncio
async def test_search_for_tools_exception(monkeypatch):
    """
    Tests `search_for_tools` error handling when the underlying AI client fails.
    It ensures a graceful fallback response is provided to the user.
    """
    # Patch `get_instructor_client` to return a `DummyClient` that raises an exception.
    monkeypatch.setattr(
        "app.agent.tool_search.get_instructor_client",
        lambda: DummyClient(raise_exc=True),
    )

    # Call the function under test with sample input.
    history = [{"type": "user", "message": "hi"}]
    result = await search_for_tools("hello", history)

    # Assert the type and content of the error-handling response.
    assert isinstance(result, ResponseSchema)
    assert "Failed to analyze" in result.reasoning
    assert "Could you please rephrase" in result.direct_response