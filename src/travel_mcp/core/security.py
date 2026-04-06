"""Security validation module for Travel MCP Server."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Pattern

from travel_mcp.config import get_config


@dataclass
class SecurityValidationResult:
    """Result of security validation."""

    is_valid: bool
    error_message: Optional[str] = None


class SecurityValidator:
    """Validates requests for security concerns."""

    # Dangerous patterns for injection attacks
    SQL_INJECTION_PATTERNS: List[Pattern[str]] = [
        re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b)", re.IGNORECASE),
        re.compile(r"(--|;|/\*|\*/|@@|@)"),
        re.compile(r"'.*OR.*'.*=.*'"),
    ]

    # XSS patterns
    XSS_PATTERNS: List[Pattern[str]] = [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS: List[Pattern[str]] = [
        re.compile(r"\.\./"),
        re.compile(r"\.\.\\"),
        re.compile(r"/etc/passwd", re.IGNORECASE),
        re.compile(r"c:\\windows", re.IGNORECASE),
    ]

    def __init__(self) -> None:
        """Initialize security validator."""
        self.config = get_config()
        self._max_string_length = 1000

    async def validate(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> SecurityValidationResult:
        """
        Validate tool arguments for security concerns.

        Checks for:
        - SQL injection patterns
        - XSS patterns
        - Path traversal attempts
        - String length limits
        - Dangerous parameter values
        """
        # Validate string lengths
        for key, value in arguments.items():
            if isinstance(value, str):
                if len(value) > self._max_string_length:
                    return SecurityValidationResult(
                        is_valid=False,
                        error_message=f"Parameter '{key}' exceeds maximum length of {self._max_string_length}",
                    )

                # Check for SQL injection
                if self._contains_sql_injection(value):
                    return SecurityValidationResult(
                        is_valid=False,
                        error_message=f"Potential SQL injection detected in parameter '{key}'",
                    )

                # Check for XSS
                if self._contains_xss(value):
                    return SecurityValidationResult(
                        is_valid=False,
                        error_message=f"Potential XSS attack detected in parameter '{key}'",
                    )

                # Check for path traversal
                if self._contains_path_traversal(value):
                    return SecurityValidationResult(
                        is_valid=False,
                        error_message=f"Potential path traversal detected in parameter '{key}'",
                    )

            elif isinstance(value, dict):
                # Recursively validate nested dicts
                result = await self.validate(tool_name, value)
                if not result.is_valid:
                    return result

            elif isinstance(value, list):
                # Validate each item in list
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        if len(item) > self._max_string_length:
                            return SecurityValidationResult(
                                is_valid=False,
                                error_message=f"Parameter '{key}[{i}]' exceeds maximum length",
                            )

        # Tool-specific validation
        if tool_name == "product_search":
            return self._validate_product_search(arguments)
        elif tool_name == "weather_query":
            return self._validate_weather_query(arguments)

        return SecurityValidationResult(is_valid=True)

    def _contains_sql_injection(self, value: str) -> bool:
        """Check if value contains SQL injection patterns."""
        for pattern in self.SQL_INJECTION_PATTERNS:
            if pattern.search(value):
                return True
        return False

    def _contains_xss(self, value: str) -> bool:
        """Check if value contains XSS patterns."""
        for pattern in self.XSS_PATTERNS:
            if pattern.search(value):
                return True
        return False

    def _contains_path_traversal(self, value: str) -> bool:
        """Check if value contains path traversal patterns."""
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if pattern.search(value):
                return True
        return False

    def _validate_product_search(self, args: Dict[str, Any]) -> SecurityValidationResult:
        """Validate product search arguments."""
        keywords = args.get("keywords", "")
        if keywords and len(keywords) < 2:
            return SecurityValidationResult(
                is_valid=False,
                error_message="Search keywords must be at least 2 characters",
            )
        return SecurityValidationResult(is_valid=True)

    def _validate_weather_query(self, args: Dict[str, Any]) -> SecurityValidationResult:
        """Validate weather query arguments."""
        city = args.get("city", "")
        # Basic city name validation - letters, spaces, hyphens only
        if city and not re.match(r"^[\w\s\-]+$", city):
            return SecurityValidationResult(
                is_valid=False,
                error_message="Invalid city name format",
            )
        return SecurityValidationResult(is_valid=True)


def sanitize_input(value: str) -> str:
    """Sanitize user input by removing dangerous characters."""
    if not isinstance(value, str):
        return value
    # Remove null bytes
    value = value.replace("\x00", "")
    # Normalize whitespace
    value = " ".join(value.split())
    return value.strip()
