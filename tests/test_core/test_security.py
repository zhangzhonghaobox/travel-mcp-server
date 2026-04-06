"""Tests for security module."""

import pytest
from travel_mcp.core.security import SecurityValidator, sanitize_input, SecurityValidationResult


class TestSecurityValidator:
    """Test suite for SecurityValidator."""

    @pytest.fixture
    def validator(self) -> SecurityValidator:
        """Create validator instance."""
        return SecurityValidator()

    @pytest.mark.asyncio
    async def test_valid_input(self, validator: SecurityValidator) -> None:
        """Test valid input passes validation."""
        result = await validator.validate(
            "weather_query",
            {"city": "Beijing"}
        )
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_sql_injection_detected(self, validator: SecurityValidator) -> None:
        """Test SQL injection is detected."""
        result = await validator.validate(
            "weather_query",
            {"city": "Beijing'; DROP TABLE users;--"}
        )
        assert result.is_valid is False
        assert "SQL injection" in result.error_message

    @pytest.mark.asyncio
    async def test_xss_detected(self, validator: SecurityValidator) -> None:
        """Test XSS attack is detected."""
        result = await validator.validate(
            "weather_query",
            {"city": "<script>alert('xss')</script>"}
        )
        assert result.is_valid is False
        assert "XSS" in result.error_message

    @pytest.mark.asyncio
    async def test_path_traversal_detected(self, validator: SecurityValidator) -> None:
        """Test path traversal is detected."""
        result = await validator.validate(
            "weather_query",
            {"city": "../../etc/passwd"}
        )
        assert result.is_valid is False
        assert "path traversal" in result.error_message

    @pytest.mark.asyncio
    async def test_long_string_rejected(self, validator: SecurityValidator) -> None:
        """Test overly long strings are rejected."""
        result = await validator.validate(
            "weather_query",
            {"city": "x" * 2000}  # Exceeds 1000 char limit
        )
        assert result.is_valid is False
        assert "exceeds maximum length" in result.error_message

    @pytest.mark.asyncio
    async def test_nested_dict_validation(self, validator: SecurityValidator) -> None:
        """Test nested dictionary validation."""
        result = await validator.validate(
            "product_search",
            {"keywords": "test", "nested": {"value": "normal"}}
        )
        assert result.is_valid is True


class TestSanitizeInput:
    """Test suite for input sanitization."""

    def test_remove_null_bytes(self) -> None:
        """Test null bytes are removed."""
        result = sanitize_input("test\x00value")
        assert "\x00" not in result

    def test_normalize_whitespace(self) -> None:
        """Test whitespace is normalized."""
        result = sanitize_input("test    multiple   spaces")
        assert result == "test multiple spaces"

    def test_strip_edges(self) -> None:
        """Test leading/trailing whitespace is stripped."""
        result = sanitize_input("  trimmed  ")
        assert result == "trimmed"
