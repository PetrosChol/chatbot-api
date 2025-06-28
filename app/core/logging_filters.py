import logging
from contextvars import ContextVar

# Define a context variable for the request ID with a default value
request_id_var: ContextVar[str | None] = ContextVar("request_id", default="N/A")


class RequestIdFilter(logging.Filter):
    """
    Logging filter that injects the request ID from a context variable into the log record.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # Get the request ID from the context variable, defaulting to "N/A" if None
        req_id = request_id_var.get()
        record.request_id = req_id if req_id is not None else "N/A"
        return True


class EndpointFilter(logging.Filter):
    """
    Filter out log records for specific endpoints (e.g., /health).
    Checks the request path often found in args[1] for uvicorn access logs.
    """

    def __init__(self, path: str):
        super().__init__()
        self._path = path

    def filter(self, record: logging.LogRecord) -> bool:
        # Primarily check based on uvicorn access log format
        request_args = getattr(record, "args", None)
        if (
            isinstance(request_args, tuple)
            and len(request_args) >= 2
            and isinstance(request_args[1], str)
            and self._path in request_args[1]
        ):
            return False  # Filter out if path found in the request line arg

        # Fallback: Check the formatted message for the path.
        try:
            if self._path in record.getMessage():
                return False
        except (TypeError, ValueError):
            # If getMessage() fails due to mismatched args/msg,
            # assume it's not the log we want to filter based on path.
            pass

        return True