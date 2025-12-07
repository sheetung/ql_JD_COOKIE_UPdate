# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based JD_COOKIE management system that integrates with Qinglong Panel (青龙面板) via its open API. The application provides a web interface for querying and updating JD_COOKIE environment variables, with built-in IP-based rate limiting.

## Architecture

**Single-file Flask application** (`app.py`):
- All API endpoints, authentication, and business logic in one file
- Token caching with automatic refresh mechanism (`get_ql_token()`)
- Custom decorator-based IP rate limiting (`limit_ip_access`)
- Static file serving for frontend HTML pages

**Qinglong Panel Integration**:
- Uses OAuth-style authentication with CLIENT_ID and CLIENT_SECRET
- Token is cached globally and auto-refreshed before expiration
- All operations interact with `/open/envs` endpoints
- Searches for environment variables by pt_pin (京东账号标识)

**Rate Limiting Design**:
- In-memory dictionary stores IP access counts (resets do not persist across restarts)
- Daily limit of 7 requests per IP (configurable via `MAX_DAILY_ACCESS`)
- Decorator automatically injects remaining count into JSON responses
- Returns HTTP 429 with countdown when limit exceeded

## Environment Variables

Required for operation:
- `QL_HOST`: Qinglong Panel URL (e.g., http://192.168.192.37:5789)
- `CLIENT_ID`: Qinglong Open API Client ID
- `CLIENT_SECRET`: Qinglong Open API Client Secret

Optional configuration:
- `MAX_DAILY_ACCESS`: Maximum requests per IP per day (default: 7)
- `BACKGROUND_IMAGE_URL`: Background image URL for the frontend (default: https://t.alcy.cc/ycy)

## Development Commands

**Local development**:
```sh
pip install -r requirements.txt
python app.py  # Runs on 0.0.0.0:8080 with debug=True
```

**Docker deployment**:
```sh
# Using docker-compose (recommended)
cp docker-compose.yaml.example docker-compose.yaml
# Edit docker-compose.yaml with your configuration
docker-compose up -d

# Or manual docker run
docker build -t jdupdate .
docker run -p 8080:8080 \
  -e QL_HOST=http://your-qinglong-host:5789 \
  -e CLIENT_ID=your-client-id \
  -e CLIENT_SECRET=your-client-secret \
  -e MAX_DAILY_ACCESS=7 \
  -e BACKGROUND_IMAGE_URL=https://t.alcy.cc/ycy \
  jdupdate
```

## API Endpoints

- `GET /`: Serves the main UI (jdupdate.html)
- `GET /api/config`: Returns frontend configuration (background image URL, etc.)
- `GET /api/envs`: Proxy to Qinglong's environment variable list (no rate limit)
- `GET /api/jdcookie/query?ptpin=<value>`: Query JD_COOKIE by pt_pin (rate limited)
- `POST /api/jdcookie/update`: Update and enable JD_COOKIE (rate limited, requires JSON body with "value")

**Update endpoint behavior**:
- Extracts pt_pin from the new cookie value via regex
- Finds existing environment variable by pt_pin
- Returns early if already enabled (status=0)
- Updates the value AND enables the variable in two API calls

## Key Implementation Details

**Configuration** (app.py:13-15):
- `MAX_DAILY_ACCESS`: Configurable via environment variable (default: 7)
- `BACKGROUND_IMAGE_URL`: Configurable via environment variable (default: https://t.alcy.cc/ycy)

**Token management** (app.py:96-108):
- Global variables `_cached_token` and `_token_expire_time`
- Refreshes 60 seconds before expiration
- No thread safety (single-threaded Flask development server)

**pt_pin extraction** (app.py:186-189):
- Regex pattern: `r"pt_pin=([^;]+);?"`
- Used to match cookies across different formats

**Status codes**:
- Qinglong API returns 200 in response body, not HTTP status
- Check `data.get("code")` not `response.status_code`
- Status field: 0=enabled, 1=disabled

## Common Issues

- SSL verification is disabled (`verify=False`) for all Qinglong API requests
- IP address tracking will reset if app restarts (in-memory only)
- The rate limiter decorator modifies response JSON after function execution
- Timeout is set to 10 seconds for all external requests
