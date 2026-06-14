from datetime import datetime, timezone

from fastapi import APIRouter, Request

from easyproxy import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request):
    app = request.app
    start_time: datetime | None = getattr(app.state, "start_time", None)
    uptime = 0
    if start_time:
        uptime = int((datetime.now(timezone.utc) - start_time).total_seconds())

    db = getattr(app.state, "db", None)
    db_ok = False
    if db:
        try:
            await db.conn.execute("SELECT 1")
            db_ok = True
        except Exception:
            pass

    status = "ok" if db_ok else "degraded"

    return {
        "status": status,
        "version": __version__,
        "uptime_seconds": uptime,
        "proxy_running": False,
        "pool": {"total": 0, "alive": 0, "dead": 0},
    }
