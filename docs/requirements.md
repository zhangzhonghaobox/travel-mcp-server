# Travel Agent MCP Server - Requirements

## 1. Overview

The Travel Agent MCP Server is a Model Context Protocol (MCP) server that provides travel-related tools including weather queries, hotel searches, flight searches, attraction searches, and product searches. The server is designed to be used by AI agents to assist users with travel planning tasks.

## 2. Core Tools

### 2.1 Weather Query (`weather_query`)

**Description**: Query current weather and forecasts for cities worldwide.

**Parameters**:

| Parameter | Type   | Required | Description                                   |
| --------- | ------ | -------- | --------------------------------------------- |
| city      | string | Yes      | City name to query                            |
| date      | string | No       | Date in YYYY-MM-DD format (defaults to today) |

**Returns**:

- Temperature (Celsius/Fahrenheit)
- Humidity percentage
- Wind speed
- Weather condition
- UV index
- Forecast information

**Data Sources**:

- Mock data (default for development/testing)
- WeatherAPI (production with API key)
- Amap (高德) weather API (production with API key)

### 2.2 Product Search (`product_search`)

**Description**: Search for travel-related products such as luggage, adapters, and accessories.

**Parameters**:

| Parameter | Type    | Required | Description                    |
| --------- | ------- | -------- | ------------------------------ |
| keywords  | string  | Yes      | Search keywords                |
| category  | string  | No       | Product category filter        |
| limit     | integer | No       | Max results (1-50, default 10) |

**Returns**:

- Product list with names, prices, ratings
- Product descriptions
- Review counts
- Category information

### 2.3 Tourist Attraction Search (`tourist_attraction_search`)

**Description**: Search for tourist attractions at destinations with tag-based filtering.

**Parameters**:

| Parameter   | Type    | Required | Description                                 |
| ----------- | ------- | -------- | ------------------------------------------- |
| destination | string  | Yes      | Destination city                            |
| tags        | array   | No       | Interest tags (history, nature, food, etc.) |
| limit       | integer | No       | Max results (1-50, default 10)              |

**Returns**:

- Attraction name and description
- Rating and review count
- Ticket price
- Opening hours
- Location information

### 2.4 Hotel Search (`hotel_search`)

**Description**: Search for hotels with check-in/out dates and guest count.

**Parameters**:

| Parameter        | Type    | Required | Description                        |
| ---------------- | ------- | -------- | ---------------------------------- |
| city             | string  | Yes      | City to search                     |
| check\_in\_date  | string  | Yes      | Check-in date (YYYY-MM-DD)         |
| check\_out\_date | string  | Yes      | Check-out date (YYYY-MM-DD)        |
| guests           | integer | No       | Number of guests (1-10, default 1) |
| limit            | integer | No       | Max results (1-50, default 10)     |

**Returns**:

- Hotel name and rating
- Star rating
- Price per night and total
- Amenities list
- Location information

### 2.5 Flight Search (`flight_search`)

**Description**: Search for flights between origin and destination.

**Parameters**:

| Parameter       | Type    | Required | Description                           |
| --------------- | ------- | -------- | ------------------------------------- |
| origin          | string  | Yes      | Origin city or airport code           |
| destination     | string  | Yes      | Destination city or airport code      |
| departure\_date | string  | Yes      | Departure date (YYYY-MM-DD)           |
| return\_date    | string  | No       | Return date for round trip            |
| passengers      | integer | No       | Number of passengers (1-9, default 1) |
| limit           | integer | No       | Max results (1-50, default 10)        |

**Returns**:

- Flight number and airline
- Departure/arrival times
- Duration and stops
- Price per person and total
- Seat availability

## 3. Non-Functional Requirements

### 3.1 Error Handling

The server implements a standardized error code system:

| Error Code            | HTTP Status | Description                  |
| --------------------- | ----------- | ---------------------------- |
| VALIDATION\_ERROR     | 400         | Input validation failed      |
| RESOURCE\_NOT\_FOUND  | 404         | Requested resource not found |
| PERMISSION\_DENIED    | 403         | Insufficient permissions     |
| RATE\_LIMIT\_EXCEEDED | 429         | Too many requests            |
| INTERNAL\_ERROR       | 500         | Internal server error        |
| SERVICE\_UNAVAILABLE  | 503         | External service unavailable |
| TIMEOUT\_ERROR        | 504         | Request timeout              |

### 3.2 Security

- **Input Validation**: All inputs are validated using Pydantic models
- **SQL Injection Prevention**: Detection of SQL injection patterns
- **XSS Prevention**: Detection of XSS attack patterns
- **Path Traversal Prevention**: Detection of path traversal attempts
- **API Key Authentication**: Optional API key for external requests
- **Rate Limiting**: Configurable per-client rate limits (sliding window algorithm)
- **Audit Logging**: All tool executions and access attempts are logged

### 3.3 Performance

- Maximum concurrent requests: 100 (configurable)
- Request timeout: 30 seconds (configurable)
- Caching: In-memory TTL cache for frequently accessed data
- Retry with exponential backoff for external API failures

### 3.4 Observability

- **Health Endpoints**:
  - `/health` - Full health check with component status
  - `/health/live` - Liveness probe
  - `/health/ready` - Readiness probe
- **Metrics**:
  - `/metrics` - Prometheus-compatible metrics endpoint
  - Request counts and latencies
  - Tool execution metrics
  - Error counts
  - Rate limit metrics
- **Logging**: Structured JSON logging with timestamps

## 4. Configuration

Configuration is managed through environment variables with the `TRAVEL_` prefix:

| Variable                         | Default | Description                  |
| -------------------------------- | ------- | ---------------------------- |
| TRAVEL\_USE\_MOCK\_DATA          | true    | Use mock data vs real APIs   |
| TRAVEL\_API\_KEY                 | ""      | API key for authentication   |
| TRAVEL\_RATE\_LIMIT\_PER\_MINUTE | 60      | Rate limit per client        |
| TRAVEL\_LOG\_LEVEL               | INFO    | Logging level                |
| TRAVEL\_METRICS\_ENABLED         | true    | Enable Prometheus metrics    |
| TRAVEL\_AMAP\_API\_KEY           | ""      | Amap API key for real data   |
| TRAVEL\_WEATHER\_API\_KEY        | ""      | WeatherAPI key for real data |

## 5. Deployment

### 5.1 Docker

```bash
# Build image
docker build -t travel-mcp-server .

# Run container
docker run -p 8000:8000 travel-mcp-server

# Run with docker-compose (including monitoring)
docker-compose --profile monitoring up -d
```

### 5.2 Environment Variables for Production

Set `USE_MOCK_DATA=false` and configure real API keys:

```bash
TRAVEL_USE_MOCK_DATA=false
TRAVEL_WEATHER_API_KEY=your-weather-api-key
TRAVEL_AMAP_API_KEY=your-amap-api-key
TRAVEL_API_KEY=your-secure-api-key
```

## 6. API Endpoints

| Method | Endpoint                   | Description                   |
| ------ | -------------------------- | ----------------------------- |
| GET    | /health                    | Full health check             |
| GET    | /health/live               | Liveness probe                |
| GET    | /health/ready              | Readiness probe               |
| GET    | /metrics                   | Prometheus metrics            |
| POST   | /api/v1/tools/{tool\_name} | Direct tool call              |
| GET    | /sse                       | SSE endpoint for MCP protocol |
| POST   | /messages                  | MCP protocol messages         |

