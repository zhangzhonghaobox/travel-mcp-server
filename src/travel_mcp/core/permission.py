"""Permission management module for Travel MCP Server."""

from enum import Enum
from typing import Dict, Set


class Permission(str, Enum):
    """Available permissions in the system."""

    # Tool permissions
    TOOL_CALL = "tool:call"
    TOOL_CALL_WEATHER = "tool:call:weather_query"
    TOOL_CALL_PRODUCT = "tool:call:product_search"
    TOOL_CALL_ATTRACTION = "tool:call:tourist_attraction_search"
    TOOL_CALL_HOTEL = "tool:call:hotel_search"
    TOOL_CALL_FLIGHT = "tool:call:flight_search"

    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    METRICS_ACCESS = "admin:metrics"
    CONFIG_ACCESS = "admin:config"


# Default role-based permissions
DEFAULT_ROLE_PERMISSIONS: Dict[str, Set[Permission]] = {
    "user": {
        Permission.TOOL_CALL_WEATHER,
        Permission.TOOL_CALL_PRODUCT,
        Permission.TOOL_CALL_ATTRACTION,
        Permission.TOOL_CALL_HOTEL,
        Permission.TOOL_CALL_FLIGHT,
    },
    "admin": {
        Permission.TOOL_CALL_WEATHER,
        Permission.TOOL_CALL_PRODUCT,
        Permission.TOOL_CALL_ATTRACTION,
        Permission.TOOL_CALL_HOTEL,
        Permission.TOOL_CALL_FLIGHT,
        Permission.ADMIN_ACCESS,
        Permission.METRICS_ACCESS,
        Permission.CONFIG_ACCESS,
    },
    "readonly": {
        Permission.TOOL_CALL_WEATHER,
        Permission.TOOL_CALL_PRODUCT,
    },
}


class PermissionChecker:
    """Manages and checks permissions for tool access."""

    def __init__(self) -> None:
        """Initialize permission checker with default roles."""
        self._role_permissions: Dict[str, Set[Permission]] = DEFAULT_ROLE_PERMISSIONS.copy()
        self._user_roles: Dict[str, Set[str]] = {}
        # Default all users to "user" role
        self._default_role = "user"
        self._current_user_id: str | None = None

    def add_user_role(self, user_id: str, role: str) -> None:
        """Assign a role to a user."""
        if role not in self._role_permissions:
            raise ValueError(f"Unknown role: {role}")
        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
        self._user_roles[user_id].add(role)

    def remove_user_role(self, user_id: str, role: str) -> None:
        """Remove a role from a user."""
        if user_id in self._user_roles:
            self._user_roles[user_id].discard(role)

    def get_user_roles(self, user_id: str) -> Set[str]:
        """Get all roles assigned to a user."""
        return self._user_roles.get(user_id, {self._default_role})

    def has_permission(self, permission: Permission, resource: str = "") -> bool:
        """
        Check if a permission is granted.

        For tool permissions, resource is the tool name.
        """
        user_id = self._current_user_id or "anonymous"

        # Super admin has all permissions
        if "admin" in self._user_roles.get(user_id, set()):
            return True

        # Check if user has the specific permission
        # Map generic TOOL_CALL to specific tool permission
        if permission == Permission.TOOL_CALL and resource:
            tool_permission = Permission(f"tool:call:{resource}")
            return self._check_permission_for_user(user_id, tool_permission)

        return self._check_permission_for_user(user_id, permission)

    def _check_permission_for_user(self, user_id: str, permission: Permission) -> bool:
        """Check if a user has a specific permission."""
        roles = self._user_roles.get(user_id, {self._default_role})
        for role in roles:
            if role in self._role_permissions:
                if permission in self._role_permissions[role]:
                    return True
        return False

    def set_user(self, user_id: str) -> None:
        """Set the current user for permission checks."""
        self._current_user_id = user_id
        if user_id not in self._user_roles:
            self._user_roles[user_id] = {self._default_role}

    def clear_user(self) -> None:
        """Clear the current user."""
        self._current_user_id = None

    def require_permission(self, permission: Permission, resource: str = "") -> None:
        """Raise exception if permission is not granted."""
        if not self.has_permission(permission, resource):
            raise PermissionError(f"Permission denied: {permission.value}")


def require_permission(permission: Permission, resource: str = "") -> None:
    """Decorator/standalone function to check permissions."""
    checker = PermissionChecker()
    checker.require_permission(permission, resource)
