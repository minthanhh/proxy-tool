# EasyProxy — Database Schema

**Engine:** SQLite 3.x  
**File location:** `~/.easyproxy/easyproxy.db`  
**Access:** `aiosqlite` (async) via FastAPI backend  
**No ORM** — raw SQL via `aiosqlite` for simplicity; migration tracking via `schema_version` table.

---

## Table: `proxies`

Static proxy list managed by the user.

| Column | Type | Constraints | Description | Example |
|--------|------|-------------|-------------|---------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique proxy ID | `1` |
| `address` | TEXT | NOT NULL | IP address or hostname | `45.67.89.10` |
| `port` | INTEGER | NOT NULL | Proxy port | `3128` |
| `protocol` | TEXT | NOT NULL DEFAULT 'http' | `http`, `https`, `socks5` | `http` |
| `username` | TEXT | NULLABLE | Auth username | `proxyuser` |
| `password` | TEXT | NULLABLE | Auth password (stored encrypted if possible) | `s3cret` |
| `region` | TEXT | NULLABLE | Geo region code (ISO 3166-1 alpha-2) | `US` |
| `status` | TEXT | NOT NULL DEFAULT 'untested' | `alive`, `dead`, `untested` | `alive` |
| `latency_ms` | INTEGER | NULLABLE | Last measured latency | `230` |
| `last_checked_at` | TEXT | NULLABLE | ISO 8601 timestamp of last health check | `2026-06-14T10:00:00Z` |
| `source` | TEXT | NOT NULL DEFAULT 'manual' | `manual`, `import`, `residential` | `manual` |
| `residential_provider` | TEXT | NULLABLE | Provider name if source=residential | `brightdata` |
| `error_count` | INTEGER | NOT NULL DEFAULT 0 | Cumulative error count | `3` |
| `success_count` | INTEGER | NOT NULL DEFAULT 0 | Cumulative success count | `45` |
| `consecutive_errors` | INTEGER | NOT NULL DEFAULT 0 | Consecutive errors (for dead detection) | `0` |
| `created_at` | TEXT | NOT NULL | ISO 8601 timestamp | `2026-06-10T08:00:00Z` |
| `updated_at` | TEXT | NOT NULL | ISO 8601 timestamp | `2026-06-14T10:00:00Z` |

**Unique constraint:** `UNIQUE(address, port)`

```sql
CREATE TABLE IF NOT EXISTS proxies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT NOT NULL,
    port INTEGER NOT NULL,
    protocol TEXT NOT NULL DEFAULT 'http',
    username TEXT,
    password TEXT,
    region TEXT,
    status TEXT NOT NULL DEFAULT 'untested',
    latency_ms INTEGER,
    last_checked_at TEXT,
    source TEXT NOT NULL DEFAULT 'manual',
    residential_provider TEXT,
    error_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    consecutive_errors INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(address, port)
);
```

---

## Table: `residential_config`

Residential proxy provider configuration. Only one active config at a time.

| Column | Type | Constraints | Description | Example |
|--------|------|-------------|-------------|---------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Row ID | `1` |
| `provider` | TEXT | NOT NULL | Provider name | `brightdata` |
| `api_key` | TEXT | NOT NULL | API key / token | `sk-abc123...` |
| `zone` | TEXT | NULLABLE | Provider zone/endpoint | `residential-static` |
| `country` | TEXT | NULLABLE DEFAULT 'auto' | Country code or 'auto' | `us` |
| `sticky_ip` | INTEGER | NOT NULL DEFAULT 0 | Boolean: use sticky IPs | `1` |
| `pool_size` | INTEGER | NOT NULL DEFAULT 50 | Target pool size | `50` |
| `active_ips` | INTEGER | NOT NULL DEFAULT 0 | Current active IP count | `42` |
| `connected` | INTEGER | NOT NULL DEFAULT 0 | Connection state | `1` |
| `connected_at` | TEXT | NULLABLE | ISO 8601 connect timestamp | `2026-06-14T00:00:00Z` |
| `expires_at` | TEXT | NULLABLE | ISO 8601 expiry | `2026-07-14T00:00:00Z` |
| `last_refreshed_at` | TEXT | NULLABLE | ISO 8601 last pool refresh | `2026-06-14T10:00:00Z` |
| `created_at` | TEXT | NOT NULL | ISO 8601 timestamp | `2026-06-10T08:00:00Z` |
| `updated_at` | TEXT | NOT NULL | ISO 8601 timestamp | `2026-06-14T10:00:00Z` |

```sql
CREATE TABLE IF NOT EXISTS residential_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    api_key TEXT NOT NULL,
    zone TEXT,
    country TEXT DEFAULT 'auto',
    sticky_ip INTEGER NOT NULL DEFAULT 0,
    pool_size INTEGER NOT NULL DEFAULT 50,
    active_ips INTEGER NOT NULL DEFAULT 0,
    connected INTEGER NOT NULL DEFAULT 0,
    connected_at TEXT,
    expires_at TEXT,
    last_refreshed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

---

## Table: `settings`

Application settings. Key-value store with JSON values for complex types.

| Column | Type | Constraints | Description | Example |
|--------|------|-------------|-------------|---------|
| `key` | TEXT | PRIMARY KEY | Setting key (dot-separated path) | `rotation.strategy` |
| `value` | TEXT | NOT NULL | JSON-encoded value | `"\"round-robin\""` |
| `updated_at` | TEXT | NOT NULL | ISO 8601 timestamp | `2026-06-14T10:00:00Z` |

```sql
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**Seed data:**
```sql
INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES
    ('general.auto_start', 'false', CURRENT_TIMESTAMP),
    ('general.minimize_to_tray', 'true', CURRENT_TIMESTAMP),
    ('general.theme', '"system"', CURRENT_TIMESTAMP),
    ('proxy.port', '8080', CURRENT_TIMESTAMP),
    ('proxy.auto_configure_system_proxy', 'true', CURRENT_TIMESTAMP),
    ('proxy.bind_address', '"127.0.0.1"', CURRENT_TIMESTAMP),
    ('rotation.strategy', '"round-robin"', CURRENT_TIMESTAMP),
    ('rotation.schedule_enabled', 'false', CURRENT_TIMESTAMP),
    ('rotation.schedule_interval_minutes', '10', CURRENT_TIMESTAMP),
    ('rotation.auto_rotate_on_429', 'true', CURRENT_TIMESTAMP),
    ('rotation.retry_attempts', '3', CURRENT_TIMESTAMP),
    ('sticky_session.enabled', 'true', CURRENT_TIMESTAMP),
    ('sticky_session.ttl_seconds', '300', CURRENT_TIMESTAMP),
    ('sticky_session.reset_on_error', 'true', CURRENT_TIMESTAMP),
    ('logs.max_entries', '10000', CURRENT_TIMESTAMP),
    ('logs.log_level', '"info"', CURRENT_TIMESTAMP),
    ('health_check.interval_seconds', '60', CURRENT_TIMESTAMP),
    ('health_check.test_url', '"http://httpbin.org/ip"', CURRENT_TIMESTAMP),
    ('health_check.timeout_seconds', '10', CURRENT_TIMESTAMP);
```

---

## Table: `rotation_log`

History of all IP rotations.

| Column | Type | Constraints | Description | Example |
|--------|------|-------------|-------------|---------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Rotation event ID | `1` |
| `timestamp` | TEXT | NOT NULL | ISO 8601 timestamp | `2026-06-14T10:05:00Z` |
| `reason` | TEXT | NOT NULL | `rate_limit_429`, `manual`, `scheduled`, `error`, `startup` | `rate_limit_429` |
| `trigger` | TEXT | NOT NULL | `auto`, `user`, `system` | `auto` |
| `from_proxy_id` | INTEGER | NULLABLE REFERENCES proxies(id) | Previous proxy | `12` |
| `from_proxy` | TEXT | NULLABLE | Previous proxy address:port (denormalized) | `45.67.89.10:3128` |
| `to_proxy_id` | INTEGER | NULLABLE REFERENCES proxies(id) | New proxy | `15` |
| `to_proxy` | TEXT | NULLABLE | New proxy address:port (denormalized) | `98.76.54.32:8080` |
| `retry_after_seconds` | INTEGER | NULLABLE | Retry-After header value | `30` |
| `request_url` | TEXT | NULLABLE | URL that triggered rotation | `https://api.example.com/data` |
| `request_method` | TEXT | NULLABLE | HTTP method | `GET` |
| `retry_success` | INTEGER | NULLABLE | Boolean: retry succeeded | `1` |
| `response_status` | INTEGER | NULLABLE | Original status code | `429` |
| `duration_ms` | INTEGER | NULLABLE | Total rotation + retry time | `1500` |

```sql
CREATE TABLE IF NOT EXISTS rotation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    reason TEXT NOT NULL,
    trigger TEXT NOT NULL,
    from_proxy_id INTEGER REFERENCES proxies(id),
    from_proxy TEXT,
    to_proxy_id INTEGER REFERENCES proxies(id),
    to_proxy TEXT,
    retry_after_seconds INTEGER,
    request_url TEXT,
    request_method TEXT,
    retry_success INTEGER,
    response_status INTEGER,
    duration_ms INTEGER
);
```

---

## Table: `request_log`

Detailed log of every proxied request. Circular buffer — old entries are deleted when count exceeds `max_entries`.

| Column | Type | Constraints | Description | Example |
|--------|------|-------------|-------------|---------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Log entry ID | `1` |
| `timestamp` | TEXT | NOT NULL | ISO 8601 with milliseconds | `2026-06-14T10:00:00.123Z` |
| `method` | TEXT | NOT NULL | HTTP method | `GET` |
| `url` | TEXT | NOT NULL | Full request URL | `https://api.example.com/data` |
| `host` | TEXT | NOT NULL | Extracted hostname | `api.example.com` |
| `status_code` | INTEGER | NOT NULL | Response status code | `200` |
| `proxy_id` | INTEGER | NULLABLE REFERENCES proxies(id) | Upstream proxy used | `12` |
| `proxy_address` | TEXT | NULLABLE | Proxy address:port (denormalized) | `45.67.89.10:3128` |
| `duration_ms` | INTEGER | NOT NULL | Request duration | `340` |
| `bytes_sent` | INTEGER | NOT NULL DEFAULT 0 | Request size in bytes | `512` |
| `bytes_received` | INTEGER | NOT NULL DEFAULT 0 | Response size in bytes | `4096` |
| `user_agent` | TEXT | NULLABLE | User-Agent header | `Mozilla/5.0...` |
| `content_type` | TEXT | NULLABLE | Response Content-Type | `application/json` |
| `rotated` | INTEGER | NOT NULL DEFAULT 0 | Boolean: rotation triggered | `0` |
| `error` | TEXT | NULLABLE | Error message if failed | `Connection timeout` |

```sql
CREATE TABLE IF NOT EXISTS request_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    method TEXT NOT NULL,
    url TEXT NOT NULL,
    host TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    proxy_id INTEGER REFERENCES proxies(id),
    proxy_address TEXT,
    duration_ms INTEGER NOT NULL,
    bytes_sent INTEGER NOT NULL DEFAULT 0,
    bytes_received INTEGER NOT NULL DEFAULT 0,
    user_agent TEXT,
    content_type TEXT,
    rotated INTEGER NOT NULL DEFAULT 0,
    error TEXT
);
```

---

## Table: `schema_version`

Migration tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `version` | INTEGER | PRIMARY KEY | Schema version number |
| `applied_at` | TEXT | NOT NULL | ISO 8601 timestamp |
| `description` | TEXT | NULLABLE | Human-readable description |

```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT
);
```

---

## Table: `proxies_history`

Soft-deleted / pruned proxies. Populated when dead proxies are pruned from pool.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Entry ID |
| `proxy_id` | INTEGER | NOT NULL | Original proxy ID (before deletion) |
| `address` | TEXT | NOT NULL | IP address |
| `port` | INTEGER | NOT NULL | Proxy port |
| `protocol` | TEXT | NOT NULL | http / https / socks5 |
| `region` | TEXT | NULLABLE | Geo region |
| `source` | TEXT | NOT NULL | `manual`, `import`, `residential` |
| `residential_provider` | TEXT | NULLABLE | Provider name if residential |
| `status_at_prune` | TEXT | NOT NULL | `dead`, `expired` |
| `prune_reason` | TEXT | NOT NULL | `consecutive_errors`, `expired`, `manual_remove` |
| `pruned_at` | TEXT | NOT NULL | ISO 8601 timestamp |
| `total_requests` | INTEGER | NOT NULL DEFAULT 0 | Requests served before deletion |
| `total_errors` | INTEGER | NOT NULL DEFAULT 0 | Errors before deletion |

```sql
CREATE TABLE IF NOT EXISTS proxies_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proxy_id INTEGER NOT NULL,
    address TEXT NOT NULL,
    port INTEGER NOT NULL,
    protocol TEXT NOT NULL DEFAULT 'http',
    region TEXT,
    source TEXT NOT NULL DEFAULT 'manual',
    residential_provider TEXT,
    status_at_prune TEXT NOT NULL DEFAULT 'dead',
    prune_reason TEXT NOT NULL DEFAULT 'consecutive_errors',
    pruned_at TEXT NOT NULL,
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_errors INTEGER NOT NULL DEFAULT 0
);
```

---

## Indexes

```sql
-- Proxy lookup
CREATE INDEX IF NOT EXISTS idx_proxies_status ON proxies(status);
CREATE INDEX IF NOT EXISTS idx_proxies_protocol ON proxies(protocol);
CREATE INDEX IF NOT EXISTS idx_proxies_region ON proxies(region);
CREATE INDEX IF NOT EXISTS idx_proxies_source ON proxies(source);

-- Request log queries
CREATE INDEX IF NOT EXISTS idx_request_log_timestamp ON request_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_request_log_host ON request_log(host);
CREATE INDEX IF NOT EXISTS idx_request_log_status_code ON request_log(status_code);
CREATE INDEX IF NOT EXISTS idx_request_log_proxy_id ON request_log(proxy_id);

-- Rotation log queries
CREATE INDEX IF NOT EXISTS idx_rotation_log_timestamp ON rotation_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_rotation_log_reason ON rotation_log(reason);
CREATE INDEX IF NOT EXISTS idx_rotation_log_to_proxy_id ON rotation_log(to_proxy_id);
```

## View: `pool_stats` (convenience view)

```sql
CREATE VIEW IF NOT EXISTS pool_stats AS
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN status = 'alive' THEN 1 ELSE 0 END) AS alive,
    SUM(CASE WHEN status = 'dead' THEN 1 ELSE 0 END) AS dead,
    SUM(CASE WHEN status = 'untested' THEN 1 ELSE 0 END) AS untested,
    AVG(CASE WHEN status = 'alive' THEN latency_ms END) AS avg_latency,
    protocol,
    region
FROM proxies
GROUP BY protocol, region;
```

## Migration strategy

```
v0 → v1: Initial schema (all tables above)
v2+: ALTER TABLE ADD COLUMN for new fields
```

**Migration files:** `~/.easyproxy/migrations/001_initial.sql`, `002_*.sql`, ...

**Migration runner pseudocode:**
```python
async def run_migrations(db):
    current = await db.fetch_val("SELECT MAX(version) FROM schema_version") or 0
    for version, sql_file in sorted(MIGRATIONS.items()):
        if version > current:
            sql = read_migration(sql_file)
            await db.execute(sql)
            await db.execute(
                "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?)",
                version, now(), sql_file
            )
```

**Data retention:**
- `request_log`: culled to `logs.max_entries` on each insert (oldest deleted first)
- `rotation_log`: permanent (low volume)
- `settings` and `residential_config`: permanent

**Cleanup query (run on startup and periodically):**
```sql
DELETE FROM request_log WHERE id NOT IN (
    SELECT id FROM request_log ORDER BY id DESC LIMIT ?
);
```
