"""Audit logging module for Travel MCP Server."""

import json
import structlog
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from travel_mcp.config import get_config

logger = structlog.get_logger("audit")


class AuditLogger:
    """Handles audit logging for security and compliance."""

    def __init__(self) -> None:
        """Initialize audit logger."""
        self.config = get_config()
        self._log = logger

    def log_tool_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        user_id: Optional[str] = None,
    ) -> None:
        """Log successful tool execution."""
        self._log.info(
            "tool_execution",
            event_type="TOOL_EXECUTION",
            tool_name=tool_name,
            arguments=self._sanitize_arguments(arguments),
            result_summary=self._summarize_result(result),
            user_id=user_id or "anonymous",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_denied_access(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        reason: str = "permission_denied",
        user_id: Optional[str] = None,
    ) -> None:
        """Log denied access attempt."""
        self._log.warning(
            "access_denied",
            event_type="ACCESS_DENIED",
            tool_name=tool_name,
            arguments=self._sanitize_arguments(arguments),
            reason=reason,
            user_id=user_id or "anonymous",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_error(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        error: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Log tool execution error."""
        self._log.error(
            "tool_error",
            event_type="TOOL_ERROR",
            tool_name=tool_name,
            arguments=self._sanitize_arguments(arguments),
            error=error,
            user_id=user_id or "anonymous",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_authentication(
        self,
        event: str,
        user_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log authentication events."""
        self._log.info(
            "authentication",
            event_type="AUTHENTICATION",
            event=event,
            user_id=user_id or "anonymous",
            success=success,
            details=details or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def log_rate_limit(
        self,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> None:
        """Log rate limit events."""
        self._log.warning(
            "rate_limit_exceeded",
            event_type="RATE_LIMIT_EXCEEDED",
            user_id=user_id or "anonymous",
            limit=limit,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from arguments before logging."""
        sensitive_keys = {"password", "api_key", "secret", "token", "credential"}
        sanitized = {}
        for key, value in arguments.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_arguments(value)
            elif isinstance(value, str) and len(value) > 100:
                sanitized[key] = value[:100] + "...[truncated]"
            else:
                sanitized[key] = value
        return sanitized

    def _summarize_result(self, result: Any) -> str:
        """Create a summary of the result for logging."""
        if result is None:
            return "None"
        if isinstance(result, dict):
            if "error" in result:
                return f"Error: {result.get('error')}"
            keys = list(result.keys())[:5]
            return f"Dict with keys: {keys}"
        if isinstance(result, list):
            return f"List with {len(result)} items"
        result_str = str(result)
        if len(result_str) > 100:
            return result_str[:100] + "...[truncated]"
        return result_str
