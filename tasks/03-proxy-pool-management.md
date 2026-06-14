# EasyProxy — Tasks: Proxy Pool Management

> Feature 3: US-004, US-005, US-006

---

## US-004: Static Proxy CRUD

### Task 4.1: Implement Pydantic models

- [ ] Tạo `easyproxy/pool/models.py` — `ProxyCreate`, `ProxyUpdate`, `ProxyResponse` schemas
- [ ] Validation: `address` format (IP:port), protocol enum (http/https/socks5)
- [ ] Optional fields: `username`, `password`, `region`, `notes`

**Files:** `easyproxy/pool/__init__.py`, `easyproxy/pool/models.py`
**Effort:** S
**Dependencies:** Task 1.1
**Verify:** Pydantic validation hoạt động

### Task 4.2: Implement pool manager

- [ ] Tạo `easyproxy/pool/manager.py` — CRUD operations cho `proxies` table
- [ ] `add()` — insert, duplicate check (IP:port unique)
- [ ] `get()` — get by ID
- [ ] `list()` — paginated, filterable (protocol, region, alive status)
- [ ] `update()` — update fields
- [ ] `remove()` — delete by ID
- [ ] `stats()` — count by status/protocol, alive/dead ratio

**Files:** `easyproxy/pool/manager.py`
**Effort:** M
**Dependencies:** Task 1.4
**Verify:** CRUD operations hoạt động với SQLite

### Task 4.3: Implement pool CRUD API routes

- [ ] Tạo `easyproxy/api/routes/pool.py`
- [ ] `GET /api/v1/pool` — list (query params: page, per_page, protocol, region, alive)
- [ ] `POST /api/v1/pool` — add (validate + duplicate check)
- [ ] `PUT /api/v1/pool/{id}` — update
- [ ] `DELETE /api/v1/pool/{id}` — remove
- [ ] `GET /api/v1/pool/stats` — pool statistics

**Files:** `easyproxy/api/routes/pool.py`
**Effort:** S
**Dependencies:** Task 4.2, Task 2.1
**Verify:** CRUD qua API hoạt động

### Task 4.4: Pool CRUD tests

- [ ] Tạo `tests/test_pool_crud.py`
- [ ] Test add/get/list/update/delete proxy
- [ ] Test duplicate detection
- [ ] Test pagination + filters

**Files:** `tests/test_pool_crud.py`
**Effort:** S
**Dependencies:** Task 4.1–4.3
**Verify:** `pytest tests/test_pool_crud.py` passes

---

## US-005: Proxy Import

### Task 5.1: Implement TXT file parser

- [ ] Tạo `easyproxy/pool/importer.py`
- [ ] Parse TXT format: `ip:port` per line
- [ ] Support optional `protocol://` prefix
- [ ] Skip empty lines, comments (#)
- [ ] Return list of validated ProxyCreate objects

**Files:** `easyproxy/pool/importer.py`
**Effort:** S
**Dependencies:** Task 4.1
**Verify:** Parse TXT file → list proxies

### Task 5.2: Implement CSV file parser

- [ ] Parse CSV format: `ip,port,protocol,username,password,region`
- [ ] Header row detection (column mapping)
- [ ] Support quoted fields, different delimiters (, ; tab)
- [ ] Return list of validated ProxyCreate objects
- [ ] Report parse errors per line (continue on error)

**Files:** `easyproxy/pool/importer.py`
**Effort:** S
**Dependencies:** Task 4.1
**Verify:** Parse CSV file → list proxies

### Task 5.3: Implement import API endpoint

- [ ] `POST /api/v1/pool/import` — accept file upload (multipart) or JSON body with proxy strings
- [ ] Detect format from file extension (.txt, .csv)
- [ ] Batch insert with duplicate detection
- [ ] Return: `{imported: 10, skipped: 2, errors: [{line: 5, reason: "invalid format"}]}`
- [ ] Also support clipboard paste (plain text input)

**Files:** `easyproxy/api/routes/pool.py`
**Effort:** S
**Dependencies:** Task 5.1, 5.2, Task 4.3
**Verify:** Upload file → proxies imported

### Task 5.4: Import tests

- [ ] Tạo `tests/test_pool_import.py`
- [ ] Test TXT parsing
- [ ] Test CSV parsing
- [ ] Test API import endpoint
- [ ] Test duplicate handling
- [ ] Test error reporting

**Files:** `tests/test_pool_import.py`
**Effort:** S
**Dependencies:** Task 5.1–5.3
**Verify:** `pytest tests/test_pool_import.py` passes

---

## US-006: Proxy Health Check

### Task 6.1: Implement health check runner

- [ ] Tạo `easyproxy/pool/health.py`
- [ ] Test single proxy: HEAD request to `https://httpbin.org/ip` (configurable test URL)
- [ ] Measure latency (connect + response time)
- [ ] Detect alive/dead (3 consecutive failures = dead)
- [ ] Store results: `alive`, `latency_ms`, `last_check` timestamp
- [ ] Thread-safe (aiosqlite connection per task)

**Files:** `easyproxy/pool/health.py`
**Effort:** M
**Dependencies:** Task 4.2
**Verify:** Test single proxy → latency recorded

### Task 6.2: Implement background scheduler

- [ ] Tạo `easyproxy/tasks/health_scheduler.py`
- [ ] Run health check on configurable interval (default 60s)
- [ ] Process proxies in batches (configurable concurrency, default 10)
- [ ] Dead proxies retested on next cycle (cooldown)
- [ ] Graceful shutdown (wait for in-progress checks)
- [ ] Log results, emit WebSocket event when proxy status changes

**Files:** `easyproxy/tasks/__init__.py`, `easyproxy/tasks/health_scheduler.py`
**Effort:** M
**Dependencies:** Task 6.1, Task 2.3
**Verify:** Background health check runs tự động

### Task 6.3: Implement test API endpoint

- [ ] `POST /api/v1/pool/test` — trigger immediate health check for all proxies
- [ ] Return progress via WebSocket (`health_check_progress`)
- [ ] `POST /api/v1/pool/test/{id}` — test single proxy
- [ ] Non-blocking: start check in background, return `accepted`

**Files:** `easyproxy/api/routes/pool.py`
**Effort:** S
**Dependencies:** Task 6.1, Task 2.3
**Verify:** `POST /api/v1/pool/test` triggers check, results returned

### Task 6.4: Health check tests

- [ ] Tạo `tests/test_pool_health.py`
- [ ] Test single proxy health check (mock upstream)
- [ ] Test dead proxy detection
- [ ] Test background scheduler
- [ ] Test API endpoint

**Files:** `tests/test_pool_health.py`
**Effort:** M
**Dependencies:** Task 6.1–6.3
**Verify:** `pytest tests/test_pool_health.py` passes
