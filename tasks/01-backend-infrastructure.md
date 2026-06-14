# EasyProxy — Tasks: Backend Infrastructure

> Feature 1: US-001, US-002
> 
> **Project location:** Python backend at `easyproxy/` (root level, standalone, không trong Turborepo).
> Frontend Nuxt app and Electron desktop live in `apps/easyproxy-ui/`, `apps/easyproxy-desktop/` (trong pnpm workspace).

---

## US-001: Project Skeleton

### Task 1.0: Set up Python virtual environment

- [x] Kiểm tra Python 3.11+ đã cài đặt: `python3 --version`
- [x] Tạo virtual environment: `python3 -m venv .venv`
- [x] Activate venv: `source .venv/bin/activate` (macOS/Linux) hoặc `.venv\Scripts\activate` (Windows)
- [x] Nâng cấp pip: `pip install --upgrade pip`
- [x] Verify: `which python` trỏ vào `.venv/bin/python`

**Files:** `.venv/` (gitignored)
**Effort:** S
**Dependencies:** None
**Verify:** `source .venv/bin/activate && python --version` → Python 3.11+

### Task 1.1: Create Python project structure

- [x] Tạo `requirements.txt` với các dependencies:
  ```
  fastapi[standard]>=0.115.0
  aiohttp>=3.9.0
  aiosqlite>=0.20.0
  structlog>=24.1.0
  pyyaml>=6.0
  typer>=0.12.0
  httpx>=0.27.0
  pydantic>=2.0.0
  ```
- [x] Cài đặt dependencies: `source .venv/bin/activate && pip install -r requirements.txt`
- [x] Verify `fastapi[standard]` đã bao gồm uvicorn: `python -c "import uvicorn; print(uvicorn.__version__)"`
- [x] Tạo `requirements-dev.txt` cho dev dependencies:
  ```
  pytest>=8.0
  pytest-asyncio>=0.24.0
  pytest-cov>=5.0
  ```
- [x] Cài đặt dev dependencies: `pip install -r requirements-dev.txt`
- [x] Tạo `pyproject.toml` với Python 3.11+, project metadata, build system
- [x] Tạo directory layout: `easyproxy/`, `easyproxy/api/`, `easyproxy/proxy/`, `easyproxy/pool/`, `easyproxy/rotation/`, `easyproxy/residential/`, `easyproxy/cli/`, `easyproxy/tasks/`, `easyproxy/migrations/`, `tests/`
- [x] Tạo `easyproxy/__init__.py` với version string
- [x] Tạo `setup.py` cho editable install
- [x] Tạo `.gitignore` với `.venv/`, `__pycache__/`, `*.db`, `.env`
- [x] Freeze lock file: `pip freeze > requirements.lock`

**Files:** `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `.gitignore`, `easyproxy/__init__.py`
**Effort:** S
**Dependencies:** Task 1.0
**Verify:** `source .venv/bin/activate && python -c "import fastapi, uvicorn, aiohttp, aiosqlite; print('All deps OK')"`

### Task 1.2: Implement config loader

- [x] Tạo `easyproxy/config.py` — load config từ `~/.easyproxy/config.json`
- [x] Hỗ trợ default values (port 8080, db path, logging level, v.v.)
- [x] Validate config keys khi load (cảnh báo unknown keys từ file/env)
- [x] Hỗ trợ environment variable override (EXPROXY_PORT, v.v.)

**Files:** `easyproxy/config.py`
**Effort:** S
**Dependencies:** Task 1.1
**Verify:** `python -c "from easyproxy.config import load_config; print(load_config())"`

### Task 1.3: Implement logging setup

- [x] Tạo `easyproxy/logging.py` — structlog configuration
- [x] Console handler (dev) + file handler (production)
- [x] Log rotation theo size (RotatingFileHandler, 10MB, 5 backups)
- [x] Request ID middleware support (bind_request_id helper)

**Files:** `easyproxy/logging.py`
**Effort:** S
**Dependencies:** Task 1.1
**Verify:** Log output ra console + file `~/.easyproxy/logs/easyproxy.log`

### Task 1.4: Implement SQLite database manager

- [x] Tạo `easyproxy/database.py` — connection manager (aiosqlite)
- [x] Migration runner: đọc file `.sql` từ `easyproxy/migrations/`, track version trong `schema_version` table
- [x] Connection pooling / reuse for FastAPI lifespan (singleton connection per process)

**Files:** `easyproxy/database.py`
**Effort:** M
**Dependencies:** Task 1.1
**Verify:** DB initialized, migrations applied

### Task 1.5: Create initial schema migration

- [x] Tạo `easyproxy/migrations/001_initial.sql` với tất cả tables:
  - `proxies`, `residential_config`, `settings`, `rotation_log`, `request_log`, `schema_version`, `proxies_history`
- [x] Thêm indexes cho frequent queries (status, protocol, region, timestamp, host, status_code, proxy_id)
- [x] Thêm seed data cho settings table (19 config values)

**Files:** `easyproxy/migrations/001_initial.sql`
**Effort:** S
**Dependencies:** Task 1.4
**Verify:** Tables created, indexes in place

### Task 1.6: Set up test infrastructure

- [x] Tạo `tests/conftest.py` — pytest fixtures (test DB, async client, sample data)
- [x] Tạo `tests/test_config.py` — config loader tests
- [x] Tạo `tests/test_database.py` — DB init, migration tests
- [x] Tạo `pytest.ini` hoặc `pyproject.toml` pytest config

**Files:** `tests/conftest.py`, `tests/test_config.py`, `tests/test_database.py`, `pytest.ini`
**Effort:** S
**Dependencies:** Task 1.1, 1.4
**Verify:** `pytest` passes

### Task 1.7: Create CLI entrypoint

- [x] Tạo `easyproxy/__main__.py` — `python -m easyproxy` entry
- [x] Tạo `easyproxy/cli/main.py` — typer app với help text
- [x] Subcommand placeholder: `start`, `stop`, `status`, `pool`, `rotate`

**Files:** `easyproxy/__main__.py`, `easyproxy/cli/__init__.py`, `easyproxy/cli/main.py`
**Effort:** S
**Dependencies:** Task 1.1
**Verify:** `python -m easyproxy --help` in ra help message

---

## US-002: Backend Foundation (FastAPI)

### Task 2.1: Set up FastAPI app factory

- [ ] Tạo `easyproxy/api/app.py` — FastAPI app factory function
- [ ] Lifespan handler: init DB, load config, start background tasks, cleanup on shutdown
- [ ] Register all routers, middleware, exception handlers

**Files:** `easyproxy/api/__init__.py`, `easyproxy/api/app.py`
**Effort:** S
**Dependencies:** Task 1.1–1.5
**Verify:** `uvicorn easyproxy.api.app:create_app()` khởi động được

### Task 2.2: Implement health endpoint

- [ ] Tạo `easyproxy/api/routes/health.py`
- [ ] `GET /health` returns `{"status": "ok", "version": "0.1.0", "uptime": 123}`
- [ ] Include DB connection check (SELECT 1)

**Files:** `easyproxy/api/routes/__init__.py`, `easyproxy/api/routes/health.py`
**Effort:** S
**Dependencies:** Task 2.1
**Verify:** `curl http://localhost:8000/health` returns 200

### Task 2.3: Implement WebSocket handler

- [ ] Tạo `easyproxy/api/routes/ws.py`
- [ ] WebSocket at `/ws` — accepts connections, sends keepalive pings
- [ ] Event bus (in-memory asyncio.Queue) — push rotation/log events to connected clients
- [ ] Auto-disconnect on error

**Files:** `easyproxy/api/routes/ws.py`, `easyproxy/api/events.py`
**Effort:** M
**Dependencies:** Task 2.1
**Verify:** WebSocket client nhận được keepalive pings

### Task 2.4: Set up CORS middleware

- [ ] Allow origins: `localhost:3002` (Nuxt dev), `app://` (Electron)
- [ ] Allow methods: GET, POST, PUT, DELETE, OPTIONS
- [ ] Allow headers: Content-Type, Authorization

**Files:** `easyproxy/api/middleware.py` (cors)
**Effort:** S
**Dependencies:** Task 2.1
**Verify:** Frontend gọi API không bị CORS error

### Task 2.5: Implement error handling middleware

- [ ] Tạo `easyproxy/api/exceptions.py` — custom exception classes
- [ ] Exception handler: catch all, return RFC 7807 problem+json
- [ ] Request ID middleware (UUID per request)
- [ ] Request timing middleware

**Files:** `easyproxy/api/exceptions.py`, `easyproxy/api/middleware.py`
**Effort:** S
**Dependencies:** Task 2.1
**Verify:** Invalid request returns structured error

### Task 2.6: API tests

- [ ] Tạo `tests/test_api.py`
- [ ] Test health endpoint
- [ ] Test WebSocket connect/disconnect
- [ ] Test CORS headers
- [ ] Test error responses

**Files:** `tests/test_api.py`
**Effort:** S
**Dependencies:** Task 2.1–2.5
**Verify:** `pytest tests/test_api.py` passes
