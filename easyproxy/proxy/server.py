import asyncio
import structlog

from easyproxy.config import load_config
from easyproxy.proxy.http_handler import handle_http_request
from easyproxy.proxy.connect import handle_connect
from easyproxy.proxy.errors import ProxyError, TooManyConnections, error_to_response
from easyproxy.proxy.upstream import UpstreamConnector
from easyproxy.proxy.middleware import get_middleware, set_middleware, RequestLogger

logger = structlog.get_logger(__name__)

MAX_CONNECTIONS = 1000


class ProxyServer:
    def __init__(self):
        cfg = load_config()
        self.host = cfg["proxy"]["bind_address"]
        self.port = cfg["proxy"]["port"]
        self.max_connections = MAX_CONNECTIONS
        self._server: asyncio.AbstractServer | None = None
        self._active_connections = 0
        self._connection_lock = asyncio.Lock()
        self._upstream: UpstreamConnector | None = None
        self._middleware: RequestLogger | None = None

    @property
    def active_connections(self) -> int:
        return self._active_connections

    async def start(self):
        self._upstream = UpstreamConnector()
        await self._upstream.start()

        self._middleware = RequestLogger()
        set_middleware(self._middleware)
        await self._middleware.start()

        self._server = await asyncio.start_server(
            self._handle_connection,
            host=self.host,
            port=self.port,
        )
        logger.info(
            "Proxy server started",
            host=self.host,
            port=self.port,
            max_connections=self.max_connections,
        )

    async def stop(self):
        if self._middleware:
            await self._middleware.stop()

        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            logger.info("Proxy server stopped")

        if self._upstream:
            await self._upstream.close()

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        async with self._connection_lock:
            if self._active_connections >= self.max_connections:
                try:
                    writer.write(
                        error_to_response(
                            TooManyConnections(self.max_connections)
                        )
                    )
                    await writer.drain()
                except Exception:
                    pass
                finally:
                    try:
                        writer.close()
                    except Exception:
                        pass
                return
            self._active_connections += 1

        try:
            request_line = await asyncio.wait_for(
                reader.readline(), timeout=30
            )
            if not request_line:
                return

            headers: dict[str, str] = {}
            while True:
                line = await asyncio.wait_for(
                    reader.readline(), timeout=30
                )
                if line == b"\r\n" or not line:
                    break
                decoded = line.decode("utf-8", errors="replace").strip()
                if ":" in decoded:
                    key, _, value = decoded.partition(":")
                    headers[key.strip()] = value.strip()

            content_length_str = headers.get("Content-Length", "0")
            content_length = 0
            try:
                content_length = int(content_length_str)
            except (ValueError, TypeError):
                pass

            body = b""
            if content_length > 0:
                body = await asyncio.wait_for(
                    reader.readexactly(content_length), timeout=30
                )

            if request_line.startswith(b"CONNECT "):
                await handle_connect(
                    reader, writer, request_line, headers, self._upstream
                )
            else:
                await handle_http_request(
                    reader, writer, request_line, headers, body, self._upstream
                )

        except asyncio.TimeoutError:
            logger.warning("Connection timed out")
            try:
                writer.write(
                    error_to_response(ProxyError("Request Timeout", 408))
                )
                await writer.drain()
            except Exception:
                pass
        except ProxyError as e:
            try:
                writer.write(error_to_response(e))
                await writer.drain()
            except Exception:
                pass
        except Exception as e:
            logger.error("Unhandled connection error", error=str(e))
            try:
                writer.write(
                    error_to_response(
                        ProxyError("Internal Server Error", 500)
                    )
                )
                await writer.drain()
            except Exception:
                pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            async with self._connection_lock:
                self._active_connections -= 1
