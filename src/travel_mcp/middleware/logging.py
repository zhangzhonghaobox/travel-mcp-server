"""Logging middleware for structured logging."""

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from travel_mcp.config import get_config


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""

    def __init__(self, app) -> None:
        """Initialize logging middleware."""
        super().__init__(app)
        self.config = get_config()
        self.logger = structlog.get_logger("http")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and log details."""
        request_id = request.headers.get("x-request-id", str(id(request)))
        client_ip = request.client.host if request.client else "unknown"

        # Log request
        self.logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
        )

        start_time = 0  # Will be set when we have access to response

        try:
            response = await call_next(request)

            # Log response
            self.logger.info(
                "request_completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            self.logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
            )
            raise
