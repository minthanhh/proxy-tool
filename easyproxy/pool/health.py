import asyncio
import time
from typing import Optional

import structlog
import aiohttp

from easyproxy.pool.models import ProxyUpdate, ProxyStatus
from easyproxy.pool.manager import PoolManager

logger = structlog.get_logger(__name__)


class HealthCheckRunner:
    def __init__(
        self,
        manager: PoolManager,
        test_url: str = "http://httpbin.org/ip",
        timeout_seconds: int = 10,
        max_consecutive_errors: int = 3,
    ):
        self._manager = manager
        self._test_url = test_url
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._max_errors = max_consecutive_errors

    async def run_all(self) -> dict:
        proxies, total = await self._manager.list(per_page=10000)
        results = {"checked": 0, "alive": 0, "dead": 0, "errors": 0}
        if not proxies:
            return results

        semaphore = asyncio.Semaphore(10)
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            tasks = [self._check_one(proxy, session, semaphore) for proxy in proxies]
            for task in asyncio.as_completed(tasks):
                status = await task
                if status == "alive":
                    results["alive"] += 1
                    results["checked"] += 1
                elif status == "dead":
                    results["dead"] += 1
                    results["checked"] += 1
                else:
                    results["errors"] += 1
        return results

    async def run_single(self, proxy_id: int) -> Optional[dict]:
        proxy = await self._manager.get(proxy_id)
        if not proxy:
            return None
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            await self._check_one(proxy, session)
        return await self._manager.get(proxy_id)

    async def _check_one(
        self,
        proxy: dict,
        session: aiohttp.ClientSession,
        semaphore: Optional[asyncio.Semaphore] = None,
    ) -> str:
        if semaphore:
            async with semaphore:
                return await self._do_check(proxy, session)
        return await self._do_check(proxy, session)

    async def _do_check(self, proxy: dict, session: aiohttp.ClientSession) -> str:
        proxy_id = proxy["id"]
        proxy_url = f"http://{proxy['address']}:{proxy['port']}"
        start = time.monotonic()
        try:
            async with session.head(
                self._test_url,
                proxy=proxy_url,
                timeout=self._timeout,
            ) as resp:
                latency_ms = int((time.monotonic() - start) * 1000)
                update = ProxyUpdate(
                    status=ProxyStatus.ALIVE,
                    latency_ms=latency_ms,
                )
                await self._manager.update(proxy_id, update)
                await self._manager.conn.execute(
                    "UPDATE proxies SET success_count = success_count + 1, consecutive_errors = 0, last_checked_at = datetime('now') WHERE id = ?",
                    (proxy_id,),
                )
                await self._manager.conn.commit()
                logger.info("Health check passed", proxy_id=proxy_id, latency_ms=latency_ms)
                return "alive"
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
            latency_ms = int((time.monotonic() - start) * 1000)
            await self._manager.conn.execute(
                "UPDATE proxies SET error_count = error_count + 1, consecutive_errors = consecutive_errors + 1, latency_ms = ?, last_checked_at = datetime('now') WHERE id = ?",
                (latency_ms, proxy_id),
            )
            await self._manager.conn.commit()

            row = await self._manager.conn.execute_fetchall(
                "SELECT consecutive_errors FROM proxies WHERE id = ?",
                (proxy_id,),
            )
            consecutive = row[0][0] if row else 0

            if consecutive >= self._max_errors:
                update = ProxyUpdate(status=ProxyStatus.DEAD)
                await self._manager.update(proxy_id, update)
                logger.warning("Proxy marked dead", proxy_id=proxy_id, consecutive_errors=consecutive)
                return "dead"

            logger.info("Health check failed", proxy_id=proxy_id, error=str(e), consecutive_errors=consecutive)
            return "error"
