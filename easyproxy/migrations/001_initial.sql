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
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(address, port)
);

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
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rotation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
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

CREATE TABLE IF NOT EXISTS request_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
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
    pruned_at TEXT NOT NULL DEFAULT (datetime('now')),
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_errors INTEGER NOT NULL DEFAULT 0
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_proxies_status ON proxies(status);
CREATE INDEX IF NOT EXISTS idx_proxies_protocol ON proxies(protocol);
CREATE INDEX IF NOT EXISTS idx_proxies_region ON proxies(region);
CREATE INDEX IF NOT EXISTS idx_proxies_source ON proxies(source);
CREATE INDEX IF NOT EXISTS idx_request_log_timestamp ON request_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_request_log_host ON request_log(host);
CREATE INDEX IF NOT EXISTS idx_request_log_status_code ON request_log(status_code);
CREATE INDEX IF NOT EXISTS idx_request_log_proxy_id ON request_log(proxy_id);
CREATE INDEX IF NOT EXISTS idx_rotation_log_timestamp ON rotation_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_rotation_log_reason ON rotation_log(reason);
CREATE INDEX IF NOT EXISTS idx_rotation_log_to_proxy_id ON rotation_log(to_proxy_id);

-- Seed settings
INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES
    ('general.auto_start', 'false', datetime('now')),
    ('general.minimize_to_tray', 'true', datetime('now')),
    ('general.theme', 'system', datetime('now')),
    ('proxy.port', '8080', datetime('now')),
    ('proxy.auto_configure_system_proxy', 'true', datetime('now')),
    ('proxy.bind_address', '127.0.0.1', datetime('now')),
    ('rotation.strategy', 'round-robin', datetime('now')),
    ('rotation.schedule_enabled', 'false', datetime('now')),
    ('rotation.schedule_interval_minutes', '10', datetime('now')),
    ('rotation.auto_rotate_on_429', 'true', datetime('now')),
    ('rotation.retry_attempts', '3', datetime('now')),
    ('sticky_session.enabled', 'true', datetime('now')),
    ('sticky_session.ttl_seconds', '300', datetime('now')),
    ('sticky_session.reset_on_error', 'true', datetime('now')),
    ('logs.max_entries', '10000', datetime('now')),
    ('logs.log_level', 'info', datetime('now')),
    ('health_check.interval_seconds', '60', datetime('now')),
    ('health_check.test_url', 'http://httpbin.org/ip', datetime('now')),
    ('health_check.timeout_seconds', '10', datetime('now'));
