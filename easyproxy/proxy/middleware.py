import asyncio
import structlog

logger = structlog.get_logger(__name__)

BATCH_SIZE = 10
FLUSH_INTERVAL = 1.0


class RequestLogger:
    def __init__(self, db=None):
        self._db = db
        self._queue: asyncio.Queue = asyncio.Queue()
        self._task: asyncio.Task | None = None
        self._running = False
        self._stats = {
            "total_requests": 0,
            "total_bytes_sent": 0,
            "total_bytes_received": 0,
            "total_errors": 0,
        }

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._flush_loop())
        logger.info("Request logger started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            await self._flush_now()
        logger.info("Request logger stopped")

    async def log_request(
        self,
        method: str,
        url: str,
        host: str,
        status_code: int,
        duration_ms: int,
        bytes_sent: int,
        bytes_received: int,
        headers: dict | None = None,
        proxy_address: str | None = None,
        error: str | None = None,
    ):
        entry = {
            "method": method,
            "url": url,
            "host": host,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "bytes_sent": bytes_sent,
            "bytes_received": bytes_received,
            "proxy_address": proxy_address,
            "error": error,
            "user_agent": (headers or {}).get("User-Agent"),
            "content_type": (headers or {}).get("Content-Type"),
        }
        await self._queue.put(entry)

        self._stats["total_requests"] += 1
        self._stats["total_bytes_sent"] += bytes_sent
        self._stats["total_bytes_received"] += bytes_received
        if error:
            self._stats["total_errors"] += 1

    async def _flush_loop(self):
        while self._running:
            await asyncio.sleep(FLUSH_INTERVAL)
            await self._flush_now()

    async def _flush_now(self):
        if self._queue.empty():
            return
        if self._db is None:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except asyncio.QueueEmpty:
                    break
            return

        batch = []
        while not self._queue.empty() and len(batch) < BATCH_SIZE:
            try:
                batch.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break

        if not batch:
            return

        try:
            conn = await self._db.connect()
            for entry in batch:
                await conn.execute(
                    """INSERT INTO request_log
                       (method, url, host, status_code, duration_ms, bytes_sent, bytes_received, proxy_address, error, user_agent, content_type)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        entry["method"],
                        entry["url"],
                        entry["host"],
                        entry["status_code"],
                        entry["duration_ms"],
                        entry["bytes_sent"],
                        entry["bytes_received"],
                        entry["proxy_address"],
                        entry["error"],
                        entry["user_agent"],
                        entry["content_type"],
                    ),
                )
            await conn.commit()
            for _ in batch:
                self._queue.task_done()
            logger.debug("Flushed request log batch", count=len(batch))
        except Exception as e:
            logger.error("Failed to flush request log", error=str(e))
            for entry in batch:
                await self._queue.put(entry)


_middleware: RequestLogger | None = None


def get_middleware() -> RequestLogger | None:
    return _middleware


def set_middleware(mw: RequestLogger | None):
    global _middleware
    _middleware = mw
