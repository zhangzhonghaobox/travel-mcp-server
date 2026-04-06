# Travel Agent MCP Server - Architecture Design

## 1. Overview

The Travel Agent MCP Server follows the Model Context Protocol (MCP) architecture, providing a standardized interface for AI agents to access travel-related tools and data.

## 2. Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Layer                          │
│  (HTTP Server, Health, Metrics, SSE Transport)              │
├─────────────────────────────────────────────────────────────┤
│                      FastMCP Layer                           │
│  (Official FastMCP /mcp endpoint with ASGI transport)      │
├─────────────────────────────────────────────────────────────┤
│                      MCP Server Layer                        │
│  (Protocol Handler, Tool Registry, Request Routing)         │
├─────────────────────────────────────────────────────────────┤
│                       Tools Layer                            │
│  (Weather, Product, Attraction, Hotel, Flight)                │
├─────────────────────────────────────────────────────────────┤
│                     Services Layer                           │
│  (Real API Services / Mock Services)                        │
├─────────────────────────────────────────────────────────────┤
│                      Core Layer                              │
│  (Security, Permission, Audit, Error Handling)               │
├─────────────────────────────────────────────────────────────┤
│                     Monitoring Layer                         │
│  (Health Checks, Metrics, Logging)                           │
└─────────────────────────────────────────────────────────────┘
```

## 3. Component Design

### 3.1 Server Components

#### TravelMCPServer
- Manages tool registration
- Handles MCP protocol communication
- Routes tool calls to appropriate handlers
- Integrates with security and permission checks

#### SSEServerTransport
- Implements Server-Sent Events for real-time communication
- Manages client sessions
- Handles HTTP POST for client-to-server messages

#### FastMCP Integration
- Official FastMCP framework integration at `/mcp` endpoint
- Uses FastMCP's `mount()` pattern for FastAPI integration
- Direct decorator-based tool registration (`@mcp.tool()`)
- Reuses existing tool implementations via wrapper functions
- ASGI-based transport for MCP protocol

### 3.2 Tool Components

Each tool inherits from `BaseTool` and implements:
- `name`: Unique identifier
- `description`: Human-readable description
- `input_schema`: JSON Schema for input validation
- `execute()`: Main tool logic

Tools are registered with the MCP server and accessed via the protocol.

### 3.3 Service Components

#### DataSource Factory
- Implements abstract factory pattern
- Switches between mock and real services based on configuration
- Provides dependency injection for services

#### Service Implementations
- **Mock Services**: Return realistic fake data for testing
- **Real Services**: Call external APIs with retry logic

### 3.4 Core Components

#### SecurityValidator
- Input sanitization
- Injection attack detection (SQL, XSS, Path Traversal)
- Tool-specific validation

#### PermissionChecker
- Role-based access control (RBAC)
- Tool-level permissions
- Default roles: user, admin, readonly

#### AuditLogger
- Structured logging of all operations
- Sensitive data redaction
- Security event tracking

#### ErrorHandler
- Standardized error codes
- HTTP status code mapping
- Detailed error responses

### 3.5 Monitoring Components

#### HealthChecker
- Liveness and readiness probes
- Dependency health checks
- Uptime tracking

#### MetricsCollector
- Prometheus-compatible metrics
- Request latency histograms
- Counter metrics for calls and errors

## 4. Data Flow

### 4.1 Tool Call Flow

```
Client Request
      │
      ▼
┌─────────────────┐
│   Security      │ ← Input Validation
│   Validation    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Permission   │ ← RBAC Check
│    Checker      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Tools       │ ← Execute Tool
│     Layer       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Services     │ ← Data Source (Mock/Real)
│     Layer       │
└────────┬────────┘
         │
         ▼
    Response
```

### 4.2 MCP Protocol Flow

```
Client                         Server
  │                              │
  │──── MCP Initialize ──────────▶│
  │◀─── Server Info ─────────────│
  │                              │
  │──── List Tools ─────────────▶│
  │◀─── Tool List ───────────────│
  │                              │
  │──── Call Tool ──────────────▶│
  │◀─── Tool Result ─────────────│
  │                              │
```

## 5. Security Architecture

### 5.1 Defense in Depth

1. **Input Layer**: Pydantic validation + SecurityValidator
2. **Authentication Layer**: API key verification
3. **Authorization Layer**: Permission checker with RBAC
4. **Audit Layer**: Comprehensive logging

### 5.2 Rate Limiting

Sliding window algorithm implementation:
- Configurable requests per minute per client
- Automatic cleanup of old entries
- Graceful handling of exceeded limits

## 6. Observability Architecture

### 6.1 Structured Logging

Using structlog for JSON-formatted logs:
- Request/response logging
- Error tracking with stack traces
- Audit events
- Performance metrics

### 6.2 Metrics

Prometheus-compatible metrics:
- `travel_mcp_requests_total`: Total requests counter
- `travel_mcp_request_latency_seconds`: Request latency histogram
- `travel_mcp_tool_calls_total`: Tool call counter
- `travel_mcp_tool_execution_seconds`: Tool execution time
- `travel_mcp_errors_total`: Error counter
- `travel_mcp_rate_limit_hits_total`: Rate limit hits
- `travel_mcp_active_requests`: Active requests gauge

### 6.3 Health Checks

- `/health`: Comprehensive health with component checks
- `/health/live`: Kubernetes liveness probe
- `/health/ready`: Kubernetes readiness probe

## 7. Deployment Architecture

### 7.1 Container Deployment

```
┌─────────────────────────────────────────────────────────┐
│                     Load Balancer                       │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ Server 1│   │ Server 2│   │ Server 3│
   │ (Pod)   │   │ (Pod)   │   │ (Pod)   │
   └─────────┘   └─────────┘   └─────────┘
```

### 7.2 Docker Compose Stack

- **travel-mcp-server**: Main application container
- **prometheus**: Metrics collection (optional)
- **grafana**: Visualization (optional)

## 8. Configuration Management

Environment-based configuration with `pydantic-settings`:
- `.env` file for local development
- Environment variables for production
- No hardcoded values
- Secrets managed via API keys

## 9. Error Handling Strategy

1. **Validation Errors**: Return 400 with details
2. **Authentication Errors**: Return 403
3. **Rate Limiting**: Return 429 with retry-after header
4. **Service Errors**: Return 503 with fallback to mock data
5. **Internal Errors**: Return 500 with error ID for tracking

## 10. Caching Strategy

- **TTL Cache**: For weather and search results
- **Cache Key**: Based on request parameters
- **Expiration**: 5 minutes for most data
- **Cache Clear**: Available via decorator
