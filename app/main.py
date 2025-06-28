import logging
import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi_limiter import FastAPILimiter
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from app.core.config import settings
from app.db.engine import create_db_engine
from app.db.session_factory import create_db_session_factory
from app.memory.setup_client import setup_redis_client
from app.memory.shutdown_client import shutdown_redis_client
from app.routers import chat as chat_router
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.core.logging_config import setup_logging

# --- Apply Logging Configuration ---
setup_logging(settings)

# Get the logger *after* configuration is applied
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application lifespan events for resource setup and teardown.
    - Creates DB Engine and Session Factory, stores factory on app.state.
    - Creates Redis Client, stores client on app.state.
    - Cleans up resources on shutdown.
    """
    logger.info("Lifespan startup sequence initiated...")

    # === Database Setup ===
    db_engine = create_db_engine()
    db_session_factory = create_db_session_factory(db_engine)
    # Store necessary DB objects on app.state
    app.state.db_session_factory = db_session_factory
    app.state.db_engine = db_engine

    # === Redis Setup ===
    # Call the async setup function for Redis
    redis_client = await setup_redis_client()
    # Store the Redis client instance on app.state
    app.state.redis_client = redis_client

    # === Rate Limiter Setup (AFTER Redis setup) ===
    if redis_client:
        try:
            await FastAPILimiter.init(redis_client)
            logger.info("FastAPI Limiter initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize FastAPI Limiter: {e}", exc_info=True)
            # Decide if this is fatal or just means limiting is disabled
    else:
        logger.warning(
            "Redis client not available. Skipping FastAPI Limiter initialization."
        )

    # Optional: Add checks here to ensure critical resources initialized
    if not app.state.db_session_factory:
        logger.critical("FATAL: Database session factory failed to initialize.")
    if not app.state.redis_client:
        logger.warning("Redis client failed to initialize. Proceeding without Redis.")

    logger.info("Application resource initialization complete.")
    # --- Application is ready to yield control ---
    yield
    # --- Application received shutdown signal ---
    logger.info("Lifespan shutdown sequence initiated...")

    # === Redis Shutdown ===
    # Retrieve Redis client from state to close it
    redis_client_to_close = getattr(app.state, "redis_client", None)
    await shutdown_redis_client(redis_client_to_close)

    # === Database Shutdown ===
    # Retrieve DB engine from state to dispose it
    engine_to_dispose = getattr(app.state, "db_engine", None)
    if engine_to_dispose:
        logger.info("Disposing database engine...")
        await engine_to_dispose.dispose()
        logger.info("DB Engine disposed.")
    else:
        logger.info("No database engine found in state to dispose.")

    logger.info("Application shutdown complete.")


app = FastAPI(title="Alex Chatbot API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add RequestIdMiddleware *before* SecurityHeadersMiddleware if you want security headers logged with ID
# Add it *after* CORS if CORS needs to process first. Usually order: CORS -> RequestID -> Security -> Others
app.add_middleware(RequestIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_root(request: Request):
    """Serves the main HTML page for the chat UI."""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        logger.error("static/index.html not found")
        raise HTTPException(status_code=404, detail="Index page not found.")
    except Exception as e:
        logger.error(f"Error reading static/index.html: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not load index page.")


@app.get("/health", tags=["Meta"], status_code=status.HTTP_200_OK)
async def health_check(request: Request):
    """
    Performs health checks on the application and its critical dependencies (DB, Redis).
    Returns 200 OK if all checks pass, 503 Service Unavailable otherwise.
    """
    db_status = "checking"
    redis_status = "checking"
    db_error = None
    redis_error = None
    is_healthy = True
    timeout = settings.HEALTH_CHECK_TIMEOUT_S

    # --- Check Database Connectivity ---
    db_session_factory = getattr(request.app.state, "db_session_factory", None)
    if db_session_factory:
        try:

            async def db_check_task():
                async with db_session_factory() as session:
                    await session.execute(select(1))
                return "ok"

            db_status = await asyncio.wait_for(db_check_task(), timeout=timeout)
            logger.debug("Database health check successful.")
        except asyncio.TimeoutError:
            db_status = "unhealthy"
            db_error = f"Database check timed out after {timeout}s"
            logger.error(db_error)
            is_healthy = False
        except SQLAlchemyError as e:
            db_status = "unhealthy"
            db_error = f"Database error: {e}"
            logger.error(db_error)
            is_healthy = False
        except Exception as e:
            db_status = "unhealthy"
            db_error = f"Unexpected error during DB check: {e}"
            logger.exception(
                "Unexpected error during database health check."
            )  # Log stack trace
            is_healthy = False
    else:
        db_status = "unavailable"
        db_error = "Database session factory not configured"
        logger.warning(db_error)

    # --- Check Redis Connectivity ---
    redis_client: redis.Redis | None = getattr(request.app.state, "redis_client", None)
    if redis_client:
        try:

            async def redis_check_task():
                if await redis_client.ping():
                    return "ok"
                else:
                    # Should not happen with aioredis ping, it raises on failure
                    return "unhealthy"

            redis_status = await asyncio.wait_for(redis_check_task(), timeout=timeout)
            logger.debug("Redis health check successful.")
        except asyncio.TimeoutError:
            redis_status = "unhealthy"
            redis_error = f"Redis check timed out after {timeout}s"
            logger.error(redis_error)
            is_healthy = False
        except redis.RedisError as e:
            redis_status = "unhealthy"
            redis_error = f"Redis error: {e}"
            logger.error(redis_error)
            is_healthy = False
        except Exception as e:
            redis_status = "unhealthy"
            redis_error = f"Unexpected error during Redis check: {e}"
            logger.exception(
                "Unexpected error during Redis health check."
            )
            is_healthy = False
    else:
        redis_status = "unavailable"
        redis_error = "Redis client not configured"
        logger.warning(redis_error)

    # --- Determine Overall Health and Response ---
    response_payload = {
        "status": "healthy" if is_healthy else "unhealthy",
        "dependencies": {
            "database": {"status": db_status, "error": db_error},
            "redis": {"status": redis_status, "error": redis_error},
        },
    }

    if not is_healthy:
        # Raise 503 if any critical dependency check failed
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response_payload,
        )

    # Return 200 OK with details if all checks passed
    return response_payload


app.include_router(
    chat_router.router, prefix=settings.API_V1_STR, tags=["Chat"]
)

logger.info("FastAPI app instance created.")
