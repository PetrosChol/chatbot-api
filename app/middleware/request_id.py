import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging_filters import request_id_var


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate or retrieve a unique request ID (X-Request-ID),
    set it in a context variable for logging, and add it to the response header.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Set the request ID in the context variable for this request's context
        request_id_token = request_id_var.set(request_id)

        # Optionally, still store in state if needed elsewhere directly via request object
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            # Add the request ID to the response headers
            response.headers["X-Request-ID"] = request_id
        finally:
            # Reset the context variable after the request is done
            request_id_var.reset(request_id_token)

        return response
