"""SSE (Server-Sent Events) transport layer for MCP over HTTP."""

import asyncio
import json
import uuid
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from sse_starlette.sse import EventSourceResponse

from travel_mcp.config import get_config


class SSEServerTransport:
    """Handles SSE transport for MCP protocol using Server-Sent Events."""

    def __init__(self) -> None:
        """Initialize SSE transport."""
        self.config = get_config()
        self._sessions: Dict[str, asyncio.Queue] = {}

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = asyncio.Queue()
        return session_id

    def get_queue(self, session_id: str) -> Optional[asyncio.Queue]:
        """Get the queue for a session."""
        return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> None:
        """Close and remove a session."""
        self._sessions.pop(session_id, None)

    async def handle_sse(self, request: Request) -> Response:
        """Handle SSE connection from MCP Inspector."""
        session_id = self.create_session()

        async def event_generator():
            """Generator that yields SSE events."""
            yield {
                "event": "endpoint",
                "data": f"/messages?session_id={session_id}"
            }
            yield {
                "event": "message",
                "data": json.dumps({
                    "jsonrpc": "2.0",
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {"listChanged": True}},
                        "serverInfo": {"name": "travel-mcp-server", "version": "1.0.0"}
                    }
                })
            }

            try:
                while True:
                    try:
                        message = await asyncio.wait_for(
                            self._sessions[session_id].get(), timeout=30
                        )
                        yield {"event": "message", "data": json.dumps(message)}
                    except asyncio.TimeoutError:
                        yield {"event": "ping", "data": ""}
                    except asyncio.CancelledError:
                        break
            finally:
                self.close_session(session_id)

        return EventSourceResponse(
            event_generator(),
            media_type="text/event-stream"
        )

    async def handle_messages(self, request: Request) -> Response:
        """Handle incoming messages from MCP client."""
        session_id = request.query_params.get("session_id")

        if not session_id or session_id not in self._sessions:
            return JSONResponse(
                {"error": "Invalid or missing session ID"},
                status_code=400
            )

        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                {"error": "Invalid JSON body"},
                status_code=400
            )

        response = await self._process_message(session_id, body)
        if response:
            await self._sessions[session_id].put(response)

        return JSONResponse({"status": "ok"})

    async def _process_message(self, session_id: str, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming JSON-RPC message."""
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": True}},
                    "serverInfo": {"name": "travel-mcp-server", "version": "1.0.0"}
                }
            }

        elif method == "tools/list":
            try:
                mcp_server = get_mcp_server()
                if mcp_server:
                    # Use the shared implementation from TravelMCPServer
                    result = await mcp_server.list_tools_impl()
                    # Convert ListToolsResult to dict format for JSON-RPC
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "tools": [
                                {
                                    "name": t.name,
                                    "description": t.description,
                                    "inputSchema": t.inputSchema
                                }
                                for t in result.tools
                            ]
                        }
                    }
            except Exception as e:
                return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": str(e)}}
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": []}}

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                mcp_server = get_mcp_server()
                if mcp_server:
                    # Use the shared implementation from TravelMCPServer
                    result = await mcp_server.call_tool_impl(tool_name, tool_args)
                    # Convert CallToolResult to dict format for JSON-RPC
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [{"type": c.type, "text": c.text} for c in result.content],
                            "isError": result.isError
                        }
                    }
            except Exception as e:
                return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": str(e)}}

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        return None


# Module-level singleton
_sse_transport: Optional[SSEServerTransport] = None
# Global reference to MCP server
_mcp_server = None


def set_mcp_server(server) -> None:
    """Set the global MCP server reference."""
    global _mcp_server
    _mcp_server = server


def get_mcp_server():
    """Get the global MCP server reference."""
    return _mcp_server


def get_sse_transport() -> SSEServerTransport:
    """Get the global SSE transport singleton."""
    global _sse_transport
    if _sse_transport is None:
        _sse_transport = SSEServerTransport()
    return _sse_transport
