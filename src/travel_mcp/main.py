"""Main entry point for Travel MCP Server."""

import asyncio
import json
import signal
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastmcp import FastMCP

from travel_mcp.config import get_config
from travel_mcp.middleware.logging import LoggingMiddleware
from travel_mcp.middleware.rate_limit import get_rate_limiter
from travel_mcp.monitoring.health import HealthChecker
from travel_mcp.monitoring.metrics import get_metrics_collector
from travel_mcp.server.mcp_server import create_server, TravelMCPServer
from travel_mcp.tools.weather import WeatherQueryTool
from travel_mcp.tools.product import ProductSearchTool
from travel_mcp.tools.attraction import TouristAttractionSearchTool
from travel_mcp.tools.hotel import HotelSearchTool
from travel_mcp.tools.flight import FlightSearchTool
from travel_mcp.tools.base import ToolExecutionContext
from travel_mcp.core.security import SecurityValidator
from travel_mcp.core.permission import Permission, PermissionChecker
from travel_mcp.core.audit import AuditLogger
from travel_mcp.core.error_handler import ErrorResponse, ErrorCode
from travel_mcp.server.sse_transport import SSEServerTransport, get_sse_transport, set_mcp_server

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("main")


# Global server instance for FastMCP tool access
_fast_mcp_server: Optional[TravelMCPServer] = None


def set_fast_mcp_server(server: TravelMCPServer) -> None:
    """Set the global FastMCP server instance for tool access."""
    global _fast_mcp_server
    _fast_mcp_server = server


def get_fast_mcp_server() -> TravelMCPServer:
    """Get the global FastMCP server instance."""
    if _fast_mcp_server is None:
        raise RuntimeError("FastMCP server not initialized")
    return _fast_mcp_server


# Create FastMCP server instance
mcp = FastMCP("Travel MCP Server")


async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a tool with full security checks via the MCP server.

    This delegates to server.call_tool_impl() which applies:
    - Security validation
    - Permission checks
    - Audit logging
    - Metrics collection
    """
    server = get_fast_mcp_server()

    # Delegate to the existing call_tool_impl which has all security infrastructure
    result = await server.call_tool_impl(tool_name, arguments)

    # Extract the text content from CallToolResult
    if result.content and len(result.content) > 0:
        return result.content[0].text
    return json.dumps({"success": False, "error": "No result content"})


# Register tools with FastMCP using decorator pattern
@mcp.tool(name="weather_query")
async def weather_query(city: str, date: str | None = None) -> str:
    """Query weather for a city."""
    return await execute_tool("weather_query", {"city": city, "date": date})


@mcp.tool(name="product_search")
async def product_search(keywords: str, category: str | None = None, limit: int = 10) -> str:
    """Search for travel-related products."""
    return await execute_tool("product_search", {"keywords": keywords, "category": category, "limit": limit})


@mcp.tool(name="tourist_attraction_search")
async def tourist_attraction_search(
    destination: str,
    tags: list[str] | None = None,
    limit: int = 10,
) -> str:
    """Search for tourist attractions at a destination."""
    return await execute_tool("tourist_attraction_search", {"destination": destination, "tags": tags, "limit": limit})


@mcp.tool(name="hotel_search")
async def hotel_search(
    city: str,
    check_in_date: str,
    check_out_date: str,
    guests: int = 1,
    limit: int = 10,
) -> str:
    """Search for hotels in a city."""
    return await execute_tool("hotel_search", {"city": city, "check_in_date": check_in_date, "check_out_date": check_out_date, "guests": guests, "limit": limit})


@mcp.tool(name="flight_search")
async def flight_search(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    passengers: int = 1,
    limit: int = 10,
) -> str:
    """Search for flights between two locations."""
    return await execute_tool("flight_search", {"origin": origin, "destination": destination, "departure_date": departure_date, "return_date": return_date, "passengers": passengers, "limit": limit})


# Create MCP ASGI app - FastMCP manages its own lifespan
# path="/" means FastMCP uses root paths internally, then we mount at /mcp
mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager - combines FastMCP lifespan with our own."""
    config = get_config()
    logger.info(
        "server_starting",
        server_name=config.server_name,
        version=config.version,
        use_mock_data=config.use_mock_data,
    )

    # Create and register tools
    server = create_server()
    server.register_tool(WeatherQueryTool())
    server.register_tool(ProductSearchTool())
    server.register_tool(TouristAttractionSearchTool())
    server.register_tool(HotelSearchTool())
    server.register_tool(FlightSearchTool())

    # Store server instance in app state
    app.state.mcp_server = server

    # Also set global reference for SSE transport
    set_mcp_server(server)

    # Set global reference for FastMCP tools
    set_fast_mcp_server(server)

    logger.info(
        "server_initialized",
        server_name=config.server_name,
        version=config.version,
    )

    # Now run FastMCP's lifespan to initialize its session manager
    async with mcp_app.lifespan(app):
        logger.info(
            "server_started",
            server_name=config.server_name,
            version=config.version,
            host=config.host,
            port=config.port,
        )
        yield
        logger.info("server_shutting_down", server_name=config.server_name)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    config = get_config()

    app = FastAPI(
        title=config.server_name,
        version=config.version,
        description="Travel Agent MCP Server - provides travel-related tools",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Health checker
    health_checker = HealthChecker()

    # Routes
    @app.get("/health")
    async def health() -> JSONResponse:
        """Health check endpoint."""
        status = await health_checker.check_health()
        http_status = 200 if status.status == "healthy" else 503
        return JSONResponse(
            content={
                "status": status.status,
                "version": status.version,
                "uptime_seconds": status.uptime_seconds,
                "checks": status.checks,
            },
            status_code=http_status,
        )

    @app.get("/health/live")
    async def liveness() -> JSONResponse:
        """Liveness probe endpoint."""
        return JSONResponse(content=health_checker.get_liveness())

    @app.get("/health/ready")
    async def readiness() -> JSONResponse:
        """Readiness probe endpoint."""
        return JSONResponse(content=health_checker.get_readiness())

    @app.get("/metrics")
    async def metrics() -> Response:
        """Prometheus metrics endpoint."""
        metrics_collector = get_metrics_collector()
        return metrics_collector.get_metrics()

    # SSE endpoints for MCP protocol - use global singleton
    @app.get("/sse")
    async def sse_endpoint(request: Request):
        """SSE endpoint for MCP server-sent events."""
        transport = get_sse_transport()
        return await transport.handle_sse(request)

    @app.post("/messages")
    async def messages_endpoint(request: Request):
        """HTTP endpoint for receiving MCP messages."""
        transport = get_sse_transport()
        return await transport.handle_messages(request)

    @app.post("/api/v1/tools/{tool_name}")
    async def call_tool(
        tool_name: str,
        request: Request,
    ) -> JSONResponse:
        """
        Direct tool call endpoint (non-MCP protocol).

        For HTTP-based tool invocation outside of MCP.
        """
        config = get_config()

        # API key check
        if config.api_key_enabled:
            api_key = request.headers.get("x-api-key")
            if api_key != config.api_key:
                return JSONResponse(
                    ErrorResponse(
                        code=ErrorCode.PERMISSION_DENIED,
                        message="Invalid API key",
                    ).model_dump(),
                    status_code=403,
                )

        # Rate limiting
        client_id = request.headers.get("x-client-id", request.client.host if request.client else "unknown")
        rate_limiter = get_rate_limiter()
        try:
            await rate_limiter.check_rate_limit(client_id)
        except Exception as e:
            return JSONResponse(
                ErrorResponse(
                    code=ErrorCode.RATE_LIMIT_EXCEEDED,
                    message=str(e),
                ).model_dump(),
                status_code=429,
            )

        # Parse request body
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                ErrorResponse(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="Invalid JSON body",
                ).model_dump(),
                status_code=400,
            )

        # Execute tool via MCP server
        mcp_server: Any = request.app.state.mcp_server

        try:
            result = await mcp_server.server._handler(
                method="tools/call",
                params={"name": tool_name, "arguments": body},
            )
            return JSONResponse(content=result)
        except Exception as e:
            return JSONResponse(
                ErrorResponse(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=str(e),
                ).model_dump(),
                status_code=500,
            )

    # Mount FastMCP at /mcp (mounts after other routes to avoid conflicts)
    app.mount("/mcp", mcp_app)

    return app


def main() -> None:
    """Main entry point."""
    config = get_config()

    # Configure uvicorn
    uvicorn_config: Dict[str, Any] = {
        "app": "travel_mcp.main:create_app",
        "factory": True,
        "host": config.host,
        "port": config.port,
        "log_level": config.log_level.lower(),
        "access_log": True,
    }

    server = uvicorn.Server(uvicorn.Config(**uvicorn_config))

    # Handle shutdown signals
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(server.serve())
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt_received")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
