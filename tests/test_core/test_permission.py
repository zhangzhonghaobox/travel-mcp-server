"""Tests for permission module."""

import pytest

from travel_mcp.core.permission import (
    Permission,
    PermissionChecker,
    require_permission,
)


class TestPermission:
    """Test suite for Permission enum."""

    def test_permission_values(self) -> None:
        """Test permission enum values."""
        assert Permission.TOOL_CALL_WEATHER.value == "tool:call:weather_query"
        assert Permission.TOOL_CALL_PRODUCT.value == "tool:call:product_search"
        assert Permission.ADMIN_ACCESS.value == "admin:access"


class TestPermissionChecker:
    """Test suite for PermissionChecker."""

    @pytest.fixture
    def checker(self) -> PermissionChecker:
        """Create permission checker instance."""
        return PermissionChecker()

    def test_default_role_is_user(self, checker: PermissionChecker) -> None:
        """Test default role is user."""
        checker.set_user("test_user")
        assert "user" in checker.get_user_roles("test_user")

    def test_add_user_role(self, checker: PermissionChecker) -> None:
        """Test adding role to user."""
        checker.add_user_role("test_user", "admin")
        assert "admin" in checker.get_user_roles("test_user")

    def test_remove_user_role(self, checker: PermissionChecker) -> None:
        """Test removing role from user."""
        checker.add_user_role("test_user", "admin")
        checker.remove_user_role("test_user", "admin")
        assert "admin" not in checker.get_user_roles("test_user")

    def test_unknown_role_raises(self, checker: PermissionChecker) -> None:
        """Test adding unknown role raises error."""
        with pytest.raises(ValueError, match="Unknown role"):
            checker.add_user_role("test_user", "superadmin")

    def test_user_has_tool_permission(self, checker: PermissionChecker) -> None:
        """Test user role has tool permissions."""
        checker.set_user("test_user")
        assert checker.has_permission(Permission.TOOL_CALL_WEATHER, "weather_query") is True

    def test_user_lacks_admin_permission(self, checker: PermissionChecker) -> None:
        """Test user role lacks admin permissions."""
        checker.set_user("test_user")
        assert checker.has_permission(Permission.ADMIN_ACCESS) is False

    def test_admin_has_all_permissions(self, checker: PermissionChecker) -> None:
        """Test admin role has all permissions."""
        checker.add_user_role("admin_user", "admin")
        checker.set_user("admin_user")
        assert checker.has_permission(Permission.ADMIN_ACCESS) is True
        assert checker.has_permission(Permission.METRICS_ACCESS) is True
        assert checker.has_permission(Permission.TOOL_CALL_WEATHER, "weather_query") is True

    def test_readonly_role_limited_permissions(self, checker: PermissionChecker) -> None:
        """Test readonly role has limited permissions."""
        checker.add_user_role("readonly_user", "readonly")
        checker.set_user("readonly_user")
        assert checker.has_permission(Permission.TOOL_CALL_WEATHER, "weather_query") is True
        assert checker.has_permission(Permission.TOOL_CALL_FLIGHT, "flight_search") is False

    def test_require_permission_raises(self, checker: PermissionChecker) -> None:
        """Test require_permission raises when denied."""
        checker.set_user("test_user")
        with pytest.raises(PermissionError):
            checker.require_permission(Permission.ADMIN_ACCESS)

    def test_clear_user(self, checker: PermissionChecker) -> None:
        """Test clearing user removes their roles."""
        checker.set_user("test_user")
        checker.clear_user()
        # After clear, no roles should be found (will use default)
        assert checker.get_user_roles("test_user") == {"user"}


class TestRequirePermission:
    """Test suite for require_permission function."""

    def test_require_permission_raises_on_denied(self) -> None:
        """Test function raises PermissionError when denied."""
        with pytest.raises(PermissionError):
            require_permission(Permission.ADMIN_ACCESS)
