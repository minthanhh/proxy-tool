# EasyProxy — Core Proxy Engine Specification

## Tổng quan

Proxy Engine là trái tim của EasyProxy — một HTTP forward proxy server chạy trên localhost, xử lý tất cả request từ user applications, chuyển tiếp qua upstream proxy với IP rotation tự động. Được xây dựng trên Python `asyncio` và `aiohttp`.

---

## HTTP Forward Proxy Implementation

### Request lifecycle

```
Client ──► Proxy Engine (:8080) ──► Strategy Selector ──► Upstream Proxy ──► Internet
             │                           │                       │
             │  ┌───────────────────┐    │                       │
             │  │ 1. Parse request  │◄───┘                       │
             │  │ 2. Check sticky   │                           │
             │  │    session cache  │                           │
             │  │ 3. Select proxy   │                           │
             │  │    from pool      │                           │
             │  └───────────────────┘                           │
             │                        ┌─────────────────────┐   │
             │                        │ 4. Forward via      │   │
             │                        │    aiohttp.ClientSession│
             │                        │ 5. Apply custom     │   │
             │                        │    headers (X-Forwarded)│
             │                        └─────────────────────┘   │
             │                           │                       │
             │  ┌───────────────────┐    │                       │
             │  │ 6. Inspect status │◄───┘                       │
             │  │    code          │                            │
             │  │ 7. If 429:       │                            │
             │  │    → log         │                            │
             │  │    → rotate      │                            │
             │  │    → retry       │                            │
             │  │ 8. Return to     │                            │
             │  │    client        │                            │
             │  └───────────────────┘                            │
```

### HTTP handling

```python
# Pseudocode — core handler
async def handle_request(request: aiohttp.web.Request):
    upstream = await pool_manager.select_proxy(strategy, host=request.host)
    session = aiohttp.ClientSession(
        proxy=f"http://{upstream.address}:{upstream.port}",
        connector=upstream_connector,
    )
    try:
        async with session.request(
            request.method,
            request.url,
            headers=prepare_headers(request.headers),
            data=request.content,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            # Check rate limit
            if resp.status == 429 and settings.auto_rotate:
                await rotate_and_retry(request, upstream)
            # Stream response back to client
            return build_response(resp)
    except (ConnectionError, TimeoutError) as e:
        await mark_dead(upstream)
        return try_next_proxy(request, upstream)
```

### CONNECT tunnel (HTTPS)

For HTTPS requests, the proxy receives a `CONNECT host:port` request. It must:

1. Respond `200 Connection Established` to the client
2. Create a raw TCP tunnel between client and upstream proxy
3. Relay all subsequent bytes bidirectionally

```python
# Pseudocode — CONNECT handler
async def handle_connect(request: aiohttp.web.Request):
    host, port = request.path.split(":")
    upstream = await pool_manager.select_proxy(strategy, host=host)

    # Connect to upstream proxy
    upstream_reader, upstream_writer = await asyncio.open_connection(
        upstream.address, upstream.port
    )

    # Send CONNECT to upstream proxy (for proxy chaining)
    connect_req = f"CONNECT {host}:{port} HTTP/1.1\r\n\r\n"
    upstream_writer.write(connect_req.encode())
    await upstream_writer.drain()

    # Wait for upstream response
    response = await upstream_reader.readuntil(b"\r\n\r\n")

    if b"200" not in response:
        await respond_502(request)
        return

    # Send 200 to client
    await request.transport.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")

    # Bidirectional pipe
    transport = request.transport
    await asyncio.gather(
        pipe(transport, upstream_writer, upstream_reader),
        pipe(upstream_reader, transport.write, transport),
    )
```

## Rotation Strategies

### Round-robin

Cycle through available (alive) proxies sequentially.

```python
next_index = (current_index + 1) % len(alive_proxies)
```

- **Pros:** Fair distribution, predictable
- **Cons:** Ignores latency, doesn't avoid overloaded proxies

### Random

Pick a random alive proxy.

```python
proxy = random.choice(alive_proxies)
```

- **Pros:** Simple, avoids pattern detection by target servers
- **Cons:** No consistency, may pick slow proxies

### Low-latency-first

Prefer proxies with lowest recent latency, with jitter to avoid thundering herd.

```python
weighted = [(1.0 / (p.latency_ms + 50)) for p in alive_proxies]
proxy = random.choices(alive_proxies, weights=weighted, k=1)[0]
```

- **Pros:** Best performance for user
- **Cons:** May overload fastest proxies

### Configuration

Strategy is configurable via `POST /api/v1/settings`:
```json
{"rotation": {"strategy": "low-latency-first"}}
```

## Rate Limit Detection

### Detection mechanism

1. Inspect response status code for `429 Too Many Requests`
2. Parse `Retry-After` header (supports both seconds and HTTP-date)
3. Extract any custom rate-limit headers: `X-RateLimit-*`, `X-Retry-After`

```python
async def check_rate_limit(response):
    if response.status == 429:
        retry_after = None
        if "Retry-After" in response.headers:
            raw = response.headers["Retry-After"]
            retry_after = int(raw) if raw.isdigit() else parse_http_date(raw)
        return RateLimitResult(
            detected=True,
            retry_after=retry_after,
            headers=dict(response.headers),
        )
    return RateLimitResult(detected=False)
```

### Auto-retry flow

1. Rate limit detected on response
2. Log the event (timestamp, URL, proxy, Retry-After)
3. Emit WebSocket event `rate_limit_detected`
4. Select new proxy (exclude current proxy from selection)
5. Wait for `Retry-After` seconds (if present and < 60s, else cap at 60s)
6. Replay the same request with new proxy
7. If retry succeeds → continue normally; if 429 again → try next proxy (up to `retry_attempts` setting)

```python
async def rotate_and_retry(original_request, failed_upstream, retry_after=0):
    for attempt in range(settings.retry_attempts):
        new_proxy = await pool_manager.select_proxy(
            strategy, exclude=[failed_upstream.id]
        )
        await asyncio.sleep(min(retry_after, 60))
        success = await forward_request(original_request, new_proxy)
        if success:
            await log_rotation(failed_upstream, new_proxy, "rate_limit_429")
            return success
    return await fallback_direct(original_request)
```

## Sticky Session

### Purpose

Some websites require the same IP for the duration of a session (e.g., login flows, CAPTCHA triggers, pagination). Sticky session ensures requests to the same domain use the same proxy IP.

### Implementation

```python
class StickySessionManager:
    def __init__(self, ttl_seconds=300):
        self._mapping: dict[str, StickyEntry] = {}  # domain → proxy
        self._ttl = ttl_seconds

    def get_proxy(self, host: str) -> Optional[Proxy]:
        entry = self._mapping.get(host)
        if entry and not entry.is_expired():
            return entry.proxy
        return None

    def set_proxy(self, host: str, proxy: Proxy):
        self._mapping[host] = StickyEntry(proxy, ttl=self._ttl)

    def reset(self, host: str = None):
        if host:
            self._mapping.pop(host, None)
        else:
            self._mapping.clear()

    def expire(self, host: str):
        entry = self._mapping.get(host)
        if entry:
            entry.expire()
```

### Behavior

- **TTL:** Each sticky binding expires after `sticky_session.ttl_seconds` (default 300s)
- **Reset on error:** If proxy returns 429 or error, sticky binding for that domain is cleared (if `reset_on_error` is true)
- **Scope:** Hostname-level (not URL-level). `api.example.com` and `www.example.com` get different bindings

## Error Handling

### Dead proxy detection

```python
DEAD_THRESHOLDS = {
    "consecutive_errors": 3,      # Mark dead after N consecutive failures
    "timeout_count": 5,           # Mark dead after N timeouts
    "latency_threshold_ms": 10000, # Mark dead if latency > 10s
    "cooldown_seconds": 300,       # Auto-revive after 5 min for retest
}
```

### Fallback chain

When a proxy fails:
1. Mark as failed in DB, increment error count
2. If consecutive errors ≥ threshold, mark as `dead`
3. Remove from active pool
4. Select next proxy (exclude failed ones)
5. Retry request
6. If all proxies fail → return 502 Bad Gateway

### Retry logic

| Failure type | Retry? | Strategy |
|-------------|--------|----------|
| HTTP 429 | Yes | Rotate IP, wait Retry-After |
| Connection timeout | Yes | Try next proxy immediately |
| Connection refused | Yes | Try next proxy immediately |
| SSL error | Yes | Try next proxy (maybe proxy issue) |
| HTTP 5xx | No | Return to client as-is |
| DNS resolution failure | No | Client error |

## Performance

### Connection pooling

```python
upstream_connector = aiohttp.TCPConnector(
    limit=100,          # Max total connections
    limit_per_host=10,  # Max per host
    ttl_dns_cache=300,  # DNS cache lifetime
    keepalive_timeout=30,
    force_close=False,  # Keep-alive when possible
)
```

### Timeout management

| Timeout | Value | Description |
|---------|-------|-------------|
| Client connection timeout | 30s | Max wait to connect to upstream proxy |
| Client read timeout | 60s | Max wait for upstream response |
| Client total timeout | 120s | Max total request duration |
| Forward proxy idle timeout | 300s | Close idle client connections |
| DNS cache TTL | 300s | How long to cache DNS results |

### Concurrent request handling

- Proxy Engine uses `asyncio` with a configurable `max_concurrent_requests` (default 500)
- Uses `asyncio.Semaphore` to limit concurrent upstream connections
- Request queue with backpressure if limit exceeded

## Security Considerations

### DNS leak prevention

- All DNS resolution must go through the upstream proxy, NOT the local DNS
- For HTTP: proxy handles DNS, client never resolves
- For HTTPS (CONNECT): client resolves DNS — cannot prevent directly, but we warn users via documentation
- Configurable option to force DNS via upstream (use `aiohttp.ClientSession` with `resolve_host=False` on client side)

### WebRTC leak prevention

- Can't prevent server-side; document that users should disable WebRTC in browser or use WebRTC leak prevention extensions
- Future: could add a browser extension companion

### IPv6 handling

- If user's system has IPv6 enabled and proxy destination is IPv4-only, may leak real IPv6
- Solution: Bind proxy engine to `127.0.0.1` only (not `::1`), force IPv4 via `aiohttp.connector.TCPConnector(family=socket.AF_INET)`
- Future: support IPv6 proxies with explicit configuration

### Header sanitization

Remove or rewrite headers that could leak client IP:

| Header | Action |
|--------|--------|
| `X-Forwarded-For` | Rewrite to upstream proxy IP |
| `X-Real-IP` | Rewrite to upstream proxy IP |
| `Via` | Add EasyProxy version |
| `Proxy-Authorization` | Strip (auth to local proxy not forwarded) |
| `Proxy-Connection` | Strip (hop-by-hop header) |

### TLS considerations

- CONNECT tunnel does not inspect TLS traffic (man-in-the-middle is NOT supported and not intended)
- All HTTPS traffic is end-to-end encrypted; EasyProxy is a simple TCP relay
- Only HTTP traffic is readable by EasyProxy
