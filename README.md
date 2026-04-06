# Travel Agent MCP Server

A Model Context Protocol (MCP) server providing travel-related tools for AI agents.

## Features

- **Weather Query** - Get weather forecasts for cities worldwide
- **Product Search** - Search travel products (luggage, adapters, accessories)
- **Tourist Attractions** - Find attractions by destination and interest tags
- **Hotel Search** - Search hotels with dates and guest count
- **Flight Search** - Find flights between airports

## Quick Start

```bash
# Install dependencies
uv sync

# Run server (uses mock data by default)
uv run python -m travel_mcp.main
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
TRAVEL_USE_MOCK_DATA=true      # Use mock data (default: true)
TRAVEL_API_KEY=your-api-key    # Optional API key
TRAVEL_PORT=8000               # Server port
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/health/live` | GET | Liveness probe |
| `/health/ready` | GET | Readiness probe |
| `/metrics` | GET | Prometheus metrics |
| `/api/v1/tools/{name}` | POST | Call a tool |

## Docker

```bash
# Build and run
docker build -t travel-mcp-server .
docker run -p 8000:8000 travel-mcp-server

# Or use docker-compose
docker-compose up -d
```

## Development

```bash
# Run tests
uv run pytest

# Run with hot reload
uv run uvicorn travel_mcp.main:create_app --factory --reload
```

## License

MIT
