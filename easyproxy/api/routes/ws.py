import asyncio

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from easyproxy.api.events import get_event_bus

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    event_bus = get_event_bus()
    queue = event_bus.subscribe()

    await websocket.send_json({"type": "ping"})

    async def listen():
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
        except (WebSocketDisconnect, Exception):
            pass

    async def emit():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    await websocket.send_json(event)
                except asyncio.TimeoutError:
                    await websocket.send_json({"type": "ping"})
        except (WebSocketDisconnect, Exception):
            pass

    try:
        await asyncio.gather(listen(), emit())
    except Exception:
        pass
    finally:
        event_bus.unsubscribe(queue)
        logger.debug("WebSocket client disconnected")
