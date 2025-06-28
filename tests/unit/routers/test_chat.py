import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
import uuid

from app.routers import chat
from app.routers.chat import ChatRequest, ChatResponse


@pytest.fixture
def mock_session():
    """Fixture for mocking SQLAlchemy AsyncSession"""
    return AsyncMock()


@pytest.fixture
def mock_redis():
    """Fixture for mocking Redis client"""
    return AsyncMock()


@pytest.fixture
def chat_request():
    """Fixture for valid chat request"""
    return ChatRequest(user_message="Hello, how are you?", session_id=str(uuid.uuid4()))


@pytest.fixture
def new_chat_request():
    """Fixture for new chat request without session ID"""
    return ChatRequest(user_message="Hello, I'm new here")


class TestChatRouter:

    @pytest.mark.asyncio
    async def test_handle_chat_message_success(
        self, mock_session, mock_redis, chat_request
    ):
        """Test successful chat message handling with existing session"""
        # Mock the process_chat_message function
        expected_reply = "I'm doing well, thank you for asking!"
        session_id = chat_request.session_id

        with patch(
            "app.routers.chat.process_chat_message",
            new=AsyncMock(return_value=(expected_reply, session_id)),
        ) as mock_process:
            response = await chat.handle_chat_message(
                request_body=chat_request, db=mock_session, redis_client=mock_redis
            )

            # Assert process_chat_message was called with correct arguments
            mock_process.assert_called_once_with(
                user_message=chat_request.user_message,
                session_id=chat_request.session_id,
                redis_client=mock_redis,
                db=mock_session,
            )

            # Assert the response matches expected values
            assert isinstance(response, ChatResponse)
            assert response.bot_reply == expected_reply
            assert response.session_id == session_id

    @pytest.mark.asyncio
    async def test_handle_new_chat_session(
        self, mock_session, mock_redis, new_chat_request
    ):
        """Test handling a new chat session (no previous session ID)"""
        expected_reply = "Hello! How can I help you today?"
        new_session_id = str(uuid.uuid4())

        with patch(
            "app.routers.chat.process_chat_message",
            new=AsyncMock(return_value=(expected_reply, new_session_id)),
        ) as mock_process:
            response = await chat.handle_chat_message(
                request_body=new_chat_request, db=mock_session, redis_client=mock_redis
            )

            # Assert process_chat_message was called with None session_id
            mock_process.assert_called_once_with(
                user_message=new_chat_request.user_message,
                session_id=None,
                redis_client=mock_redis,
                db=mock_session,
            )

            # Assert the response contains the new session ID
            assert isinstance(response, ChatResponse)
            assert response.bot_reply == expected_reply
            assert response.session_id == new_session_id

    @pytest.mark.asyncio
    async def test_handle_chat_http_exception(
        self, mock_session, mock_redis, chat_request
    ):
        """Test handling of HTTP exceptions from the chat service"""
        # Create an HTTP exception to be raised by the service
        http_error = HTTPException(
            status_code=503, detail="Service temporarily unavailable"
        )

        with patch(
            "app.routers.chat.process_chat_message",
            new=AsyncMock(side_effect=http_error),
        ):
            # The HTTP exception should be propagated
            with pytest.raises(HTTPException) as exc_info:
                await chat.handle_chat_message(
                    request_body=chat_request, db=mock_session, redis_client=mock_redis
                )

            # Assert the exception is the same one raised by the service
            assert exc_info.value.status_code == 503
            assert exc_info.value.detail == "Service temporarily unavailable"

    @pytest.mark.asyncio
    async def test_handle_chat_generic_exception(
        self, mock_session, mock_redis, chat_request
    ):
        """Test handling of generic exceptions from the chat service"""
        # Create a generic exception to be raised by the service
        generic_error = ValueError("Invalid input format")

        with patch(
            "app.routers.chat.process_chat_message",
            new=AsyncMock(side_effect=generic_error),
        ):
            # Should convert to HTTP 500 exception
            with pytest.raises(HTTPException) as exc_info:
                await chat.handle_chat_message(
                    request_body=chat_request, db=mock_session, redis_client=mock_redis
                )

            # Assert the exception is converted to a 500 with appropriate message
            assert exc_info.value.status_code == 500
            assert "internal error occurred" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_chat_request_validation(self):
        """Test ChatRequest model validation"""
        # Valid request
        valid_request = ChatRequest(user_message="Hello")
        assert valid_request.user_message == "Hello"
        assert valid_request.session_id is None

        # With session ID
        request_with_session = ChatRequest(
            user_message="Hello again", session_id="test-session-123"
        )
        assert request_with_session.user_message == "Hello again"
        assert request_with_session.session_id == "test-session-123"

    @pytest.mark.asyncio
    async def test_chat_response_validation(self):
        """Test ChatResponse model validation"""
        response = ChatResponse(
            bot_reply="Hello, how can I help you?", session_id="test-session-456"
        )
        assert response.bot_reply == "Hello, how can I help you?"
        assert response.session_id == "test-session-456"

    @pytest.mark.asyncio
    async def test_rate_limiter_dependency(self):
        """Test that the rate limiter dependency is properly applied"""
        # This is a bit harder to test directly, but we can verify the router has the dependency
        route = next(r for r in chat.router.routes if r.path == "/chat")
        # Check that RateLimiter is in the dependencies
        has_rate_limiter = any(
            "RateLimiter" in str(dep.dependency) for dep in route.dependencies
        )
        assert has_rate_limiter
