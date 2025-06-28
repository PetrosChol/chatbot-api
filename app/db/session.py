import logging
from typing import AsyncGenerator
from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yields a session using factory from app.state."""
    session_factory = getattr(request.app.state, "db_session_factory", None)
    if session_factory is None:
        logger.error("Database session factory not found in app.state.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not configured correctly.",
        )

    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            # Log with exc_info=True to get the full traceback for unexpected errors.
            # The error 'e' itself might contain sensitive data if it's a complex ORM error
            # that stringifies parts of a query with parameters.
            # However, for a general session rollback, exc_info=True is standard.
            logger.error(
                f"Session rollback due to error: {type(e).__name__}", exc_info=True
            )
            await session.rollback()
            raise
