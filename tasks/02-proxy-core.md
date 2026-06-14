# EasyProxy — Tasks: Proxy Core

> Feature 2: US-003

---

## US-003: Forward Proxy Core

### Task 3.1: Implement asyncio TCP server

- [x] Tạo `easyproxy/proxy/server.py` — asyncio.start_server wrapper (180 lines)
- [x] Listen on configurable host:port (default 127.0.0.1:8080)
- [x] Accept TCP connections, parse first bytes to detect HTTP/CONNECT
- [x] Graceful shutdown (close all connections on stop)
- [x] Connection limits (max concurrent: 1000)

**Files:** `easyproxy/proxy/__init__.py`, `easyproxy/proxy/server.py`
**Effort:** M
**Dependencies:** Task 1.1, 1.3
**Verify:** `nc localhost 8080` kết nối được

### Task 3.2: Implement HTTP request handler

- [x] Parse incoming HTTP request (method, URL, headers, body)
- [x] Forward request to target server via aiohttp
- [x] Return response to client with proper status/headers/body
- [x] Handle Content-Length for request body
- [x] Handle connection keep-alive

**Files:** `easyproxy/proxy/http_handler.py`
**Effort:** M
**Dependencies:** Task 3.1
**Verify:** `curl -x http://localhost:8080 http://example.com` trả về response

### Task 3.3: Implement CONNECT tunnel for HTTPS

- [x] Handle CONNECT method — establish TCP tunnel to target
- [x] Relay bidirectional data between client and target (asyncio.gather)
- [x] Handle tunnel timeout (600s idle timeout)
- [x] Handle CONNECT through HTTP/SOCKS5 upstream proxy

**Files:** `easyproxy/proxy/connect.py`
**Effort:** M
**Dependencies:** Task 3.1
**Verify:** `curl -x http://localhost:8080 https://example.com -v` tunnel thành công

### Task 3.4: Implement upstream proxy connector

- [x] Tạo `easyproxy/proxy/upstream.py` — aiohttp cho HTTP, raw TCP cho CONNECT
- [x] Hỗ trợ HTTP/HTTPS upstream protocols (qua aiohttp + HTTP CONNECT)
- [x] Hỗ trợ SOCKS5 upstream (SOCKS5 handshake protocol)
- [x] Basic auth support (Proxy-Authorization header + SOCKS5)
- [x] Connection pooling (aiohttp TCPConnector với limit=100)
- [x] Timeout handling (connect + read timeout, configurable)

**Files:** `easyproxy/proxy/upstream.py`
**Effort:** M
**Dependencies:** Task 3.2, 3.3
**Verify:** Request qua upstream proxy hoạt động

### Task 3.5: Implement header sanitization

- [x] Remove X-Forwarded-For, X-Real-IP, Via, Forwarded, X-Forwarded-*
- [x] Remove hop-by-hop headers (Connection, Transfer-Encoding, etc.)
- [x] Add `Via` header with EasyProxy/0.1.0 signature
- [x] Handle `Connection` header correctly (parse additional hop-by-hop)

**Files:** `easyproxy/proxy/headers.py`
**Effort:** S
**Dependencies:** Task 3.2
**Verify:** Target server không thấy IP thật của client

### Task 3.6: Implement request logging middleware

- [x] Log mỗi request: method, URL, status code, proxy IP used, duration, bytes
- [x] Write to `request_log` table (async via aiosqlite)
- [x] Track stats: request count, bytes transferred, error count
- [x] Debounce high-frequency writes (batch insert every 10 requests)

**Files:** `easyproxy/proxy/middleware.py`
**Effort:** S
**Dependencies:** Task 3.2, Task 1.4
**Verify:** Request logged trong DB

### Task 3.7: Implement error handling

- [x] Upstream unreachable → 502 Bad Gateway (`UpstreamUnreachable`)
- [x] Upstream timeout → 504 Gateway Timeout (`UpstreamTimeout`)
- [x] Invalid request → 400 Bad Request (`InvalidRequest`)
- [x] Too many connections → 429 (`TooManyConnections`)
- [x] Connection refused (`ConnectionRefused`), DNS failure (`DNSResolutionFailed`)
- [x] All errors logged with context, RFC-compliant HTML error pages

**Files:** `easyproxy/proxy/errors.py`
**Effort:** S
**Dependencies:** Task 3.1–3.4
**Verify:** `curl -x http://localhost:8080 http://nonexistent.domain` returns 502

### Task 3.8: Proxy engine tests

- [x] Tạo `tests/test_proxy_server.py` — start/stop/connections (4 tests)
- [x] Tạo `tests/test_proxy_http.py` — HTTP GET/POST/GET JSON qua proxy (4 tests)
- [x] Tạo `tests/test_proxy_connect.py` — CONNECT tunnel + HTTPS + error cases (4 tests)
- [x] Tạo `tests/test_proxy_errors.py` — error classes, headers, upstream parsing, server errors (22 tests)

**Files:** `tests/test_proxy_server.py`, `tests/test_proxy_http.py`, `tests/test_proxy_connect.py`, `tests/test_proxy_errors.py`
**Effort:** M
**Dependencies:** Task 3.1–3.7
**Verify:** `pytest tests/test_proxy_*.py` passes
