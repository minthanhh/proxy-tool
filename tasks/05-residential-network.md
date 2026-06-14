# EasyProxy — Tasks: Residential Network

> Feature 5: US-015, US-016

---

## US-015: Residential Provider Integration

### Task 15.1: Implement abstract provider base class

- [ ] Tạo `easyproxy/residential/base.py`
- [ ] Abstract class `ResidentialProvider`:
  - `connect(config) → bool` — verify API key, test connection
  - `fetch_ips() → List[ProxyCreate]` — fetch available IPs
  - `rotate_ip(proxy_id) → ProxyCreate` — request new IP for specific proxy
  - `report_dead(proxy_id)` — report IP as dead to provider
  - `disconnect()` — cleanup
- [ ] Pydantic model `ResidentialConfig`: provider name, API key, options

**Files:** `easyproxy/residential/__init__.py`, `easyproxy/residential/base.py`
**Effort:** M
**Dependencies:** Task 4.1 (ProxyCreate model)
**Verify:** Base class can be instantiated

### Task 15.2: Implement BrightData adapter

- [ ] Tạo `easyproxy/residential/brightdata.py`
- [ ] Implement `ResidentialProvider` cho BrightData API
- [ ] API: `https://api.brightdata.com/`
- [ ] Auth: API token in header
- [ ] `fetch_ips()` — lấy danh sách proxy zones, IPs
- [ ] `rotate_ip()` — yêu cầu IP mới cho zone
- [ ] `report_dead()` — báo cáo IP không hoạt động
- [ ] Handle rate limits, pagination

**Files:** `easyproxy/residential/brightdata.py`
**Effort:** M
**Dependencies:** Task 15.1
**Verify:** Kết nối BrightData API thành công (cần API key thật)

### Task 15.3: Implement Oxylabs adapter

- [ ] Tạo `easyproxy/residential/oxylabs.py`
- [ ] Implement `ResidentialProvider` cho Oxylabs API
- [ ] API: `https://api.oxylabs.io/`
- [ ] Auth: username:password basic auth
- [ ] `fetch_ips()` — lấy danh sách proxy entries
- [ ] `rotate_ip()` — yêu cầu IP mới

**Files:** `easyproxy/residential/oxylabs.py`
**Effort:** M
**Dependencies:** Task 15.1
**Verify:** Kết nối Oxylabs API thành công (cần API key thật)

### Task 15.4: Implement Smartproxy adapter

- [ ] Tạo `easyproxy/residential/smartproxy.py`
- [ ] Implement `ResidentialProvider` cho Smartproxy API
- [ ] API: `https://api.smartproxy.com/v1/`
- [ ] Auth: API token
- [ ] `fetch_ips()` — lấy danh sách proxy endpoints

**Files:** `easyproxy/residential/smartproxy.py`
**Effort:** M
**Dependencies:** Task 15.1
**Verify:** Kết nối Smartproxy API thành công (cần API key thật)

### Task 15.5: Implement residential config API

- [ ] `GET /api/v1/residential/config` — lấy config hiện tại (masked API key)
- [ ] `PUT /api/v1/residential/config` — save config + verify connection
- [ ] `POST /api/v1/residential/refresh` — fetch IPs từ provider → add to pool
- [ ] `GET /api/v1/residential/status` — connection status, pool stats
- [ ] `GET /api/v1/residential/providers` — list supported providers

**Files:** `easyproxy/api/routes/residential.py`
**Effort:** M
**Dependencies:** Task 15.1–15.4, Task 2.1
**Verify:** Config residential provider qua API

### Task 15.6: Residential tests

- [ ] Tạo `tests/test_residential.py`
- [ ] Test base provider interface
- [ ] Test config save/load
- [ ] Test API endpoints (mock provider responses)
- [ ] Test error handling (invalid API key)

**Files:** `tests/test_residential.py`
**Effort:** M
**Dependencies:** Task 15.1–15.5
**Verify:** `pytest tests/test_residential.py` passes

---

## US-016: Auto-refresh Pool

### Task 16.1: Implement pool refresh scheduler

- [ ] Tạo `easyproxy/tasks/pool_refresh.py`
- [ ] Background task: refresh residential IP pool every N minutes
- [ ] Configurable interval (default 60 min)
- [ ] Fetch new IPs from all enabled providers → add to `proxies` table
- [ ] Remove stale residential IPs (not refreshed in >2 intervals)
- [ ] Emit WebSocket event `pool_refreshed`

**Files:** `easyproxy/tasks/pool_refresh.py`
**Effort:** S
**Dependencies:** Task 15.5, Task 2.3
**Verify:** Residential pool tự động refresh

### Task 16.2: Implement dead proxy pruning

- [ ] Background task: prune dead static proxies after N consecutive failures
- [ ] Configurable threshold (default 5 consecutive dead checks)
- [ ] Respect minimum pool size (configurable, default 1)
- [ ] Pruned proxies moved to `proxies_history` table (soft delete)
- [ ] Emit WebSocket event `proxies_pruned`

**Files:** `easyproxy/tasks/pool_refresh.py`
**Effort:** S
**Dependencies:** Task 6.2, Task 4.2
**Verify:** Dead proxies tự động bị xoá

### Task 16.3: Auto-refresh tests

- [ ] Tạo `tests/test_pool_refresh.py`
- [ ] Test refresh scheduler
- [ ] Test dead proxy pruning
- [ ] Test WebSocket events

**Files:** `tests/test_pool_refresh.py`
**Effort:** S
**Dependencies:** Task 16.1, 16.2
**Verify:** `pytest tests/test_pool_refresh.py` passes
