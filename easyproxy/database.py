import aiosqlite
import structlog
from pathlib import Path
from easyproxy.config import load_config

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
logger = structlog.get_logger(__name__)


class Database:
    def __init__(self, db_path: str | None = None):
        cfg = load_config()
        self.db_path = db_path or cfg["database"]["path"]
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> aiosqlite.Connection:
        if self._conn is not None:
            return self._conn
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._conn

    async def run_migrations(self):
        await self.connect()
        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL,
                description TEXT
            )"""
        )
        current = await self.conn.execute_fetchall(
            "SELECT COALESCE(MAX(version), 0) FROM schema_version"
        )
        current_version = current[0][0] if current else 0

        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for mf in migration_files:
            version = int(mf.stem.split("_")[0])
            if version > current_version:
                sql = mf.read_text()
                await self.conn.executescript(sql)
                await self.conn.execute(
                    "INSERT INTO schema_version (version, applied_at, description) VALUES (?, datetime('now'), ?)",
                    (version, mf.name),
                )
                logger.info("Migration applied", migration=mf.name)
        await self.conn.commit()

    async def cleanup_request_log(self, max_entries: int = 10000):
        await self.conn.execute(
            "DELETE FROM request_log WHERE id NOT IN (SELECT id FROM request_log ORDER BY id DESC LIMIT ?)",
            (max_entries,),
        )
        await self.conn.commit()
