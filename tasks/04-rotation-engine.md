# EasyProxy — Tasks: Rotation Engine

> Feature 4: US-007, US-008, US-009, US-010

---

## US-007: Manual Rotation

### Task 7.1: Implement rotation engine

- [ ] Tạo `easyproxy/rotation/engine.py`
- [ ] `rotate()` — pick next proxy from alive pool according to strategy
- [ ] Strategy: round-robin (initially), random, low-latency-first (prep for future)
- [ ] Track current proxy in memory (singleton state)
- [ ] If no alive proxies, raise `NoAliveProxyError`
- [ ] Exclude current proxy from selection (unless only one)
- [ ] Log rotation to `rotation_log` table

**Files:** `easyproxy/rotation/__init__.py`, `easyproxy/rotation/engine.py`
**Effort:** M
**Dependencies:** Task 4.2 (pool manager)
**Verify:** `rotate()` trả về proxy khác mỗi lần gọi

### Task 7.2: Implement rotate API endpoint

- [ ] `POST /api/v1/proxy/rotate` — trigger manual rotation
- [ ] Return: `{previous_ip, new_ip, strategy, timestamp}`
- [ ] `GET /api/v1/proxy/status` — current proxy info, proxy running state
- [ ] Handle: 503 if no alive proxies

**Files:** `easyproxy/api/routes/proxy.py`
**Effort:** S
**Dependencies:** Task 7.1, Task 2.1
**Verify:** `POST /api/v1/proxy/rotate` returns new IP

### Task 7.3: Implement WebSocket event on rotation

- [ ] Emit `proxy_rotated` event: `{previous_ip, new_ip, reason: "manual"}`
- [ ] Connected WebSocket clients receive event in real-time
- [ ] Include rotation ID for frontend traceability

**Files:** `easyproxy/api/routes/proxy.py`, `easyproxy/api/events.py`
**Effort:** S
**Dependencies:** Task 7.2, Task 2.3
**Verify:** WebSocket client nhận rotation event

### Task 7.4: Rotation engine tests

- [ ] Tạo `tests/test_rotation.py`
- [ ] Test round-robin rotation
- [ ] Test no-alive-proxies error
- [ ] Test rotation logging
- [ ] Test API endpoint
- [ ] Test WebSocket event

**Files:** `tests/test_rotation.py`
**Effort:** S
**Dependencies:** Task 7.1–7.3
**Verify:** `pytest tests/test_rotation.py` passes

---

## US-008: Auto-detect Rate Limit

### Task 8.1: Implement rate limit detector

- [ ] Tạo `easyproxy/proxy/ratelimit.py`
- [ ] Parse HTTP response: status == 429 → rate limited
- [ ] Parse `Retry-After` header (seconds or HTTP-date)
- [ ] Configurable status codes (default: 429 only, extendable via settings)
- [ ] Configurable header/body patterns for detection

**Files:** `easyproxy/proxy/ratelimit.py`
**Effort:** S
**Dependencies:** Task 3.2
**Verify:** Detect 429 response correctly

### Task 8.2: Integrate with proxy middleware

- [ ] Hook into proxy response pipeline: after receiving upstream response, before returning to client
- [ ] If rate limited: trigger auto-rotate, retry request with new IP
- [ ] Max retry attempts (configurable, default 3)
- [ ] If all proxies exhausted, return original 429 to client
- [ ] Add `X-EasyProxy-Retry-Count` header to retried requests

**Files:** `easyproxy/proxy/middleware.py`, `easyproxy/proxy/ratelimit.py`
**Effort:** M
**Dependencies:** Task 8.1, Task 7.1
**Verify:** Request gặp 429 → tự động retry với IP khác

### Task 8.3: Implement retry policy

- [ ] Respect `Retry-After` (wait before retry)
- [ ] Exponential backoff cho multiple retries
- [ ] Sticky session reset on 429 (if `reset_on_error` enabled)
- [ ] Rate limit events logged to `rotation_log` with reason `rate_limit_429`

**Files:** `easyproxy/proxy/ratelimit.py`
**Effort:** S
**Dependencies:** Task 8.2
**Verify:** Retry with backoff hoạt động

### Task 8.4: Auto-detect tests

- [ ] Tạo `tests/test_ratelimit.py`
- [ ] Test 429 detection
- [ ] Test Retry-After parsing
- [ ] Test auto-retry flow (mock upstream returns 429 then 200)
- [ ] Test max retry exhaustion

**Files:** `tests/test_ratelimit.py`
**Effort:** M
**Dependencies:** Task 8.1–8.3
**Verify:** `pytest tests/test_ratelimit.py` passes

---

## US-009: Scheduled Rotation

### Task 9.1: Implement rotation scheduler

- [ ] Tạo `easyproxy/tasks/rotation_scheduler.py`
- [ ] Async background task: rotate IP every N minutes
- [ ] Configurable interval via settings (min 30s, max 24h)
- [ ] Respect enabled/disabled flag
- [ ] Wait for in-flight requests before rotation (graceful)
- [ ] Emit WebSocket event `rotation_scheduled`
- [ ] Log reason `scheduled`

**Files:** `easyproxy/tasks/rotation_scheduler.py`
**Effort:** S
**Dependencies:** Task 7.1, Task 2.3
**Verify:** IP tự động rotate sau N phút

### Task 9.2: Scheduled rotation tests

- [ ] Tạo `tests/test_rotation_schedule.py`
- [ ] Test scheduler start/stop
- [ ] Test interval configuration
- [ ] Test WebSocket event

**Files:** `tests/test_rotation_schedule.py`
**Effort:** S
**Dependencies:** Task 9.1
**Verify:** `pytest tests/test_rotation_schedule.py` passes

---

## US-010: Sticky Session

### Task 10.1: Implement sticky session manager

- [ ] Tạo `easyproxy/proxy/sticky.py`
- [ ] In-memory cache: `hostname → proxy_id`
- [ ] TTL per entry (configurable, default 300s)
- [ ] Thread-safe access (asyncio.Lock)
- [ ] Auto-expire stale entries (background cleanup task)
- [ ] Cache size limit (configurable, default 1000 entries, LRU eviction)

**Files:** `easyproxy/proxy/sticky.py`
**Effort:** M
**Dependencies:** Task 7.1
**Verify:** Request tới cùng hostname → cùng proxy trong TTL

### Task 10.2: Integrate sticky session with proxy

- [ ] Hook into proxy request routing: check sticky cache before selecting proxy
- [ ] If proxy in cache is dead → clear entry, select new proxy
- [ ] On 429 error → clear sticky binding (if `reset_on_error` enabled)
- [ ] On manual rotation → clear sticky binding for affected domains
- [ ] Enable/disable via settings

**Files:** `easyproxy/proxy/sticky.py`, `easyproxy/proxy/middleware.py`
**Effort:** M
**Dependencies:** Task 10.1, Task 3.2
**Verify:** Sticky session hoạt động end-to-end

### Task 10.3: Sticky session tests

- [ ] Tạo `tests/test_sticky.py`
- [ ] Test sticky binding
- [ ] Test TTL expiry
- [ ] Test reset on error
- [ ] Test manual rotation clear
- [ ] Test dead proxy fallback

**Files:** `tests/test_sticky.py`
**Effort:** S
**Dependencies:** Task 10.1, 10.2
**Verify:** `pytest tests/test_sticky.py` passes
