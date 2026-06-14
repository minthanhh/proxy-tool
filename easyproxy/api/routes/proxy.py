from fastapi import APIRouter, HTTPException, Request

from easyproxy.pool.manager import PoolManager
from easyproxy.rotation.engine import RotationEngine
from easyproxy.api.events import get_event_bus

router = APIRouter(prefix="/api/v1/proxy", tags=["proxy"])


def _get_manager(request: Request) -> PoolManager:
    db = getattr(request.app.state, "db", None)
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    return PoolManager(db)


@router.post("/rotate", status_code=200)
async def rotate(request: Request):
    manager = _get_manager(request)
    engine = RotationEngine(manager)
    try:
        result = await engine.rotate(reason="manual", trigger="api")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    bus = get_event_bus()
    await bus.publish({
        "type": "proxy_rotated",
        "data": result,
    })
    return result
