import tempfile
from pathlib import Path

import pytest

from easyproxy.database import Database


@pytest.fixture
async def db(isolate_db):
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        db = Database(db_path=db_path)
        yield db
        await db.close()


@pytest.mark.asyncio
async def test_connect_creates_db_file(db):
    conn = await db.connect()
    assert conn is not None
    assert Path(db.db_path).exists()


@pytest.mark.asyncio
async def test_connect_returns_same_connection(db):
    conn1 = await db.connect()
    conn2 = await db.connect()
    assert conn1 is conn2


@pytest.mark.asyncio
async def test_run_migrations_creates_tables(db):
    await db.run_migrations()
    tables = await db.conn.execute_fetchall(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    table_names = [row[0] for row in tables]
    assert "schema_version" in table_names
    assert "proxies" in table_names
    assert "residential_config" in table_names
    assert "settings" in table_names
    assert "rotation_log" in table_names
    assert "request_log" in table_names
    assert "proxies_history" in table_names


@pytest.mark.asyncio
async def test_run_migrations_tracks_version(db):
    await db.run_migrations()
    rows = await db.conn.execute_fetchall(
        "SELECT version FROM schema_version ORDER BY version"
    )
    versions = [row[0] for row in rows]
    assert versions == [1]


@pytest.mark.asyncio
async def test_run_migrations_idempotent(db):
    await db.run_migrations()
    await db.run_migrations()
    rows = await db.conn.execute_fetchall(
        "SELECT COUNT(*) FROM schema_version"
    )
    assert rows[0][0] == 1


@pytest.mark.asyncio
async def test_run_migrations_seeds_settings(db):
    await db.run_migrations()
    rows = await db.conn.execute_fetchall(
        "SELECT key, value FROM settings ORDER BY key"
    )
    keys = [row[0] for row in rows]
    assert "proxy.port" in keys
    assert "rotation.strategy" in keys
    assert "health_check.test_url" in keys


@pytest.mark.asyncio
async def test_wal_mode_enabled(db):
    conn = await db.connect()
    row = await conn.execute_fetchall("PRAGMA journal_mode")
    assert row[0][0].upper() == "WAL"


@pytest.mark.asyncio
async def test_foreign_keys_enabled(db):
    conn = await db.connect()
    row = await conn.execute_fetchall("PRAGMA foreign_keys")
    assert row[0][0] == 1


@pytest.mark.asyncio
async def test_cleanup_request_log(db):
    await db.run_migrations()
    for i in range(5):
        await db.conn.execute(
            "INSERT INTO request_log (method, url, host, status_code, duration_ms) VALUES (?, ?, ?, ?, ?)",
            ("GET", f"http://example.com/{i}", "example.com", 200, 10),
        )
    await db.conn.commit()
    await db.cleanup_request_log(max_entries=3)
    remaining = await db.conn.execute_fetchall("SELECT COUNT(*) FROM request_log")
    assert remaining[0][0] == 3


@pytest.mark.asyncio
async def test_close_connection(db):
    await db.connect()
    await db.close()
    assert db._conn is None
    with pytest.raises(RuntimeError, match="not connected"):
        _ = db.conn
