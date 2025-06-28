import pytest
from unittest.mock import patch, AsyncMock
import uuid
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.schemas import ResponseSchema, FinalResponseSchema, OutagesArgs
from app.services import chat_service


# --- Test Fixtures ---

@pytest.fixture
def mock_redis():
    """
    Provides an asynchronous mock of the Redis client.
    Useful for simulating Redis operations without needing a real Redis instance.
    """
    return AsyncMock(spec=redis.Redis)


@pytest.fixture
def mock_db():
    """
    Provides an asynchronous mock of the SQLAlchemy AsyncSession.
    Essential for testing database interactions in isolation.
    """
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_memory_service():
    """
    Patches the `memory_service` module to control its behavior during tests.
    Sets default return values for chat history operations.
    """
    with patch("app.services.chat_service.memory_service", autospec=True) as mock_mem:
        mock_mem.get_chat_history = AsyncMock(return_value=[])
        mock_mem.add_chat_turn = AsyncMock()
        yield mock_mem


@pytest.fixture
def mock_tool_search():
    """
    Patches the `search_for_tools` function, which determines if a user query
    requires tool execution or a direct response.
    Defaults to returning a direct response.
    """
    with patch(
        "app.services.chat_service.search_for_tools", autospec=True
    ) as mock_search:
        mock_search.return_value = ResponseSchema(
            reasoning="Direct response appropriate",
            direct_response="Hello from mock search!",
        )
        yield mock_search


@pytest.fixture
def mock_tool_executor():
    """
    Patches the `execute_tools_sequentially` function, simulating the execution
    of AI-determined tools. Defaults to a generic successful tool result.
    """
    with patch(
        "app.services.chat_service.execute_tools_sequentially", autospec=True
    ) as mock_exec:
        mock_exec.return_value = {
            "tool1": {"result": "Mock tool result"}
        }
        yield mock_exec


@pytest.fixture
def mock_response_generator():
    """
    Patches the `get_response_with_db_info_grounding` function, which synthesizes
    the final user-facing response, potentially leveraging tool results.
    """
    with patch(
        "app.services.chat_service.get_response_with_db_info_grounding", autospec=True
    ) as mock_gen:
        mock_gen.return_value = FinalResponseSchema(
            reasoning="Synthesized response based on tool results",
            response_to_user="Here is the info you requested.",
        )
        yield mock_gen


@pytest.fixture
def mock_uuid():
    """
    Patches `uuid.uuid4` to ensure a predictable UUID is generated for new chat sessions.
    """
    with patch("app.services.chat_service.uuid.uuid4") as mock_uuid4:
        mock_uuid4.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
        yield mock_uuid4


# --- Test Cases for `process_chat_message` ---


@pytest.mark.asyncio
async def test_process_chat_message_new_session_direct_response(
    mock_redis,
    mock_db,
    mock_memory_service,
    mock_tool_search,
    mock_tool_executor,
    mock_response_generator,
    mock_uuid,
):
    """
    Tests the scenario where a new chat session is initiated, and the AI
    determines that a direct response is sufficient without needing any tools.
    Verifies session ID generation and correct function calls.
    """
    user_message = "Hi"
    session_id = None # Indicates a new session.
    expected_session_id = str(mock_uuid.return_value)
    expected_bot_reply = "Hello from mock search!"

    # Call the function under test.
    bot_reply, returned_session_id = await chat_service.process_chat_message(
        user_message, session_id, mock_redis, mock_db
    )

    # Assert the returned values.
    assert returned_session_id == expected_session_id
    assert bot_reply == expected_bot_reply

    # Verify interactions with mocked dependencies.
    mock_memory_service.get_chat_history.assert_awaited_once_with(
        session_id=expected_session_id, redis_client=mock_redis, limit=4
    )
    mock_tool_search.assert_awaited_once_with(
        user_message=user_message, history=[]
    )
    mock_tool_executor.assert_not_awaited()
    mock_response_generator.assert_not_awaited()
    mock_memory_service.add_chat_turn.assert_awaited_once_with(
        session_id=expected_session_id,
        user_message=user_message,
        bot_message=expected_bot_reply,
        redis_client=mock_redis,
    )


@pytest.mark.asyncio
async def test_process_chat_message_existing_session_with_tools(
    mock_redis,
    mock_db,
    mock_memory_service,
    mock_tool_search,
    mock_tool_executor,
    mock_response_generator,
):
    """
    Tests the scenario for an existing chat session where the AI
    determines that specific tools need to be executed to fulfill the user's request.
    Verifies the entire tool-use pipeline.
    """
    user_message = "Find outages in downtown"
    session_id = "existing-session-456"
    mock_history = [{"type": "user", "message": "Previous message"}]
    mock_tool_calls = [OutagesArgs(locations=["downtown"])]
    mock_tool_results = {"outages": ["Outage A", "Outage B"]}
    expected_bot_reply = "Here is the info you requested."

    # Configure mocks for this specific tool-use scenario.
    mock_memory_service.get_chat_history.return_value = mock_history
    mock_tool_search.return_value = ResponseSchema(
        reasoning="Outages tool needed", tools=mock_tool_calls
    )
    mock_tool_executor.return_value = mock_tool_results

    # Call the function under test.
    bot_reply, returned_session_id = await chat_service.process_chat_message(
        user_message, session_id, mock_redis, mock_db
    )

    # Assert the returned values.
    assert returned_session_id == session_id
    assert bot_reply == expected_bot_reply

    # Verify interactions with mocked dependencies, including tool execution steps.
    mock_memory_service.get_chat_history.assert_awaited_once_with(
        session_id=session_id, redis_client=mock_redis, limit=4
    )
    mock_tool_search.assert_awaited_once_with(
        user_message=user_message, history=mock_history
    )
    mock_tool_executor.assert_awaited_once_with(tool_calls=mock_tool_calls, db=mock_db)
    mock_response_generator.assert_awaited_once_with(
        user_message=user_message, history=mock_history, tool_results=mock_tool_results
    )
    mock_memory_service.add_chat_turn.assert_awaited_once_with(
        session_id=session_id,
        user_message=user_message,
        bot_message=expected_bot_reply,
        redis_client=mock_redis,
    )


@pytest.mark.asyncio
@patch("app.services.chat_service.logger")
async def test_process_chat_message_history_load_fails(
    mock_logger, mock_redis, mock_db, mock_memory_service, mock_tool_search
):
    """
    Tests the resilience of `process_chat_message` when loading chat history fails.
    Ensures that the process continues with an empty history and logs the error,
    still providing a response.
    """
    user_message = "Test message"
    session_id = "session-hist-fail"
    test_exception = redis.RedisError("Failed to load history")
    expected_bot_reply = "Hello from mock search!"

    # Simulate history load failure.
    mock_memory_service.get_chat_history.side_effect = test_exception

    # Call the function under test.
    bot_reply, returned_session_id = await chat_service.process_chat_message(
        user_message, session_id, mock_redis, mock_db
    )

    # Assert the returned values.
    assert returned_session_id == session_id
    assert bot_reply == expected_bot_reply

    # Verify interactions and error logging.
    mock_memory_service.get_chat_history.assert_awaited_once_with(
        session_id=session_id, redis_client=mock_redis, limit=4
    )
    mock_logger.error.assert_any_call(
        f"Failed to get chat history for session {session_id}: {test_exception}",
        exc_info=True,
    )
    mock_tool_search.assert_awaited_once_with(user_message=user_message, history=[])
    mock_memory_service.add_chat_turn.assert_awaited_once_with(
        session_id=session_id,
        user_message=user_message,
        bot_message=expected_bot_reply,
        redis_client=mock_redis,
    )


@pytest.mark.asyncio
@patch("app.services.chat_service.logger")
async def test_process_chat_message_history_save_fails(
    mock_logger, mock_redis, mock_db, mock_memory_service, mock_tool_search
):
    """
    Tests the resilience of `process_chat_message` when saving chat history fails.
    Ensures that the bot's reply is still returned to the user, and the error is logged.
    """
    user_message = "Another test"
    session_id = "session-save-fail"
    test_exception = redis.RedisError("Failed to save history")
    expected_bot_reply = "Hello from mock search!"

    # Simulate history save failure.
    mock_memory_service.add_chat_turn.side_effect = test_exception

    # Call the function under test.
    bot_reply, returned_session_id = await chat_service.process_chat_message(
        user_message, session_id, mock_redis, mock_db
    )

    # Assert the returned values.
    assert returned_session_id == session_id
    assert bot_reply == expected_bot_reply

    # Verify interactions and error logging.
    mock_memory_service.get_chat_history.assert_awaited_once_with(
        session_id=session_id, redis_client=mock_redis, limit=4
    )
    mock_tool_search.assert_awaited_once_with(user_message=user_message, history=[])
    mock_memory_service.add_chat_turn.assert_awaited_once_with(
        session_id=session_id,
        user_message=user_message,
        bot_message=expected_bot_reply,
        redis_client=mock_redis,
    )
    mock_logger.error.assert_any_call(
        f"Failed to add chat turn to history for session {session_id}: {test_exception}",
        exc_info=True,
    )