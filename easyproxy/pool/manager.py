from enum import Enum
import structlog
from typing import Optional

from easyproxy.database import Database
from easyproxy.pool.models import ProxyCreate, ProxyUpdate

logger = structlog.get_logger(__name__)

PAGE_SIZE = 50


class PoolManager:
    def __init__(self, db: Database):
        self._db = db

    @property
    def conn(self):
        return self._db.conn

    async def add(self, proxy: ProxyCreate) -> int:
        existing = await self.conn.execute_fetchall(
            "SELECT id FROM proxies WHERE address = ? AND port = ?",
            (proxy.address, proxy.port),
        )
        if existing:
            raise ValueError(f"Proxy {proxy.address}:{proxy.port} already exists")

        cursor = await self.conn.execute(
            """INSERT INTO proxies (address, port, protocol, username, password, region, source, residential_provider)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                proxy.address,
                proxy.port,
                proxy.protocol.value,
                proxy.username,
                proxy.password,
                proxy.region,
                proxy.source,
                proxy.residential_provider,
            ),
        )
        await self._db.conn.commit()
        proxy_id = cursor.lastrowid
        if proxy_id is None:
            raise RuntimeError("Failed to insert proxy")
        logger.info("Proxy added", proxy_id=proxy_id, address=proxy.address, port=proxy.port)
        return proxy_id

    async def get(self, proxy_id: int) -> Optional[dict]:
        rows = await self.conn.execute_fetchall(
            "SELECT * FROM proxies WHERE id = ?", (proxy_id,)
        )
        if not rows:
            return None
        return dict(rows[0])

    async def list(
        self,
        page: int = 1,
        per_page: int = PAGE_SIZE,
        protocol: Optional[str] = None,
        region: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        conditions: list[str] = []
        params: list = []

        if protocol:
            conditions.append("protocol = ?")
            params.append(protocol)
        if region:
            conditions.append("region = ?")
            params.append(region)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if source:
            conditions.append("source = ?")
            params.append(source)

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        count_rows = await self.conn.execute_fetchall(
            f"SELECT COUNT(*) FROM proxies {where}", params
        )
        total = count_rows[0][0] if count_rows else 0

        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        rows = await self.conn.execute_fetchall(
            f"SELECT * FROM proxies {where} ORDER BY id DESC LIMIT ? OFFSET ?",
            params,
        )
        return [dict(r) for r in rows], total

    async def update(self, proxy_id: int, updates: ProxyUpdate) -> bool:
        existing = await self.get(proxy_id)
        if not existing:
            return False

        fields: list[str] = []
        params: list = []

        update_data = updates.model_dump(exclude_none=True)
        for key, value in update_data.items():
            if key in ("address", "port", "protocol", "username", "password", "region", "status"):
                if isinstance(value, Enum):
                    value = value.value
                fields.append(f"{key} = ?")
                params.append(value)

        if not fields:
            return True

        fields.append("updated_at = datetime('now')")
        params.append(proxy_id)

        await self.conn.execute(
            f"UPDATE proxies SET {', '.join(fields)} WHERE id = ?",
            params,
        )
        await self._db.conn.commit()
        logger.info("Proxy updated", proxy_id=proxy_id)
        return True

    async def remove(self, proxy_id: int) -> bool:
        existing = await self.get(proxy_id)
        if not existing:
            return False
        await self.conn.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
        await self._db.conn.commit()
        logger.info("Proxy removed", proxy_id=proxy_id)
        return True

    async def stats(self) -> dict:
        total_rows = await self.conn.execute_fetchall("SELECT COUNT(*) FROM proxies")
        total = total_rows[0][0] if total_rows else 0

        by_status = await self.conn.execute_fetchall(
            "SELECT status, COUNT(*) as count FROM proxies GROUP BY status"
        )
        by_protocol = await self.conn.execute_fetchall(
            "SELECT protocol, COUNT(*) as count FROM proxies GROUP BY protocol"
        )

        alive_rows = await self.conn.execute_fetchall(
            "SELECT COUNT(*) FROM proxies WHERE status = 'alive'"
        )
        alive = alive_rows[0][0] if alive_rows else 0
        dead = total - alive

        return {
            "total": total,
            "alive": alive,
            "dead": dead,
            "by_status": {row[0]: row[1] for row in by_status},
            "by_protocol": {row[0]: row[1] for row in by_protocol},
        }
