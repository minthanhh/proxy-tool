import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from easyproxy.proxy.server import ProxyServer
from easyproxy.rotation.engine import RotationEngine
from easyproxy.pool.manager import PoolManager

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/proxy", tags=["proxy"])


def _get_manager(request: Request) -> PoolManager:
    db = getattr(request.app.state, "db", None)
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    return PoolManager(db)


def _get_engine(request: Request) -> RotationEngine:
    return RotationEngine(_get_manager(request))


class StartRequest(BaseModel):
    system_proxy: bool = False


@router.get("/status")
async def proxy_status(request: Request):
    server: ProxyServer | None = getattr(request.app.state, "proxy_server", None)
    if server is None:
        return {
            "running": False,
            "port": 8080,
            "current_ip": None,
            "current_proxy_id": None,
            "strategy": "round-robin",
            "uptime_seconds": 0,
            "requests_served": 0,
            "rate_limits_detected": 0,
            "rotations_performed": 0,
        }

    mgr = _get_manager(request)
    return {
        "running": True,
        "port": server.port,
        "current_ip": None,
        "current_proxy_id": None,
        "strategy": "round-robin",
        "uptime_seconds": 0,
        "requests_served": 0,
        "rate_limits_detected": 0,
        "rotations_performed": 0,
    }


@router.post("/start")
async def proxy_start(request: Request, body: StartRequest | None = None):
    server: ProxyServer | None = getattr(request.app.state, "proxy_server", None)
    if server is not None:
        raise HTTPException(status_code=409, detail="Proxy already running")

    server = ProxyServer()
    try:
        await server.start()
    except Exception as e:
        logger.error("Failed to start proxy", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start proxy: {e}")

    request.app.state.proxy_server = server
    logger.info("Proxy engine started via API")
    return {"running": True, "port": server.port, "current_ip": None}


@router.post("/stop")
async def proxy_stop(request: Request):
    server: ProxyServer | None = getattr(request.app.state, "proxy_server", None)
    if server is None:
        raise HTTPException(status_code=409, detail="Proxy not running")

    try:
        await server.stop()
    except Exception as e:
        logger.error("Failed to stop proxy", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to stop proxy: {e}")

    request.app.state.proxy_server = None
    logger.info("Proxy engine stopped via API")
    return {"running": False, "message": "Proxy stopped."}


@router.post("/rotate")
async def proxy_rotate(request: Request):
    server: ProxyServer | None = getattr(request.app.state, "proxy_server", None)
    if server is None:
        raise HTTPException(status_code=409, detail="Proxy not running")

    engine = _get_engine(request)
    try:
        result = await engine.rotate(reason="manual", trigger="api")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return result


@router.get("/logs")
async def proxy_logs(
    request: Request,
    page: int = 1,
    per_page: int = 100,
    status: int | None = None,
    method: str | None = None,
    proxy_address: str | None = None,
    since: str | None = None,
    until: str | None = None,
    search: str | None = None,
    rate_limited: bool | None = None,
):
    db = getattr(request.app.state, "db", None)
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    conditions = []
    params: list = []

    if status is not None:
        conditions.append("status_code = ?")
        params.append(status)
    if method:
        conditions.append("method = ?")
        params.append(method)
    if proxy_address:
        conditions.append("proxy_address = ?")
        params.append(proxy_address)
    if since:
        conditions.append("timestamp >= ?")
        params.append(since)
    if until:
        conditions.append("timestamp <= ?")
        params.append(until)
    if search:
        conditions.append("url LIKE ?")
        params.append(f"%{search}%")
    if rate_limited:
        conditions.append("rotated = 1")

    where = " AND ".join(conditions) if conditions else "1=1"
    offset = (page - 1) * per_page

    count_row = await db.conn.execute_fetchone(
        f"SELECT COUNT(*) FROM request_log WHERE {where}", params
    )
    total = count_row[0] if count_row else 0

    rows = await db.conn.execute_fetchall(
        f"SELECT * FROM request_log WHERE {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    )

    logs = []
    for row in rows:
        d = dict(row)
        logs.append({
            "id": d["id"],
            "timestamp": d["timestamp"],
            "method": d["method"],
            "url": d["url"],
            "status_code": d["status_code"],
            "proxy_id": d.get("proxy_id"),
            "proxy_address": d.get("proxy_address"),
            "duration_ms": d["duration_ms"],
            "bytes_sent": d.get("bytes_sent", 0),
            "bytes_received": d.get("bytes_received", 0),
            "user_agent": d.get("user_agent"),
            "rotated": bool(d.get("rotated", False)),
        })

    return {"total": total, "page": page, "per_page": per_page, "logs": logs}


@router.get("/logs/export")
async def proxy_logs_export(
    request: Request,
    since: str | None = None,
    until: str | None = None,
    format: str = "csv",
):
    from fastapi.responses import StreamingResponse
    import io, csv

    db = getattr(request.app.state, "db", None)
    if not db:
        raise HTTPException(status_code=503)

    conditions = []
    params: list = []
    if since:
        conditions.append("timestamp >= ?")
        params.append(since)
    if until:
        conditions.append("timestamp <= ?")
        params.append(until)
    where = " AND ".join(conditions) if conditions else "1=1"

    rows = await db.conn.execute_fetchall(
        f"SELECT * FROM request_log WHERE {where} ORDER BY id ASC", params
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "timestamp", "method", "url", "status_code", "proxy_address", "duration_ms", "rotated"])
    for row in rows:
        d = dict(row)
        writer.writerow([
            d["id"], d["timestamp"], d["method"], d["url"],
            d["status_code"], d.get("proxy_address", ""),
            d["duration_ms"], d.get("rotated", 0),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=easyproxy-logs.csv"},
    )
