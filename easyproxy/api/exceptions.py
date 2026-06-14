from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class EasyProxyException(Exception):
    def __init__(
        self,
        status_code: int,
        title: str,
        detail: str,
        type_: str | None = None,
    ):
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.type_ = type_ or f"https://errors.easyproxy.app/{status_code}"


class NotFoundError(EasyProxyException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            404, "Not Found", detail, "https://errors.easyproxy.app/not-found"
        )


class ConflictError(EasyProxyException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(
            409, "Conflict", detail, "https://errors.easyproxy.app/conflict"
        )


class ValidationError(EasyProxyException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            422, "Validation Error", detail, "https://errors.easyproxy.app/validation-error"
        )


class ProxyNotRunningError(EasyProxyException):
    def __init__(self):
        super().__init__(
            409,
            "Proxy Not Running",
            "Cannot perform action: proxy is not running",
            "https://errors.easyproxy.app/proxy-not-running",
        )


class ProxyAlreadyRunningError(EasyProxyException):
    def __init__(self):
        super().__init__(
            409,
            "Proxy Already Running",
            "Cannot start proxy: already listening on port",
            "https://errors.easyproxy.app/proxy-already-running",
        )


class NoAliveProxyError(EasyProxyException):
    def __init__(self):
        super().__init__(
            503,
            "No Alive Proxies",
            "No alive proxies available in the pool",
            "https://errors.easyproxy.app/no-alive-proxies",
        )


async def easyproxy_exception_handler(request: Request, exc: EasyProxyException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": exc.type_,
            "title": exc.title,
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": str(request.url.path),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://errors.easyproxy.app/internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred",
            "instance": str(request.url.path),
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    status_code = exc.status_code
    return JSONResponse(
        status_code=status_code,
        content={
            "type": f"https://errors.easyproxy.app/http-{status_code}",
            "title": exc.detail or "HTTP Error",
            "status": status_code,
            "detail": exc.detail,
            "instance": str(request.url.path),
        },
    )
