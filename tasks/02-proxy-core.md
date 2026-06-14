# EasyProxy — Tasks: Proxy Core

> Feature 2: US-003

---

## US-003: Forward Proxy Core

### Task 3.1: Implement asyncio TCP server

- [ ] Tạo `easyproxy/proxy/server.py` — asyncio.start_server wrapper
- [ ] Listen on configurable host:port (default 0.0.0.0:8080)
- [ ] Accept TCP connections, parse first bytes to detect HTTP/CONNECT
- [ ] Graceful shutdown (close all connections on stop)
- [ ] Connection limits (max concurrent connections)

**Files:** `easyproxy/proxy/__init__.py`, `easyproxy/proxy/server.py`
**Effort:** M
**Dependencies:** Task 1.1, 1.3
**Verify:** `nc localhost 8080` kết nối được

### Task 3.2: Implement HTTP request handler

- [ ] Parse incoming HTTP request (method, URL, headers, body)
- [ ] Forward request to target server via upstream proxy
- [ ] Return response to client
- [ ] Handle chunked encoding
- [ ] Handle connection keep-alive

**Files:** `easyproxy/proxy/http_handler.py`
**Effort:** M
**Dependencies:** Task 3.1
**Verify:** `curl -x http://localhost:8080 http://example.com` trả về response

### Task 3.3: Implement CONNECT tunnel for HTTPS

- [ ] Handle CONNECT method — establish TCP tunnel to target
- [ ] Relay bidirectional data between client and target
- [ ] Handle tunnel timeout (configurable)
- [ ] Handle CONNECT through upstream proxy

**Files:** `easyproxy/proxy/connect.py`
**Effort:** M
**Dependencies:** Task 3.1
**Verify:** `curl -x http://localhost:8080 https://example.com -v` tunnel thành công

### Task 3.4: Implement upstream proxy connector

- [ ] Tạo `easyproxy/proxy/upstream.py` — kết nối tới upstream proxy
- [ ] Hỗ trợ HTTP/HTTPS/SOCKS5 upstream protocols
- [ ] Basic auth support (username:password@host:port)
- [ ] Connection pooling (reuse connections to same upstream)
- [ ] Timeout handling (connect + read timeout)

**Files:** `easyproxy/proxy/upstream.py`
**Effort:** M
**Dependencies:** Task 3.2, 3.3
**Verify:** Request qua upstream proxy hoạt động

### Task 3.5: Implement header sanitization

- [ ] Remove/rewrite `X-Forwarded-For`, `X-Real-IP`, `Via`, `Forwarded`
- [ ] Remove proxy-specific headers before forwarding
- [ ] Add `Via` header with EasyProxy signature
- [ ] Handle `Connection` header correctly (hop-by-hop)

**Files:** `easyproxy/proxy/headers.py`
**Effort:** S
**Dependencies:** Task 3.2
**Verify:** Target server không thấy IP thật của client

### Task 3.6: Implement request logging middleware

- [ ] Log mỗi request: method, URL, status code, proxy IP used, duration, bytes
- [ ] Write to `request_log` table (async via aiosqlite)
- [ ] Track stats: request count, bytes transferred, error count
- [ ] Debounce high-frequency writes (batch insert every N requests)

**Files:** `easyproxy/proxy/middleware.py`
**Effort:** S
**Dependencies:** Task 3.2, Task 1.4
**Verify:** Request logged trong DB

### Task 3.7: Implement error handling

- [ ] Upstream unreachable → 502 Bad Gateway
- [ ] Upstream timeout → 504 Gateway Timeout
- [ ] Invalid request → 400 Bad Request
- [ ] Too many connections → 429 (with Retry-After)
- [ ] Connection refused, DNS failure handled gracefully
- [ ] Log all errors with context

**Files:** `easyproxy/proxy/errors.py`
**Effort:** S
**Dependencies:** Task 3.1–3.4
**Verify:** `curl -x http://localhost:8080 http://nonexistent.domain` returns 502

### Task 3.8: Proxy engine tests

- [ ] Tạo `tests/test_proxy_server.py` — start/stop proxy
- [ ] Tạo `tests/test_proxy_http.py` — HTTP GET/POST/HEAD qua proxy
- [ ] Tạo `tests/test_proxy_connect.py` — HTTPS CONNECT tunnel test
- [ ] Tạo `tests/test_proxy_errors.py` — error handling test
- [ ] Sử dụng aiohttp test client + mock upstream server

**Files:** `tests/test_proxy_server.py`, `tests/test_proxy_http.py`, `tests/test_proxy_connect.py`, `tests/test_proxy_errors.py`
**Effort:** M
**Dependencies:** Task 3.1–3.7
**Verify:** `pytest tests/test_proxy_*.py` passes
