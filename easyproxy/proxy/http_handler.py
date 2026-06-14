import structlog
from urllib.parse import urlparse

from easyproxy.proxy.headers import prepare_request_headers
from easyproxy.proxy.errors import InvalidRequest
from easyproxy.proxy.upstream import UpstreamConnector
from easyproxy.proxy.middleware import get_middleware

logger = structlog.get_logger(__name__)


async def handle_http_request(
    reader: object,
    writer: asyncio.StreamWriter,
    request_line: bytes,
    headers: dict[str, str],
    body: bytes,
    upstream_connector: UpstreamConnector | None = None,
) -> None:
    import asyncio

    parts = request_line.decode().strip().split(" ")
    if len(parts) < 2:
        raise InvalidRequest("Malformed request line")

    method = parts[0]
    url = parts[1]
    version = parts[2] if len(parts) > 2 else "HTTP/1.1"

    parsed = urlparse(url)
    if not parsed.hostname:
        raise InvalidRequest(f"Invalid URL: {url}")

    host = parsed.hostname
    target_port = parsed.port or (443 if parsed.scheme == "https" else 80)

    connector = upstream_connector or _get_default_connector()

    clean_headers = prepare_request_headers(headers)
    if "Host" not in clean_headers:
        clean_headers["Host"] = host

    try:
        status, response_headers, response_body = await connector.forward_http(
            method=method,
            url=url,
            headers=clean_headers,
            body=body,
        )

        response_line = f"HTTP/1.1 {status} {_status_reason(status)}\r\n"
        writer.write(response_line.encode())
        for key, value in response_headers.items():
            writer.write(f"{key}: {value}\r\n".encode())
        writer.write(b"\r\n")
        writer.write(response_body)
        await writer.drain()

        middleware = get_middleware()
        if middleware:
            await middleware.log_request(
                method=method,
                url=url,
                host=host,
                status_code=status,
                duration_ms=0,
                bytes_sent=len(body),
                bytes_received=len(response_body),
                headers=headers,
            )

    except Exception:
        raise


def _status_reason(status: int) -> str:
    reasons = {
        200: "OK", 201: "Created", 204: "No Content",
        301: "Moved Permanently", 302: "Found", 304: "Not Modified",
        400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
        404: "Not Found", 405: "Method Not Allowed", 408: "Request Timeout",
        429: "Too Many Requests",
        500: "Internal Server Error", 502: "Bad Gateway",
        503: "Service Unavailable", 504: "Gateway Timeout",
    }
    return reasons.get(status, "Unknown")


_connector: UpstreamConnector | None = None


def _get_default_connector() -> UpstreamConnector:
    global _connector
    if _connector is None:
        _connector = UpstreamConnector()
    return _connector
