# EasyProxy — Kế hoạch triển khai (Implementation Plan)

## Phases overview

```
Phase 1: Foundation    ─── US-001, US-002, US-003
         │
Phase 2: Basic Proxy   ─── US-004, US-005, US-006, US-007
         │
Phase 3: Auto + Desktop ─── US-008, US-009, US-010, US-011, US-012, US-013, US-014
         │
Phase 4: Residential   ─── US-015, US-016, US-017, US-018, US-019, US-020
```

---

## Phase 1: Foundation

### US-001: Project Skeleton

**Description:** Set up Python project structure, dependency management, configuration system, logging framework, and CLI entrypoint.

**Dependencies:** None  
**Effort:** S (Small)  
**Files created:**
- `pyproject.toml` / `requirements.txt`
- `easyproxy/__init__.py`
- `easyproxy/cli.py` — CLI entrypoint
- `easyproxy/config.py` — Configuration loader (YAML/JSON)
- `easyproxy/logging.py` — Logging setup (structlog / standard logging)
- `easyproxy/database.py` — SQLite connection manager, migration runner
- `easyproxy/migrations/001_initial.sql`
- `tests/conftest.py` — Test fixtures

**Acceptance criteria:**
- [x] `python -m easyproxy` prints help message
- [x] Configuration loads from `~/.easyproxy/config.json` or defaults
- [x] Logging writes to `~/.easyproxy/logs/easyproxy.log`
- [x] Database initializes with all tables on first run
- [x] All existing tests pass (placeholder: at minimum `test_import` and `test_config`)

### US-002: Backend Foundation

**Description:** Set up FastAPI server with health check, WebSocket endpoint, CORS, and initial route structure.

**Dependencies:** US-001  
**Effort:** S  
**Files created:**
- `easyproxy/api/__init__.py`
- `easyproxy/api/app.py` — FastAPI app factory
- `easyproxy/api/routes/health.py`
- `easyproxy/api/routes/ws.py` — WebSocket handler
- `easyproxy/api/middleware.py` — Error handling, CORS, request ID

**Acceptance criteria:**
- [x] `GET /health` returns 200 with version and uptime
- [x] `GET /docs` serves Swagger UI
- [x] WebSocket at `/ws` accepts connections and sends keepalive pings
- [x] CORS allows any origin (local use only)
- [x] All error responses follow RFC 7807 format

### US-003: Forward Proxy Core

**Description:** Implement the HTTP forward proxy engine on asyncio — handle HTTP requests and CONNECT tunnels.

**Dependencies:** US-001  
**Effort:** L (Large)  
**Files created:**
- `easyproxy/proxy/__init__.py`
- `easyproxy/proxy/server.py` — asyncio server, HTTP protocol handler
- `easyproxy/proxy/connect.py` — CONNECT tunnel handler
- `easyproxy/proxy/upstream.py` — Upstream proxy connector
- `easyproxy/proxy/headers.py` — Header sanitization
- `easyproxy/proxy/middleware.py` — Logging, stats collection middleware

**Acceptance criteria:**
- [x] Proxy listens on configurable port (default 8080)
- [x] HTTP GET requests are forwarded to upstream proxy and response returned
- [x] HTTPS via CONNECT tunnel works (tested with `curl -x`)
- [x] Headers are sanitized (X-Forwarded-For, Via, etc.)
- [x] Basic auth support for upstream proxies
- [x] 502 Bad Gateway returned when upstream is unreachable
- [x] Request is logged to `request_log` table

---

## Phase 2: Basic Proxy

### US-004: Static Proxy CRUD

**Description:** Full CRUD API + database operations for static proxy management.

**Dependencies:** US-001, US-002  
**Effort:** S  
**Files created:**
- `easyproxy/api/routes/pool.py`
- `easyproxy/pool/manager.py` — Pool manager logic
- `easyproxy/pool/models.py` — Pydantic models

**Acceptance criteria:**
- [x] `GET /api/v1/pool` returns paginated list with filters
- [x] `POST /api/v1/pool` adds proxy with validation (duplicate check)
- [x] `PUT /api/v1/pool/{id}` updates proxy fields
- [x] `DELETE /api/v1/pool/{id}` removes proxy
- [x] `GET /api/v1/pool/stats` returns pool statistics

### US-005: Proxy Import

**Description:** Import proxies from file (TXT, CSV) and clipboard paste.

**Dependencies:** US-004  
**Effort:** S  
**Files created:**
- `easyproxy/pool/importer.py` — File parsers

**Acceptance criteria:**
- [x] TXT format: `ip:port` per line
- [x] CSV format: `ip,port,protocol,username,password,region`
- [x] Duplicates skipped, invalid lines reported
- [x] `POST /api/v1/pool/import` returns count of imported/skipped/errors

### US-006: Proxy Health Check

**Description:** Background health check system — test proxies, measure latency, mark dead/alive.

**Dependencies:** US-004  
**Effort:** M (Medium)  
**Files created:**
- `easyproxy/pool/health.py` — Health check runner
- `easyproxy/tasks/health_scheduler.py` — Background task

**Acceptance criteria:**
- [x] Health check runs on configurable interval (default 60s)
- [x] Test via HEAD request to `test_url` (configurable)
- [x] Latency measured and stored
- [x] Dead proxy detection: 3 consecutive failures → mark dead
- [x] Dead proxies retested on next cycle (cooldown)
- [x] Alive proxies sorted by latency for low-latency-first strategy
- [x] `POST /api/v1/pool/test` triggers immediate test

### US-007: Manual Rotation

**Description:** Manual rotate API — switch to next IP on demand.

**Dependencies:** US-003, US-004  
**Effort:** S  
**Files created:**
- `easyproxy/rotation/engine.py` — Rotation engine
- `easyproxy/api/routes/proxy.py`

**Acceptance criteria:**
- [x] `POST /api/v1/proxy/rotate` picks next proxy from alive pool
- [x] Rotation strategy respected (round-robin initially)
- [x] Rotation logged to `rotation_log`
- [x] WebSocket event emitted on rotation
- [x] If no alive proxies, returns 503

---

## Phase 3: Auto + Desktop

### US-008: Auto-detect Rate Limit

**Description:** Detect HTTP 429 responses, auto-rotate IP, retry request.

**Dependencies:** US-003, US-007  
**Effort:** M  
**Files modified:**
- `easyproxy/proxy/middleware.py` — Add rate limit detection
- `easyproxy/rotation/engine.py` — Add auto-rotate flow
- `easyproxy/api/routes/proxy.py` — Add rotation history endpoint

**Acceptance criteria:**
- [x] HTTP 429 response triggers rate limit detection
- [x] `Retry-After` header parsed and respected
- [x] Auto-rotate: new IP selected (excluding current), request retried
- [x] Max retry attempts configurable (default 3)
- [x] Rotation logged with reason `rate_limit_429`
- [x] WebSocket event `rate_limit_detected` emitted
- [x] If all proxies exhausted for retry, return original 429 to client

### US-009: Scheduled Rotation

**Description:** Schedule automatic rotation at fixed intervals.

**Dependencies:** US-007  
**Effort:** S  
**Files created:**
- `easyproxy/tasks/rotation_scheduler.py`

**Acceptance criteria:**
- [x] Configurable interval (minutes)
- [x] Enabled/disabled via settings
- [x] Rotation logged with reason `scheduled`
- [x] Current in-flight requests complete before rotation

### US-010: Sticky Session

**Description:** Maintain same proxy for same domain within TTL.

**Dependencies:** US-007  
**Effort:** M  
**Files created:**
- `easyproxy/proxy/sticky.py` — Sticky session manager

**Acceptance criteria:**
- [x] Requests to same hostname use same proxy within TTL
- [x] TTL configurable (default 300s)
- [x] On 429 error, sticky binding cleared (if `reset_on_error`)
- [x] Manual rotation clears sticky binding for that domain
- [x] Sticky cache is thread-safe (asyncio.Lock)

### US-011: Electron Shell

**Description:** Electron main process with system tray, window management, auto-updater.

**Dependencies:** US-002  
**Effort:** L  
**Files created:**
- `electron/main.js` — Main process
- `electron/preload.js` — Preload script (IPC bridge)
- `electron/tray.js` — System tray management
- `electron/updater.js` — Auto-update config
- `package.json` — Electron + Nuxt dependencies

**Acceptance criteria:**
- [x] Window loads Nuxt frontend
- [x] System tray icon with context menu (Start/Stop, Rotate, Show, Quit)
- [x] Minimize to tray on close
- [x] Spawns Python backend as child process
- [x] Waits for `/health` before loading UI
- [x] Restarts Python process if it crashes
- [x] Auto-update via electron-updater

### US-012: System Proxy Config

**Description:** Auto-configure OS system proxy settings on start/stop.

**Dependencies:** US-011  
**Effort:** M  
**Files created:**
- `electron/system-proxy.js` — OS-specific proxy configuration

**Acceptance criteria:**
- [x] macOS: Set via `networksetup -setwebproxy` / `-setsecurewebproxy`
- [x] Windows: Set via WinHTTP / registry
- [x] Linux: Set via gsettings (GNOME) or environment variables
- [x] Restore original proxy settings on stop/quit
- [x] Handle permission errors gracefully (fallback: manual config prompt)

### US-013: Dashboard UI

**Description:** Build dashboard screen with proxy status, stats, quick actions.

**Dependencies:** US-002, US-011  
**Effort:** M  
**Files created:**
- `packages/ui/components/DashboardPage.vue`
- `packages/ui/components/ProxyStatusCard.vue`
- `packages/ui/components/StatsGrid.vue`
- `packages/ui/components/RequestTimelineChart.vue`
- `packages/ui/components/RecentLogsList.vue`

**Acceptance criteria:**
- [x] Proxy running/stopped status visible
- [x] Current IP displayed
- [x] Stats: requests, rate limits, rotations — real-time via WebSocket
- [x] Quick actions: Start/Stop toggle, Rotate button
- [x] Recent logs auto-scroll
- [x] Green/grey status indicator

### US-014: Proxy Manager UI

**Description:** Build proxy manager screen with table, CRUD modals, import.

**Dependencies:** US-004, US-005, US-011, US-013  
**Effort:** M  
**Files created:**
- `packages/ui/components/ProxyManagerPage.vue`
- `packages/ui/components/ProxyTable.vue`
- `packages/ui/components/ProxyFormModal.vue`
- `packages/ui/components/ImportPreviewModal.vue`

**Acceptance criteria:**
- [x] Table displays all proxies with sortable columns
- [x] Add/Edit modal with validation
- [x] Delete with confirmation dialog
- [x] Import file picker + preview
- [x] Test All button with progress
- [x] Status indicators (alive/dead/untested)

---

## Phase 4: Residential + Polish

### US-015: Residential Provider Integration

**Description:** Integrate with BrightData/Oxylabs/Smartproxy API for residential IP pool.

**Dependencies:** US-004, US-007  
**Effort:** L  
**Files created:**
- `easyproxy/residential/__init__.py`
- `easyproxy/residential/brightdata.py` — BrightData adapter
- `easyproxy/residential/oxylabs.py` — Oxylabs adapter
- `easyproxy/residential/smartproxy.py` — Smartproxy adapter
- `easyproxy/residential/base.py` — Abstract provider base
- `easyproxy/api/routes/residential.py`

**Acceptance criteria:**
- [x] Provider config saved to `residential_config` table
- [x] API key verified on save
- [x] Pool refresh fetches IPs from provider and adds to `proxies` table
- [x] Dead IPs rotated via provider API
- [x] Connection status displayed in UI
- [x] At least BrightData integration works end-to-end
- [x] Provider abstraction allows easy addition of new providers

### US-016: Auto-refresh Pool

**Description:** Background task that periodically refreshes residential pool and prunes dead proxies.

**Dependencies:** US-015  
**Effort:** S  
**Files created:**
- `easyproxy/tasks/pool_refresh.py`

**Acceptance criteria:**
- [x] Residential pool refreshed on configurable interval
- [x] Dead static proxies automatically removed after N consecutive failures
- [x] Pool stats updated in real-time
- [x] Pruning respects minimum pool size (configurable)

### US-017: CLI Mode

**Description:** Run EasyProxy as a headless CLI application (no Electron).

**Dependencies:** US-002, US-003  
**Effort:** S  
**Files created:**
- `easyproxy/cli/proxy.py` — Start/stop proxy from CLI
- `easyproxy/cli/pool.py` — Pool management commands
- `easyproxy/cli/rotate.py` — Rotation commands

**Acceptance criteria:**
- [x] `easyproxy start` starts proxy + backend
- [x] `easyproxy stop` stops gracefully
- [x] `easyproxy status` prints current state
- [x] `easyproxy pool list/add/remove/import/export` works
- [x] `easyproxy rotate` triggers manual rotation
- [x] CLI runs without Electron installed

### US-018: Logs & Monitoring

**Description:** Log viewer UI with filtering, export, rotation history.

**Dependencies:** US-003, US-007, US-013  
**Effort:** M  
**Files created:**
- `packages/ui/components/LogsPage.vue`
- `packages/ui/components/LogFilterBar.vue`
- `packages/ui/components/LogTable.vue`
- `packages/ui/components/RotationHistoryTable.vue`
- `easyproxy/api/routes/logs.py`

**Acceptance criteria:**
- [x] Request log table with virtual scrolling
- [x] Filter by date range, method, status code, proxy
- [x] Rotation history tab with details
- [x] CSV export of filtered logs
- [x] Live tail toggle (auto-scroll new entries)
- [x] Log retention enforced (max_entries)

### US-019: Notifications

**Description:** OS notifications and in-app toasts for important events.

**Dependencies:** US-008, US-011  
**Effort:** S  
**Files created:**
- `packages/ui/components/NotificationToast.vue`
- `electron/notifications.js` — Native notification bridge

**Acceptance criteria:**
- [x] Rate limit detected → OS notification (when minimized)
- [x] Rotation completed → toast (when focused)
- [x] Proxy dead → warning toast
- [x] Errors → persistent error toast
- [x] Notification preferences in Settings

### US-020: Auto-start

**Description:** App auto-starts with OS login.

**Dependencies:** US-011  
**Effort:** S  
**Files created:**
- `electron/auto-launch.js`

**Acceptance criteria:**
- [x] Toggle in Settings: "Auto-start with system"
- [x] macOS: registered as Login Item
- [x] Windows: registered in Run registry
- [x] Linux: .desktop file in autostart directory
- [x] Starts minimized to tray

---

## Dependency graph

```
US-001 (Skeleton)
 ├── US-002 (Backend)
 │    ├── US-011 (Electron)
 │    │    ├── US-012 (System Proxy)
 │    │    ├── US-013 (Dashboard UI)
 │    │    │    └── US-014 (Proxy Manager UI)
 │    │    ├── US-019 (Notifications)
 │    │    └── US-020 (Auto-start)
 │    ├── US-004 (Proxy CRUD)
 │    │    ├── US-005 (Import)
 │    │    ├── US-006 (Health Check)
 │    │    └── US-015 (Residential)
 │    │         └── US-016 (Auto-refresh)
 │    └── US-007 (Manual Rotation)
 │         ├── US-008 (Auto-detect 429)
 │         ├── US-009 (Scheduled Rotation)
 │         └── US-010 (Sticky Session)
 ├── US-003 (Proxy Engine)
 │    ├── US-007 (Manual Rotation) ←—— waits for proxy + pool
 │    └── US-008 (Auto Detect) ←—— waits for rotation engine
 └── US-017 (CLI Mode) ←—— independent
```

**Parallelizable groups:**
- Group A: US-003 (Proxy Engine) + US-004 (Pool CRUD) — can build in parallel after US-001
- Group B: US-005 (Import) + US-006 (Health Check) — can build after US-004
- Group C: US-009 (Scheduled) + US-010 (Sticky Session) — can build after US-007
- Group D: US-013 (Dashboard) + US-014 (Proxy Manager) + US-018 (Logs) — can build after US-011

## Effort summary

| Phase | Stories | Total effort |
|-------|---------|-------------|
| Phase 1 — Foundation | 3 | S + S + L |
| Phase 2 — Basic Proxy | 4 | S + S + M + S |
| Phase 3 — Auto + Desktop | 7 | M + S + M + L + M + M + M |
| Phase 4 — Residential | 6 | L + S + S + M + S + S |
| **Total** | **20** | **~20 weeks (1 dev)** |

## Testing strategy

| Type | Tool | Target |
|------|------|--------|
| Unit tests | pytest | All business logic, rotation engine, pool manager |
| API tests | httpx | All REST endpoints |
| Proxy tests | aiohttp test client | Proxy engine with mock upstream |
| E2E tests | Playwright + Electron | Full desktop flow |
| Load tests | locust | Proxy engine throughput |
