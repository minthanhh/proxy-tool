from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from easyproxy.pool.models import ProxyCreate, ProxyUpdate
from easyproxy.pool.manager import PoolManager
from easyproxy.pool.importer import Importer
from easyproxy.pool.health import HealthCheckRunner


class ImportRequest(BaseModel):
    format: str
    content: str

router = APIRouter(prefix="/api/v1/pool", tags=["pool"])


def _get_manager(request: Request) -> PoolManager:
    db = getattr(request.app.state, "db", None)
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    return PoolManager(db)


@router.get("")
async def list_proxies(
    request: Request,
    page: int = 1,
    per_page: int = 50,
    protocol: Optional[str] = None,
    region: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
):
    manager = _get_manager(request)
    proxies, total = await manager.list(
        page=page, per_page=per_page,
        protocol=protocol, region=region,
        status=status, source=source,
    )
    return {
        "data": proxies,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


@router.post("", status_code=201)
async def add_proxy(request: Request, body: ProxyCreate):
    manager = _get_manager(request)
    try:
        proxy_id = await manager.add(body)
        proxy = await manager.get(proxy_id)
        return {"data": proxy}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/stats")
async def pool_stats(request: Request):
    manager = _get_manager(request)
    return await manager.stats()


@router.get("/{proxy_id}")
async def get_proxy(request: Request, proxy_id: int):
    manager = _get_manager(request)
    proxy = await manager.get(proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return {"data": proxy}


@router.put("/{proxy_id}")
async def update_proxy(request: Request, proxy_id: int, body: ProxyUpdate):
    manager = _get_manager(request)
    success = await manager.update(proxy_id, body)
    if not success:
        raise HTTPException(status_code=404, detail="Proxy not found")
    proxy = await manager.get(proxy_id)
    return {"data": proxy}


@router.delete("/{proxy_id}")
async def delete_proxy(request: Request, proxy_id: int):
    manager = _get_manager(request)
    success = await manager.remove(proxy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return {"message": "Proxy deleted"}


@router.post("/test", status_code=200)
async def test_proxies(request: Request, proxy_id: Optional[int] = None):
    manager = _get_manager(request)
    config = request.app.state.config if hasattr(request.app.state, "config") else {}
    hc = config.get("health_check", {})
    runner = HealthCheckRunner(
        manager,
        test_url=hc.get("test_url", "http://httpbin.org/ip"),
        timeout_seconds=hc.get("timeout_seconds", 10),
    )
    if proxy_id:
        result = await runner.run_single(proxy_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Proxy not found")
        return {"data": result}
    results = await runner.run_all()
    return results


@router.post("/import", status_code=200)
async def import_proxies(request: Request, body: ImportRequest):
    if body.format not in ("txt", "csv"):
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'txt' or 'csv'")
    manager = _get_manager(request)
    importer = Importer(manager)
    if body.format == "txt":
        result = await importer.import_txt(body.content)
    else:
        result = await importer.import_csv(body.content)
    return result
