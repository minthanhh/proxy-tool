# EasyProxy — API Specifications

**Base URL:** `http://127.0.0.1:8000`  
**Content-Type:** `application/json`  
**Auth:** None (localhost-only; may add API key for remote access later)

---

## General

### `GET /health`

Health check endpoint.

**Response `200`:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "uptime_seconds": 3600,
  "proxy_running": true,
  "pool": {
    "total": 25,
    "alive": 22,
    "dead": 3
  }
}
```

---

## Proxy Control

### `GET /api/v1/proxy/status`

Get current proxy status.

**Response `200`:**
```json
{
  "running": true,
  "port": 8080,
  "current_proxy_id": 12,
  "current_proxy": "45.67.89.10:3128",
  "current_proxy_country": "US",
  "strategy": "round-robin",
  "sticky_session": true,
  "uptime_seconds": 1800,
  "requests_served": 1523,
  "rate_limits_detected": 7,
  "rotations_performed": 9,
  "bytes_sent": 1048576,
  "bytes_received": 52428800
}
```

### `POST /api/v1/proxy/start`

Start proxy engine.

**Request body:**
```json
{
  "port": 8080,
  "auto_configure_system_proxy": true
}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Proxy started on port 8080",
  "system_proxy_configured": true
}
```

**Errors:** `409` — Already running; `400` — Port in use.

### `POST /api/v1/proxy/stop`

Stop proxy engine.

**Response `200`:**
```json
{
  "success": true,
  "message": "Proxy stopped",
  "system_proxy_restored": true
}
```

**Errors:** `409` — Not running.

### `POST /api/v1/proxy/rotate`

Manually rotate to next IP.

**Request body:** _(optional)_
```json
{
  "sticky_domain": null
}
```

**Response `200`:**
```json
{
  "success": true,
  "previous_proxy_id": 12,
  "previous_proxy": "45.67.89.10:3128",
  "current_proxy_id": 15,
  "current_proxy": "98.76.54.32:8080",
  "reason": "manual"
}
```

**Errors:** `409` — Proxy not running.

---

## Pool Management

### `GET /api/v1/pool`

List all proxies in pool.

**Query params:** `?status=alive&protocol=http&search=45.67&page=1&per_page=50`

**Response `200`:**
```json
{
  "total": 100,
  "page": 1,
  "per_page": 50,
  "proxies": [
    {
      "id": 1,
      "address": "45.67.89.10",
      "port": 3128,
      "protocol": "http",
      "username": null,
      "password": null,
      "region": "US",
      "status": "alive",
      "latency_ms": 230,
      "last_checked_at": "2026-06-14T10:00:00Z",
      "source": "manual",
      "residential_provider": null,
      "error_count": 0,
      "success_count": 45,
      "created_at": "2026-06-10T08:00:00Z"
    }
  ]
}
```

### `POST /api/v1/pool`

Add a proxy to pool.

**Request body:**
```json
{
  "address": "45.67.89.10",
  "port": 3128,
  "protocol": "http",
  "username": null,
  "password": null,
  "region": "US",
  "source": "manual"
}
```

**Response `201`:**
```json
{
  "success": true,
  "proxy_id": 101
}
```

**Errors:** `409` — Duplicate (same address:port), `422` — Validation error.

### `DELETE /api/v1/pool/{id}`

Remove a proxy from pool.

**Response `200`:**
```json
{
  "success": true,
  "message": "Proxy #101 deleted"
}
```

**Errors:** `404` — Not found.

### `PUT /api/v1/pool/{id}`

Update a proxy.

**Request body:** (partial update)
```json
{
  "region": "GB",
  "username": "newuser"
}
```

**Response `200`:**
```json
{
  "success": true,
  "proxy_id": 101
}
```

### `POST /api/v1/pool/test`

Test all proxies (or specific ones).

**Request body:** _(optional — if empty, test all)_
```json
{
  "proxy_ids": [1, 2, 3],
  "test_url": "http://httpbin.org/ip"
}
```

**Response `200`:** (streaming via WebSocket or long-poll fallback)
```json
{
  "started": true,
  "total": 50,
  "completed": 0
}
```

Results arrive via WebSocket events.

### `POST /api/v1/pool/import`

Import proxies from file content.

**Request body:**
```json
{
  "format": "txt",
  "content": "45.67.89.10:3128\n98.76.54.32:8080\n",
  "protocol": "http",
  "region": null,
  "replace": false
}
```

Or:
```json
{
  "format": "csv",
  "content": "ip,port,protocol,username,password,region\n45.67.89.10,3128,http,,,US\n",
  "replace": true
}
```

**Response `200`:**
```json
{
  "success": true,
  "imported": 50,
  "skipped": 3,
  "errors": ["Line 4: invalid format"]
}
```

### `GET /api/v1/pool/stats`

Pool statistics.

**Response `200`:**
```json
{
  "total": 100,
  "alive": 85,
  "dead": 15,
  "by_protocol": {
    "http": 60,
    "https": 30,
    "socks5": 10
  },
  "by_region": {
    "US": 40,
    "GB": 15,
    "DE": 10,
    "unknown": 35
  },
  "average_latency_ms": 280,
  "median_latency_ms": 210
}
```

---

## Residential Proxy

### `GET /api/v1/residential/config`

Get residential proxy configuration.

**Response `200`:**
```json
{
  "provider": "brightdata",
  "api_key": "sk-...****",
  "zone": "residential",
  "country": "us",
  "pool_size": 50,
  "active_ips": 42,
  "connected": true,
  "expires_at": "2026-07-14T00:00:00Z"
}
```

### `PUT /api/v1/residential/config`

Set / update residential proxy configuration.

**Request body:**
```json
{
  "provider": "brightdata",
  "api_key": "sk-abc123",
  "zone": "residential-static",
  "country": "us",
  "sticky_ip": true
}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Residential config updated",
  "pool_refreshed": true
}
```

### `POST /api/v1/residential/refresh`

Refresh residential pool — fetch new IPs from provider.

**Request body:** _(optional override)_
```json
{
  "count": 100
}
```

**Response `200`:**
```json
{
  "success": true,
  "previous_count": 42,
  "new_count": 55,
  "added": 15,
  "removed": 2
}
```

---

## Settings

### `GET /api/v1/settings`

Get all settings.

**Response `200`:**
```json
{
  "general": {
    "auto_start": false,
    "minimize_to_tray": true,
    "theme": "system"
  },
  "proxy": {
    "port": 8080,
    "auto_configure_system_proxy": true,
    "bind_address": "127.0.0.1"
  },
  "rotation": {
    "strategy": "round-robin",
    "schedule_enabled": false,
    "schedule_interval_minutes": 10,
    "auto_rotate_on_429": true,
    "retry_attempts": 3
  },
  "sticky_session": {
    "enabled": true,
    "ttl_seconds": 300,
    "reset_on_error": true
  },
  "logs": {
    "max_entries": 10000,
    "log_level": "info"
  },
  "health_check": {
    "interval_seconds": 60,
    "test_url": "http://httpbin.org/ip",
    "timeout_seconds": 10
  }
}
```

### `PUT /api/v1/settings`

Update settings. Partial updates allowed.

**Request body:**
```json
{
  "general": {
    "auto_start": true
  },
  "rotation": {
    "strategy": "random"
  }
}
```

**Response `200`:**
```json
{
  "success": true,
  "applied": ["general.auto_start", "rotation.strategy"]
}
```

**Errors:** `422` — Invalid value for field.

---

## Logs

### `GET /api/v1/proxy/logs`

Get request logs.

**Query params:** `?page=1&per_page=100&status=429&method=GET&proxy_id=12&since=2026-06-13T00:00:00Z&until=2026-06-14T00:00:00Z`

**Response `200`:**
```json
{
  "total": 5000,
  "page": 1,
  "per_page": 100,
  "logs": [
    {
      "id": 1,
      "timestamp": "2026-06-14T10:00:00.123Z",
      "method": "GET",
      "url": "https://api.example.com/data",
      "status_code": 200,
      "proxy_id": 12,
      "proxy_address": "45.67.89.10:3128",
      "duration_ms": 340,
      "bytes_sent": 512,
      "bytes_received": 4096,
      "user_agent": "Mozilla/5.0...",
      "rotated": false
    }
  ]
}
```

### `GET /api/v1/rotation-log`

Get rotation history.

**Query params:** `?page=1&per_page=50`

**Response `200`:**
```json
{
  "total": 15,
  "page": 1,
  "per_page": 50,
  "rotations": [
    {
      "id": 1,
      "timestamp": "2026-06-14T10:05:00Z",
      "reason": "rate_limit_429",
      "trigger": "auto",
      "from_proxy_id": 12,
      "from_proxy": "45.67.89.10:3128",
      "to_proxy_id": 15,
      "to_proxy": "98.76.54.32:8080",
      "retry_after_seconds": 30,
      "request_url": "https://api.example.com/data",
      "retry_success": true
    }
  ]
}
```

### `GET /api/v1/proxy/logs/export`

Export logs as CSV.

**Query params:** `?since=...&until=...&format=csv`

**Response `200`:** `text/csv` file download.

---

## WebSocket

### `ws://127.0.0.1:8000/ws`

Real-time event stream.

**Events (server → client):**

```json
// Proxy status
{"type": "proxy_started", "data": {"port": 8080}}
{"type": "proxy_stopped", "data": {"reason": "user"}}

// Rate limit
{"type": "rate_limit_detected", "data": {
  "request_url": "https://api.example.com/data",
  "status_code": 429,
  "retry_after_seconds": 30,
  "proxy_id": 12
}}

// Rotation
{"type": "rotation_completed", "data": {
  "reason": "rate_limit_429",
  "from_proxy": "45.67.89.10:3128",
  "to_proxy": "98.76.54.32:8080",
  "retry_success": true
}}

// Pool health
{"type": "pool_stats", "data": {
  "total": 100,
  "alive": 85,
  "dead": 15
}}

// Proxy test results
{"type": "proxy_test_result", "data": {
  "proxy_id": 1,
  "status": "alive",
  "latency_ms": 230,
  "error": null
}}

// Error
{"type": "proxy_error", "data": {
  "message": "Connection timeout to upstream",
  "proxy_id": 5,
  "severity": "warning"
}}

// Log
{"type": "request_log", "data": {
  "timestamp": "2026-06-14T10:00:00.123Z",
  "method": "GET",
  "url": "https://api.example.com/data",
  "status_code": 200,
  "duration_ms": 340
}}
```

**Client → server:**

```json
{"type": "ping"}
{"type": "subscribe", "data": {"events": ["rotation", "rate_limit"]}}
```

## Error response format

All errors follow RFC 7807 (Problem Details):

```json
{
  "type": "https://errors.easyproxy.app/proxy-already-running",
  "title": "Proxy already running",
  "status": 409,
  "detail": "Cannot start proxy: already listening on port 8080",
  "instance": "/api/v1/proxy/start"
}
```

## Summary of endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/proxy/status` | Proxy status & stats |
| POST | `/api/v1/proxy/start` | Start proxy engine |
| POST | `/api/v1/proxy/stop` | Stop proxy engine |
| POST | `/api/v1/proxy/rotate` | Manual IP rotation |
| GET | `/api/v1/pool` | List proxies |
| POST | `/api/v1/pool` | Add proxy |
| PUT | `/api/v1/pool/{id}` | Update proxy |
| DELETE | `/api/v1/pool/{id}` | Remove proxy |
| POST | `/api/v1/pool/test` | Test proxy(es) |
| POST | `/api/v1/pool/import` | Bulk import proxies |
| GET | `/api/v1/pool/stats` | Pool statistics |
| GET | `/api/v1/residential/config` | Get residential config |
| PUT | `/api/v1/residential/config` | Update residential config |
| POST | `/api/v1/residential/refresh` | Refresh residential pool |
| GET | `/api/v1/settings` | Get all settings |
| PUT | `/api/v1/settings` | Update settings |
| GET | `/api/v1/proxy/logs` | Request logs |
| GET | `/api/v1/rotation-log` | Rotation history |
| GET | `/api/v1/proxy/logs/export` | Export logs CSV |
| WS | `/ws` | Real-time events |
