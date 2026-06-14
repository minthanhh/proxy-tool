import structlog

from easyproxy.pool.manager import PoolManager

logger = structlog.get_logger(__name__)

SETTINGS_KEY = "rotation.current_proxy_id"


class RotationEngine:
    def __init__(self, manager: PoolManager):
        self._manager = manager

    async def rotate(self, reason: str = "manual", trigger: str = "api") -> dict:
        alive = await self._manager.conn.execute_fetchall(
            "SELECT * FROM proxies WHERE status = 'alive' ORDER BY id ASC"
        )
        if not alive:
            raise RuntimeError("No alive proxies available for rotation")

        rows = await self._manager.conn.execute_fetchall(
            "SELECT value FROM settings WHERE key = ?", (SETTINGS_KEY,)
        )
        current_id = int(rows[0][0]) if rows else None

        from_proxy = None
        to_proxy = None

        if current_id is None:
            to_proxy = dict(alive[0])
        else:
            ids = [dict(r)["id"] for r in alive]
            if current_id in ids:
                idx = ids.index(current_id)
                next_idx = (idx + 1) % len(ids)
                to_proxy = dict(alive[next_idx])
                from_proxy = dict(alive[idx])
            else:
                to_proxy = dict(alive[0])

        new_id = to_proxy["id"]
        await self._manager.conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            (SETTINGS_KEY, str(new_id)),
        )
        await self._manager.conn.execute(
            """INSERT INTO rotation_log (reason, trigger, from_proxy_id, from_proxy, to_proxy_id, to_proxy)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                reason,
                trigger,
                from_proxy["id"] if from_proxy else None,
                f"{from_proxy['address']}:{from_proxy['port']}" if from_proxy else None,
                to_proxy["id"],
                f"{to_proxy['address']}:{to_proxy['port']}",
            ),
        )
        await self._manager.conn.commit()
        logger.info("Rotation completed", from_id=from_proxy["id"] if from_proxy else None, to_id=new_id, reason=reason)
        return {
            "from": {"id": from_proxy["id"], "address": from_proxy["address"], "port": from_proxy["port"]} if from_proxy else None,
            "to": {"id": to_proxy["id"], "address": to_proxy["address"], "port": to_proxy["port"]},
        }
