import warnings
import pytest
from app.agent.response_generator import get_response_with_db_info_grounding
from app.agent.schemas import FinalResponseSchema

# This module contains tests for the AI response generation logic,
# specifically `get_response_with_db_info_grounding`. It ensures the function
# behaves as expected both in success and failure scenarios when interacting
# with the underlying AI (Instructor) client.

# Filter out specific DeprecationWarnings from google._upb.
# These warnings are related to internal Python C extension types and
# are not directly actionable for application code, so they are suppressed
# to keep test output clean.
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
    A mock class simulating the `instructor` client.
    It allows pre-defining a response or configuring it to raise an exception,
    mimicking the `chat.completions.create` method.
    """
    def __init__(self, response=None, raise_exc=False):
        self._response = response or FinalResponseSchema(
            reasoning="ok", response_to_user="Hello"
        )
        self._raise = raise_exc

        class Completions:
            async def create(inner_self, messages, response_model):
                if self._raise:
                    raise Exception("Simulated client failure")
                return self._response

        self.chat = type("Chat", (), {"completions": Completions()})


@pytest.mark.asyncio
async def test_response_generator_success(monkeypatch):
    """
    Tests the successful path of `get_response_with_db_info_grounding`.
    It ensures the function correctly processes a dummy AI response.
    """
    # Define a specific dummy response for the test.
    dummy_response = FinalResponseSchema(reasoning="test", response_to_user="Test")
    # Patch `get_instructor_client` to return our `DummyClient` configured
    # with the success response.
    monkeypatch.setattr(
        "app.agent.response_generator.get_instructor_client",
        lambda: DummyClient(response=dummy_response),
    )

    # Call the function under test with sample data.
    history = [{"type": "user", "message": "hi"}]
    tool_results = {"tool": "result"}
    result = await get_response_with_db_info_grounding("hello", history, tool_results)

    # Assert the returned object is of the expected type and contains the dummy data.
    assert isinstance(result, FinalResponseSchema)
    assert result.reasoning == "test"
    assert result.response_to_user == "Test"


@pytest.mark.asyncio
async def test_response_generator_exception(monkeypatch):
    """
    Tests the error handling of `get_response_with_db_info_grounding`
    when the underlying AI client encounters an exception.
    Ensures a graceful fallback response is generated.
    """
    # Patch `get_instructor_client` to return our `DummyClient` configured
    # to raise an exception during the `create` call.
    monkeypatch.setattr(
        "app.agent.response_generator.get_instructor_client",
        lambda: DummyClient(raise_exc=True),
    )

    # Call the function under test with sample data.
    history = [{"type": "user", "message": "hi"}]
    tool_results = {"tool": "result"}
    result = await get_response_with_db_info_grounding("hello", history, tool_results)

    # Assert the returned object is a `FinalResponseSchema` and its content
    # reflects the error state.
    assert isinstance(result, FinalResponseSchema)
    assert "Failed to synthesize" in result.reasoning
    assert "encountered an issue" in result.response_to_user