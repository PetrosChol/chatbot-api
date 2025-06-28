from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
import logging


logger = logging.getLogger(__name__)


def create_db_session_factory(
    engine: AsyncEngine | None,
) -> async_sessionmaker[AsyncSession] | None:
    """Creates the SQLAlchemy async session factory."""
    if engine is None:
        logger.warning("No DB engine provided. Cannot create session factory.")
        return None
    logger.info("Creating database session factory.")
    try:
        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        return session_factory
    except Exception as e:
        logger.error(f"Failed to create session factory: {e}", exc_info=True)
        return None
