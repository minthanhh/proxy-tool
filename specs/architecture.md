# EasyProxy — Kiến trúc hệ thống

## High-level architecture diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   USER APPLICATIONS                          │
│     (Browser, curl, API client, scraper, ...)                │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS (system proxy)
                     ▼
┌──────────────────────────────────────────────────────────────┐
│            ELECTRON DESKTOP SHELL (main process)              │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐              │
│  │ System   │  │  Window      │  │ System    │              │
│  │ Tray     │  │  Manager     │  │ Auto-start│              │
│  └──────────┘  └──────────────┘  └───────────┘              │
│  ┌──────────────────────────────────────────────────┐        │
│  │     Nuxt 3 Frontend (Vue 3, in BrowserWindow)    │        │
│  │  ┌──────────┐ ┌───────────┐ ┌────────────────┐  │        │
│  │  │Dashboard │ │Proxy Mgr  │ │Settings / Logs  │  │        │
│  │  └──────────┘ └───────────┘ └────────────────┘  │        │
│  └────────────────────┬────────────────────────────┘        │
└───────────────────────┼────────────────────────────────────┘
                        │ REST (localhost:8000)
                        ▼
┌──────────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND (Python, localhost:8000)         │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌────────────┐ │
│  │ REST API │ │ Rotation     │ │ Pool     │ │ Residential│ │
│  │ Server   │ │ Engine       │ │ Manager  │ │ Integrator │ │
│  └──────────┘ └──────┬───────┘ └────┬─────┘ └──────┬─────┘ │
│                       │              │               │       │
│  ┌────────────────────┴──────────────┴───────────────┴───┐  │
│  │              PROXY ENGINE (:8080)                     │  │
│  │  ┌────────────────┐ ┌──────────────┐ ┌─────────────┐ │  │
│  │  │ HTTP Forward   │ │ CONNECT      │ │ Rate Limit  │ │  │
│  │  │ Proxy          │ │ Tunnel (HTTPS)│ │ Detector    │ │  │
│  │  └───────┬────────┘ └──────┬───────┘ └──────┬──────┘ │  │
│  │          │                 │                 │        │  │
│  │  ┌───────┴─────────────────┴─────────────────┴──────┐ │  │
│  │  │           Upstream Proxy Connector                │ │  │
│  │  │   (aiohttp, upstream proxy rotation)             │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │              │               │       │
└───────────────────────┼──────────────┼───────────────┼──────┘
                        │              │               │
                        ▼              ▼               ▼
                ┌────────────┐ ┌──────────────┐ ┌────────────┐
                │  SQLite    │ │ Residential  │ │  Static    │
                │  Database  │ │ Proxy Network│ │  Proxy List│
                └────────────┘ └──────────────┘ └────────────┘
```

## Component listing

### 1. Electron Desktop Shell

| Responsibility | Chi tiết |
|----------------|----------|
| **System tray** | Icon trên khay hệ thống, menu chuột phải: Start/Stop, Rotate, Show/Hide, Quit |
| **Window management** | Tạo/destroy BrowserWindow, quản lý lifecycle (minimize to tray, restore) |
| **Auto-start** | Đăng ký launch trên system startup (login items / registry / autostart desktop file) |
| **System proxy config** | Gọi OS API để set system-wide proxy (Windows: WinHTTP, macOS: Networksetup, Linux: GNOME/gsettings) |
| **Process management** | Spawn Python backend process, monitor health, restart nếu crash |
| **Deep linking** | Xử lý `easyproxy://` protocol (optional) |
| **Updates** | Auto-update Electron app (electron-updater) |

**Tech:** Electron main process, Node.js IPC, `electron-tray` for tray, `auto-launch` for startup.

### 2. Nuxt Frontend (Vue 3)

| Responsibility | Chi tiết |
|----------------|----------|
| **Dashboard** | Proxy status card, current IP, real-time stats, quick actions |
| **Proxy Manager** | CRUD table for static proxies, import, test, search/filter |
| **Residential Config** | Provider settings, API key, connection status |
| **Settings** | Rotation strategy, schedule, theme, auto-start toggle, system proxy toggle |
| **Logs** | Virtual scrolling log table, filter by method/status/proxy, rotation history |
| **Real-time** | WebSocket connection to receive proxy events, 429 alerts, rotation notifications |

**Tech:** Nuxt 3 (Vite, SSR disabled for Electron), Vue 3 Composition API, Pinia for state, Tailwind CSS (or similar), Chart.js for stats.

### 3. FastAPI Backend

| Responsibility | Chi tiết |
|----------------|----------|
| **REST API server** | FastAPI app listening on `127.0.0.1:8000`, all endpoints under `/api/v1/` |
| **Orchestrator** | Routes commands to Proxy Engine, Rotation Engine, Pool Manager |
| **Database access** | SQLite via `aiosqlite`, models in Pydantic |
| **WebSocket** | `/ws` endpoint for real-time events (proxy status, rotation, 429) |
| **CLI entrypoint** | `python -m easyproxy.cli` — serves same FastAPI app + proxy engine without Electron |
| **Health checks** | `/health` endpoint, periodic self-check |

**Tech:** FastAPI, uvicorn, aiosqlite, Pydantic v2.

### 4. Proxy Engine

| Responsibility | Chi tiết |
|----------------|----------|
| **HTTP forward proxy** | Listen on `0.0.0.0:8080`, parse HTTP requests, forward to upstream |
| **CONNECT tunnel** | Handle `CONNECT host:port` for HTTPS, bi-directional pipe |
| **Upstream selection** | Pick proxy from pool based on rotation strategy & sticky session |
| **Rate limit detection** | Inspect upstream response for 429, extract Retry-After header |
| **Fallback chain** | If proxy fails/dead, try next in pool |
| **Connection pooling** | Reuse upstream connections via `aiohttp.TCPConnector` |

**Tech:** Python `asyncio`, `aiohttp`, custom HTTP parser for CONNECT.

### 5. Rotation Engine

| Responsibility | Chi tiết |
|----------------|----------|
| **Auto-rotate** | Triggered by Rate Limit Detector — pick new proxy, replay failed request |
| **Manual rotate** | Via API `POST /api/v1/proxy/rotate` or tray menu |
| **Scheduled rotate** | Background task running on configurable interval |
| **Sticky session** | Track `domain → proxy_id` mapping with TTL, reset on error |
| **Rotation history** | Record all rotations to database |

### 6. Proxy Pool Manager

| Responsibility | Chi tiết |
|----------------|----------|
| **Static proxy CRUD** | Add/remove/list/test proxies in SQLite |
| **Import** | Parse proxy file formats (TXT: `ip:port`, CSV: `ip,port,protocol,user,pass`) |
| **Health check** | Periodic test each proxy (HEAD request to test URL), mark dead/alive, measure latency |
| **Residential integration** | Connect to residential provider API, fetch session IPs, add to pool |
| **Pool stats** | Return alive/dead/total counts, average latency |

### 7. SQLite Database

Stored at `~/.easyproxy/easyproxy.db`. Schema in `data-model.md`.

## Data flow

```
User App (browser)                    EasyProxy
      │                                   │
      │  1. HTTP GET example.com          │
      │  ─────────────────────────────►   │
      │         (system proxy :8080)      │
      │                                   │
      │                        2. Pick upstream proxy
      │                           from pool (strategy)
      │                                   │
      │                        3. Forward request via
      │                           upstream proxy
      │                                   │
      │                           ┌───────────────┐
      │                           │ Upstream Proxy│
      │                           │  (static/     │
      │                           │  residential) │
      │                           │               │
      │                           │  4. GET       │
      │                           │  example.com  │
      │                           │  ──────────►  │
      │                           │               │
      │                           │  5. Response  │
      │                           │  ◄──────────  │
      │                           └───────────────┘
      │                                   │
      │                        6. Check for 429
      │                           If 429:
      │                             a. Log rotation
      │                             b. Pick new proxy
      │                             c. Retry (goto 3)
      │                                   │
      │  7. HTTP Response                 │
      │  ◄─────────────────────────────   │
```

## Startup sequence

```
1. User launches EasyProxy (Electron or CLI)
2. Electron:
   a. Write config to ~/.easyproxy/
   b. Spawn Python backend as child process (uvicorn)
   c. Wait for /health to return 200
   d. Create BrowserWindow → load Nuxt frontend (localhost:8000)
   e. Create system tray icon
   f. Load saved settings from SQLite
3. Python backend:
   a. Initialize SQLite (create tables if not exist)
   b. Load proxy pool from DB
   c. Load residential config (if saved)
   d. Start health check background task
   e. Start rotation scheduler (if enabled)
   f. Start Proxy Engine (listen on :8080) — **NOT auto-started, requires user action**
4. User clicks "Start" on Dashboard
5. Backend:
   a. Configure system proxy (set OS proxy to 127.0.0.1:8080)
   b. Begin accepting connections on :8080
   c. Emit WebSocket event: proxy_started
6. User clicks "Stop":
   a. Close all proxy connections
   b. Unset system proxy (restore original)
   c. Emit: proxy_stopped
```

## Communication patterns

```
┌─────────────┐          ┌──────────────┐          ┌──────────────┐
│  Nuxt       │  REST    │  FastAPI     │  IPC     │  Proxy       │
│  Frontend   │◄────────►│  Backend     │◄────────►│  Engine      │
│  (Vue 3)    │  JSON    │  :8000       │  internal │  :8080       │
└─────────────┘          └──────────────┘          └──────────────┘
       │                        │
       │  WebSocket             │  WebSocket
       │  (real-time)           │  (backend → frontend)
       └────────────────────────┘
            Events: proxy_started, proxy_stopped,
            rate_limit_detected, rotation_completed,
            proxy_error, proxy_stats

Internal IPC (Python, in-process):
  - Backend ↔ Engine: asyncio queues + direct method calls
  - Backend ↔ Pool Manager: direct calls via module imports
  - Engine → Backend: callback/event bus for 429 detection
```

**Key design decisions:**

1. **In-process proxy engine** — Not a separate process; uses asyncio tasks within the same Python process. Simpler than out-of-process, sufficient for local desktop use.
2. **Frontend-backend separation** — Even though Electron wraps the frontend, the REST API architecture allows CLI mode and remote debugging.
3. **Single port model** — Proxy on 8080, API on 8000. Frontend served via API server (static files + API routes) to avoid CORS issues in Electron.
