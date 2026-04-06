"""MCP Server implementation for Travel Agent."""

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListResourcesResult,
    ListToolsResult,
    Resource,
    TextContent,
    Tool,
)

from travel_mcp.config import get_config
from travel_mcp.core.error_handler import ErrorResponse, ErrorCode as TravelErrorCode
from travel_mcp.core.security import SecurityValidator
from travel_mcp.core.permission import Permission, PermissionChecker
from travel_mcp.core.audit import AuditLogger
from travel_mcp.monitoring.metrics import MetricsCollector
from travel_mcp.tools.base import BaseTool, ToolExecutionContext

# Global metrics collector
metrics = MetricsCollector()


class TravelMCPServer:
    """Main MCP Server class for Travel Agent."""

    def __init__(self) -> None:
        """Initialize the MCP Server."""
        self.config = get_config()
        self.server = Server(
            name="travel-mcp-server",
            version=self.config.version,
            instructions="Travel Agent MCP Server - provides travel-related tools including weather, hotels, flights, attractions, and products",
        )
        self._tools: Dict[str, BaseTool] = {}
        self._permission_checker = PermissionChecker()
        self._audit_logger = AuditLogger()
        self._security_validator = SecurityValidator()

        self._register_handlers()

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the server."""
        self._tools[tool.name] = tool
        metrics.register_tool(tool.name)

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List all available tools."""
            tools = []
            for tool in self._tools.values():
                tools.append(
                    Tool(
                        name=tool.name,
                        description=tool.description,
                        inputSchema=tool.input_schema,
                    )
                )
            metrics.record_request("list_tools", success=True)
            return ListToolsResult(tools=tools)

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> CallToolResult:
            """Handle tool calls from clients."""
            metrics.increment_counter("tool_call_total", tool_name=name)

            # Check if tool exists
            if name not in self._tools:
                metrics.increment_counter("tool_call_errors", tool_name=name)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps(
                                ErrorResponse(
                                    code=TravelErrorCode.RESOURCE_NOT_FOUND,
                                    message=f"Tool '{name}' not found",
                                ).model_dump()
                            ),
                        )
                    ],
                    isError=True,
                )

            tool = self._tools[name]

            # Security validation
            security_result = await self._security_validator.validate(
                name, arguments
            )
            if not security_result.is_valid:
                metrics.increment_counter("tool_call_errors", tool_name=name)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps(
                                ErrorResponse(
                                    code=TravelErrorCode.VALIDATION_ERROR,
                                    message=security_result.error_message or "Security validation failed",
                                ).model_dump()
                            ),
                        )
                    ],
                    isError=True,
                )

            # Permission check
            if not self._permission_checker.has_permission(Permission.TOOL_CALL, name):
                metrics.increment_counter("tool_call_errors", tool_name=name)
                self._audit_logger.log_denied_access(name, arguments)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps(
                                ErrorResponse(
                                    code=TravelErrorCode.PERMISSION_DENIED,
                                    message=f"Permission denied for tool '{name}'",
                                ).model_dump()
                            ),
                        )
                    ],
                    isError=True,
                )

            # Execute tool
            context = ToolExecutionContext(
                request_id=f"{name}_{asyncio.get_event_loop().time()}",
                tool_name=name,
                arguments=arguments,
            )

            try:
                result = await tool.execute(context)
                self._audit_logger.log_tool_execution(name, arguments, result)
                metrics.record_request(name, success=True)
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result))]
                )
            except Exception as e:
                metrics.increment_counter("tool_call_errors", tool_name=name)
                self._audit_logger.log_error(name, arguments, str(e))
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps(
                                ErrorResponse(
                                    code=TravelErrorCode.INTERNAL_ERROR,
                                    message=f"Tool execution failed: {str(e)}",
                                ).model_dump()
                            ),
                        )
                    ],
                    isError=True,
                )

    async def run(self) -> None:
        """Run the MCP server using stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def create_server() -> TravelMCPServer:
    """Factory function to create a configured server instance."""
    server = TravelMCPServer()
    return server
