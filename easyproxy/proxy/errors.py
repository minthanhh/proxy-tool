import structlog

logger = structlog.get_logger(__name__)


class ProxyError(Exception):
    def __init__(self, message: str, status_code: int = 502, detail: str | None = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(self.message)


class UpstreamUnreachable(ProxyError):
    def __init__(self, host: str, port: int, detail: str | None = None):
        self.host = host
        self.port = port
        super().__init__(
            message=f"Upstream {host}:{port} unreachable",
            status_code=502,
            detail=detail or f"Could not connect to upstream {host}:{port}",
        )


class UpstreamTimeout(ProxyError):
    def __init__(self, host: str, port: int, timeout: float):
        self.host = host
        self.port = port
        super().__init__(
            message=f"Upstream {host}:{port} timed out after {timeout}s",
            status_code=504,
            detail=f"Connection to {host}:{port} timed out",
        )


class InvalidRequest(ProxyError):
    def __init__(self, detail: str = "Invalid request"):
        super().__init__(message=detail, status_code=400, detail=detail)


class TooManyConnections(ProxyError):
    def __init__(self, max_connections: int):
        super().__init__(
            message=f"Too many connections (max {max_connections})",
            status_code=429,
            detail=f"Maximum concurrent connections ({max_connections}) exceeded",
        )


class DNSResolutionFailed(ProxyError):
    def __init__(self, host: str):
        super().__init__(
            message=f"DNS resolution failed for {host}",
            status_code=502,
            detail=f"Could not resolve {host}",
        )


class ConnectionRefused(ProxyError):
    def __init__(self, host: str, port: int):
        super().__init__(
            message=f"Connection refused by {host}:{port}",
            status_code=502,
            detail=f"Connection refused",
        )


def error_to_response(error: ProxyError) -> bytes:
    body = (
        f"<html><body><h1>{error.status_code} {error.message}</h1>"
        f"<p>{error.detail}</p></body></html>"
    )
    return (
        f"HTTP/1.1 {error.status_code} {error.message}\r\n"
        f"Content-Type: text/html\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
        f"{body}"
    ).encode()
