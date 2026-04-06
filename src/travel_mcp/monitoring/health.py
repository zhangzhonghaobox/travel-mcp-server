"""Health check endpoint handler."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

from travel_mcp.config import get_config


@dataclass
class HealthStatus:
    """Health status information."""

    status: str
    version: str
    uptime_seconds: float
    checks: Dict[str, Any]


class HealthChecker:
    """Performs health checks on the server and its dependencies."""

    def __init__(self) -> None:
        """Initialize health checker."""
        self.config = get_config()
        self._start_time = datetime.now(timezone.utc)

    async def check_health(self) -> HealthStatus:
        """
        Perform comprehensive health check.

        Returns:
            HealthStatus with overall status and individual checks
        """
        checks = {}
        overall_status = "healthy"

        # Check configuration
        checks["configuration"] = self._check_configuration()

        # Check memory (basic)
        checks["memory"] = self._check_memory()

        # Calculate uptime
        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        # Determine overall status
        if any(c.get("status") != "ok" for c in checks.values()):
            overall_status = "degraded"

        return HealthStatus(
            status=overall_status,
            version=self.config.version,
            uptime_seconds=uptime,
            checks=checks,
        )

    def _check_configuration(self) -> Dict[str, Any]:
        """Check if configuration is valid."""
        try:
            # Verify critical config values
            if self.config.server_name and self.config.version:
                return {"status": "ok", "message": "Configuration loaded"}
            return {"status": "error", "message": "Missing required configuration"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage (basic)."""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            mem_mb = mem_info.rss / 1024 / 1024

            return {
                "status": "ok",
                "memory_mb": round(mem_mb, 2),
            }
        except ImportError:
            # psutil not available, skip memory check
            return {"status": "ok", "message": "psutil not available"}
        except Exception as e:
            return {"status": "warning", "message": str(e)}

    def get_liveness(self) -> Dict[str, Any]:
        """Simple liveness probe - is the server running?"""
        return {
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_readiness(self) -> Dict[str, Any]:
        """Readiness probe - is the server ready to accept traffic?"""
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": self.config.version,
        }
