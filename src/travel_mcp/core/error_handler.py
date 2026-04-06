"""Error handling module for Travel MCP Server."""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Standard error codes for the Travel MCP Server."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


ERROR_HTTP_STATUS = {
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.RESOURCE_NOT_FOUND: 404,
    ErrorCode.PERMISSION_DENIED: 403,
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.TIMEOUT_ERROR: 504,
}


class ErrorResponse(BaseModel):
    """Standard error response format."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump(exclude_none=True)


class TravelMCPError(Exception):
    """Base exception for Travel MCP Server."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize error."""
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)

    def to_response(self) -> ErrorResponse:
        """Convert to error response."""
        return ErrorResponse(
            code=self.code.value,
            message=self.message,
            details=self.details,
        )


class ValidationError(TravelMCPError):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize validation error."""
        super().__init__(ErrorCode.VALIDATION_ERROR, message, details)


class ResourceNotFoundError(TravelMCPError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize resource not found error."""
        super().__init__(ErrorCode.RESOURCE_NOT_FOUND, message, details)


class PermissionDeniedError(TravelMCPError):
    """Raised when permission is denied."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize permission denied error."""
        super().__init__(ErrorCode.PERMISSION_DENIED, message, details)


class RateLimitExceededError(TravelMCPError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize rate limit exceeded error."""
        super().__init__(ErrorCode.RATE_LIMIT_EXCEEDED, message, details)


class ServiceUnavailableError(TravelMCPError):
    """Raised when a service is unavailable."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize service unavailable error."""
        super().__init__(ErrorCode.SERVICE_UNAVAILABLE, message, details)


class TimeoutError(TravelMCPError):
    """Raised when a request times out."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize timeout error."""
        super().__init__(ErrorCode.TIMEOUT_ERROR, message, details)


def get_http_status(error_code: ErrorCode) -> int:
    """Get HTTP status code for error code."""
    return ERROR_HTTP_STATUS.get(error_code, 500)
