"""Prometheus metrics collection."""

from typing import Any, Dict, Optional

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response


# Request metrics
REQUEST_COUNT = Counter(
    "travel_mcp_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "travel_mcp_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Tool metrics
TOOL_CALL_COUNT = Counter(
    "travel_mcp_tool_calls_total",
    "Total number of tool calls",
    ["tool_name", "status"],
)

TOOL_EXECUTION_TIME = Histogram(
    "travel_mcp_tool_execution_seconds",
    "Tool execution time in seconds",
    ["tool_name"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Error metrics
ERROR_COUNT = Counter(
    "travel_mcp_errors_total",
    "Total number of errors",
    ["error_type", "tool_name"],
)

# Rate limit metrics
RATE_LIMIT_HITS = Counter(
    "travel_mcp_rate_limit_hits_total",
    "Total number of rate limit hits",
)

# Active requests
ACTIVE_REQUESTS = Gauge(
    "travel_mcp_active_requests",
    "Number of currently active requests",
)


class MetricsCollector:
    """Collector for application-specific metrics."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._registered_tools: set = set()

    def register_tool(self, tool_name: str) -> None:
        """Register a tool for metrics."""
        self._registered_tools.add(tool_name)

    def increment_counter(self, name: str, **labels) -> None:
        """Increment a counter metric."""
        if name == "tool_call_total":
            TOOL_CALL_COUNT.labels(tool_name=labels.get("tool_name", "unknown"), status="success").inc()
        elif name == "tool_call_errors":
            ERROR_COUNT.labels(error_type="tool_error", tool_name=labels.get("tool_name", "unknown")).inc()

    def record_request(self, endpoint: str, success: bool) -> None:
        """Record an API request."""
        status = "success" if success else "error"
        REQUEST_COUNT.labels(method="POST", endpoint=endpoint, status=status).inc()

    def record_tool_execution(self, tool_name: str, duration: float) -> None:
        """Record tool execution time."""
        TOOL_EXECUTION_TIME.labels(tool_name=tool_name).observe(duration)

    def record_error(self, error_type: str, tool_name: Optional[str] = None) -> None:
        """Record an error."""
        ERROR_COUNT.labels(error_type=error_type, tool_name=tool_name or "unknown").inc()

    def record_rate_limit_hit(self) -> None:
        """Record a rate limit hit."""
        RATE_LIMIT_HITS.inc()

    def set_active_requests(self, count: int) -> None:
        """Set the number of active requests."""
        ACTIVE_REQUESTS.set(count)

    def get_metrics(self) -> Response:
        """Generate Prometheus metrics response."""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )


# Global metrics collector instance
_metrics: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics
