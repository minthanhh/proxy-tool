from contextlib import asynccontextmanager
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from starlette.exceptions import HTTPException as StarletteHTTPException

from easyproxy import __version__
from easyproxy.api.exceptions import (
    EasyProxyException,
    easyproxy_exception_handler,
    generic_exception_handler,
    http_exception_handler,
)
from easyproxy.api.middleware import RequestIDMiddleware, RequestTimingMiddleware
from easyproxy.api.routes.health import router as health_router
from easyproxy.api.routes.ws import router as ws_router
from easyproxy.api.routes.pool import router as pool_router
from easyproxy.api.routes.proxy import router as proxy_router
from easyproxy.config import load_config
from easyproxy.database import Database
from easyproxy.logging import setup_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config()
    setup_logging(cfg)

    db = Database()
    await db.connect()
    await db.run_migrations()
    await db.cleanup_request_log(cfg["logs"]["max_entries"])
    app.state.db = db
    app.state.start_time = datetime.now(timezone.utc)
    app.state.config = cfg

    logger.info("EasyProxy backend started", version=__version__)
    yield

    await db.close()
    logger.info("EasyProxy backend stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="EasyProxy",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
    )

    app.add_exception_handler(EasyProxyException, easyproxy_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestTimingMiddleware)

    app.include_router(health_router)
    app.include_router(ws_router)
    app.include_router(pool_router)
    app.include_router(proxy_router)

    return app
