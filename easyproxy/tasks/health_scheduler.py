import asyncio
from typing import Optional

import structlog

from easyproxy.pool.health import HealthCheckRunner
from easyproxy.pool.manager import PoolManager

logger = structlog.get_logger(__name__)


class HealthScheduler:
    def __init__(self, manager: PoolManager, interval_seconds: int = 60, test_url: str = "http://httpbin.org/ip", timeout_seconds: int = 10):
        self._runner = HealthCheckRunner(manager, test_url=test_url, timeout_seconds=timeout_seconds)
        self._interval = interval_seconds
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Health scheduler started", interval_seconds=self._interval)

    async def stop(self):
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("Health scheduler stopped")

    async def _run_loop(self):
        while True:
            try:
                await asyncio.sleep(self._interval)
                await self._runner.run_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check error", error=str(e))
