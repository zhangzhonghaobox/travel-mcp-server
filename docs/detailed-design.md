# Travel Agent MCP Server - Detailed Design

## 1. Project Structure

```
travel-mcp-server/
├── pyproject.toml           # Project configuration and dependencies
├── uv.lock                  # Locked dependencies
├── .env.example             # Environment variables template
├── Dockerfile               # Container build
├── docker-compose.yml       # Container orchestration
├── prometheus.yml           # Prometheus config
├── README.md                # Project documentation
├── docs/
│   ├── requirements.md      # Requirements specification
│   ├── architecture.md      # Architecture documentation
│   └── detailed-design.md   # This file
├── src/
│   └── travel_mcp/
│       ├── __init__.py
│       ├── main.py              # FastAPI application entry
│       ├── config.py            # Configuration management
│       ├── server/
│       │   ├── __init__.py
│       │   ├── mcp_server.py    # MCP Server implementation
│       │   └── sse_transport.py # SSE transport layer
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── base.py          # Base tool class
│       │   ├── weather.py       # Weather tool
│       │   ├── product.py       # Product search tool
│       │   ├── attraction.py    # Attraction search tool
│       │   ├── hotel.py         # Hotel search tool
│       │   └── flight.py        # Flight search tool
│       ├── services/
│       │   ├── __init__.py
│       │   ├── data_source.py        # Service factory
│       │   ├── weather_service.py    # Real weather API
│       │   ├── product_service.py    # Real product API
│       │   ├── mock_weather.py        # Mock weather data
│       │   ├── mock_product.py       # Mock product data
│       │   ├── mock_attraction.py    # Mock attraction data
│       │   ├── mock_hotel.py          # Mock hotel data
│       │   └── mock_flight.py        # Mock flight data
│       ├── core/
│       │   ├── __init__.py
│       │   ├── security.py      # Security validation
│       │   ├── permission.py    # Permission management
│       │   ├── error_handler.py  # Error handling
│       │   └── audit.py         # Audit logging
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── rate_limit.py    # Rate limiting
│       │   └── logging.py       # Request logging
│       ├── monitoring/
│       │   ├── __init__.py
│       │   ├── health.py        # Health checks
│       │   └── metrics.py       # Prometheus metrics
│       └── utils/
│           ├── __init__.py
│           ├── cache.py         # Caching utilities
│           └── retry.py         # Retry utilities
└── tests/
    ├── __init__.py
    ├── conftest.py              # Pytest fixtures
    ├── test_tools/
    │   ├── __init__.py
    │   ├── test_weather.py
    │   └── test_product.py
    └── test_core/
        ├── __init__.py
        ├── test_security.py
        └── test_permission.py
```

## 2. Configuration Schema

```python
class MCPServerConfig(BaseSettings):
    # Identity
    server_name: str = "travel-mcp-server"
    version: str = "1.0.0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # MCP
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8000

    # Performance
    max_concurrent_requests: int = 100
    request_timeout: float = 30.0

    # Data Source
    use_mock_data: bool = True

    # API Keys
    amap_api_key: str = ""
    weather_api_key: str = ""

    # Security
    api_key: str = ""
    rate_limit_per_minute: int = 60

    # Monitoring
    log_level: str = "INFO"
    metrics_enabled: bool = True
```

## 3. Tool Interface Design

### 3.1 Base Tool

```python
class BaseTool(ABC):
    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = {}

    @abstractmethod
    async def execute(self, context: ToolExecutionContext) -> Dict[str, Any]:
        pass
```

### 3.2 Weather Tool Schema

```json
{
  "type": "object",
  "properties": {
    "city": {
      "type": "string",
      "description": "City name to query weather for"
    },
    "date": {
      "type": "string",
      "description": "Date in YYYY-MM-DD format"
    }
  },
  "required": ["city"]
}
```

### 3.3 Tool Response Format

```json
{
  "success": true,
  "data": {
    "city": "Beijing",
    "temperature_c": 18,
    "humidity": 65,
    "condition": "Sunny"
  }
}
```

## 4. Error Response Format

```json
{
  "code": "VALIDATION_ERROR",
  "message": "City parameter is required",
  "details": {
    "field": "city",
    "reason": "missing_required_field"
  }
}
```

## 5. API Endpoints

### 5.1 Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /health | GET | Full health check |
| /health/live | GET | Liveness probe |
| /health/ready | GET | Readiness probe |

### 5.2 Metrics Endpoint

| Endpoint | Method | Description |
|----------|--------|-------------|
| /metrics | GET | Prometheus metrics |

### 5.3 Tool Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/tools/{tool_name} | POST | Direct tool call |

## 6. Service Factory

```python
class DataSource:
    def get_weather_service(self) -> WeatherService | MockWeatherService:
        if self.config.use_mock_data:
            return MockWeatherService()
        return WeatherService(api_key=self.config.amap_api_key)
```

## 7. Security Patterns

### 7.1 Input Validation

- Pydantic model validation
- Regex pattern matching for injection
- String length limits

### 7.2 Permission Model

```
Permission.TOOL_CALL_WEATHER     → user, admin
Permission.TOOL_CALL_PRODUCT     → user, admin
Permission.TOOL_CALL_ATTRACTION  → user, admin
Permission.TOOL_CALL_HOTEL       → user, admin
Permission.TOOL_CALL_FLIGHT      → user, admin
Permission.ADMIN_ACCESS          → admin only
Permission.METRICS_ACCESS         → admin only
```

## 8. Caching Design

```python
@timed_cache(seconds=300)
async def get_weather(self, city: str, date: Optional[str] = None) -> Dict[str, Any]:
    # Result cached for 5 minutes
    pass
```

## 9. Retry Strategy

```python
@retry_with_backoff(max_retries=3, base_delay=1.0, exponential_base=2.0)
async def fetch_weather(self, city: str) -> Dict[str, Any]:
    # Retries with exponential backoff on failure
    pass
```

## 10. Monitoring Metrics

### 10.1 Counters
- `travel_mcp_requests_total{method, endpoint, status}`
- `travel_mcp_tool_calls_total{tool_name, status}`
- `travel_mcp_errors_total{error_type, tool_name}`
- `travel_mcp_rate_limit_hits_total`

### 10.2 Histograms
- `travel_mcp_request_latency_seconds{method, endpoint}`
- `travel_mcp_tool_execution_seconds{tool_name}`

### 10.3 Gauges
- `travel_mcp_active_requests`

## 11. Health Check Format

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "checks": {
    "configuration": {"status": "ok"},
    "memory": {"status": "ok", "memory_mb": 128.5}
  }
}
```

## 12. Rate Limiting Algorithm

Sliding window counter:
1. Maintain list of request timestamps per client
2. On each request, remove timestamps older than 60 seconds
3. If remaining count >= limit, reject with 429
4. Otherwise, add current timestamp and allow

## 13. Audit Log Format

```json
{
  "event_type": "TOOL_EXECUTION",
  "tool_name": "weather_query",
  "user_id": "user123",
  "timestamp": "2024-01-15T10:30:00Z",
  "arguments": {"city": "Beijing"},
  "result_summary": "Success: 1 result"
}
```
