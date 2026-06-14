import asyncio
import structlog

from easyproxy.proxy.errors import InvalidRequest, ProxyError, error_to_response
from easyproxy.proxy.upstream import UpstreamConnector

logger = structlog.get_logger(__name__)

TUNNEL_BUFFER_SIZE = 65536


async def handle_connect(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    request_line: bytes,
    headers: dict[str, str],
    upstream_connector: UpstreamConnector | None = None,
) -> None:
    parts = request_line.decode().strip().split(" ")
    if len(parts) < 2:
        raise InvalidRequest("Malformed CONNECT request")

    target = parts[1]
    if ":" not in target:
        raise InvalidRequest(f"Invalid CONNECT target: {target}")

    host, port_str = target.rsplit(":", 1)
    try:
        port = int(port_str)
    except ValueError:
        raise InvalidRequest(f"Invalid port in CONNECT target: {target}")

    connector = upstream_connector or _get_default_connector()

    try:
        remote_reader, remote_writer = await connector.create_tunnel(host, port)

        writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        await writer.drain()

        await _relay_bidirectional(reader, writer, remote_reader, remote_writer)

    except ProxyError as e:
        writer.write(error_to_response(e))
        await writer.drain()
    except Exception as e:
        logger.error("CONNECT tunnel error", error=str(e))
        writer.write(error_to_response(ProxyError("Tunnel failed", 502)))
        await writer.drain()


async def _relay_bidirectional(
    client_reader: asyncio.StreamReader,
    client_writer: asyncio.StreamWriter,
    remote_reader: asyncio.StreamReader,
    remote_writer: asyncio.StreamWriter,
) -> None:
    async def relay(src: asyncio.StreamReader, dst: asyncio.StreamWriter) -> None:
        try:
            while True:
                data = await asyncio.wait_for(
                    src.read(TUNNEL_BUFFER_SIZE),
                    timeout=600,
                )
                if not data:
                    break
                dst.write(data)
                await dst.drain()
        except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError, OSError):
            pass
        finally:
            try:
                dst.close()
            except Exception:
                pass

    await asyncio.gather(
        relay(client_reader, remote_writer),
        relay(remote_reader, client_writer),
    )


_connector: UpstreamConnector | None = None


def _get_default_connector() -> UpstreamConnector:
    global _connector
    if _connector is None:
        _connector = UpstreamConnector()
    return _connector
