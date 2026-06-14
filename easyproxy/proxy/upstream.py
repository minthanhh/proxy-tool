import asyncio
import structlog
from urllib.parse import urlparse

import aiohttp

from easyproxy.proxy.errors import (
    UpstreamUnreachable,
    UpstreamTimeout,
    DNSResolutionFailed,
    ConnectionRefused,
)

logger = structlog.get_logger(__name__)

HTTP_TIMEOUT = 30.0
CONNECT_TIMEOUT = 10.0


def parse_proxy_url(proxy_url: str | None) -> dict | None:
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    result: dict = {
        "protocol": parsed.scheme,
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or (1080 if parsed.scheme == "socks5" else 8080),
    }
    if parsed.username:
        result["username"] = parsed.username
    if parsed.password:
        result["password"] = parsed.password
    return result


class UpstreamConnector:
    def __init__(self):
        self._session: aiohttp.ClientSession | None = None

    async def start(self):
        connector = aiohttp.TCPConnector(verify_ssl=False, limit=100)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT),
        )

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

    async def forward_http(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes = b"",
        proxy: str | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        if self._session is None:
            await self.start()

        parsed = urlparse(url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        try:
            kwargs: dict = {
                "headers": headers,
                "timeout": aiohttp.ClientTimeout(total=HTTP_TIMEOUT),
            }
            if body:
                kwargs["data"] = body
            if proxy:
                kwargs["proxy"] = proxy

            async with self._session.request(method, url, **kwargs) as resp:
                response_headers = dict(resp.headers)
                response_body = await resp.read()
                logger.info(
                    "HTTP forward complete",
                    method=method,
                    url=url,
                    status=resp.status,
                    bytes=len(response_body),
                )
                return resp.status, response_headers, response_body

        except aiohttp.ClientConnectorError as e:
            raise UpstreamUnreachable(host, port, str(e))
        except asyncio.TimeoutError:
            raise UpstreamTimeout(host, port, HTTP_TIMEOUT)
        except OSError as e:
            raise ConnectionRefused(host, port)

    async def create_tunnel(
        self,
        host: str,
        port: int,
        proxy: str | None = None,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        if proxy:
            return await self._tunnel_via_proxy(host, port, proxy)

        try:
            await asyncio.wait_for(
                asyncio.get_event_loop().getaddrinfo(host, port),
                timeout=CONNECT_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise DNSResolutionFailed(host)
        except OSError as e:
            raise DNSResolutionFailed(host)

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=CONNECT_TIMEOUT,
            )
            return reader, writer
        except asyncio.TimeoutError:
            raise UpstreamTimeout(host, port, CONNECT_TIMEOUT)
        except ConnectionRefusedError:
            raise ConnectionRefused(host, port)
        except OSError as e:
            raise UpstreamUnreachable(host, port, str(e))

    async def _tunnel_via_proxy(
        self,
        host: str,
        port: int,
        proxy: str,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        proxy_info = parse_proxy_url(proxy)
        if not proxy_info:
            raise UpstreamUnreachable(host, port, "Invalid proxy URL")

        proxy_host = proxy_info["host"]
        proxy_port = proxy_info["port"]
        protocol = proxy_info["protocol"]

        if protocol == "socks5":
            return await self._socks5_tunnel(
                host, port, proxy_host, proxy_port, proxy_info
            )
        elif protocol in ("http", "https"):
            return await self._http_proxy_tunnel(
                host, port, proxy_host, proxy_port, proxy_info
            )
        else:
            raise UpstreamUnreachable(host, port, f"Unsupported proxy protocol: {protocol}")

    async def _http_proxy_tunnel(
        self,
        host: str,
        port: int,
        proxy_host: str,
        proxy_port: int,
        proxy_info: dict,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        try:
            remote_reader, remote_writer = await asyncio.wait_for(
                asyncio.open_connection(proxy_host, proxy_port),
                timeout=CONNECT_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise UpstreamTimeout(proxy_host, proxy_port, CONNECT_TIMEOUT)
        except (ConnectionRefusedError, OSError) as e:
            raise UpstreamUnreachable(proxy_host, proxy_port, str(e))

        auth = ""
        if "username" in proxy_info and "password" in proxy_info:
            import base64
            credentials = f"{proxy_info['username']}:{proxy_info['password']}"
            auth = f"Proxy-Authorization: Basic {base64.b64encode(credentials.encode()).decode()}\r\n"

        connect_req = (
            f"CONNECT {host}:{port} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"{auth}\r\n"
        )
        remote_writer.write(connect_req.encode())
        await remote_writer.drain()

        response = await asyncio.wait_for(
            remote_reader.readline(), timeout=CONNECT_TIMEOUT
        )
        while True:
            line = await asyncio.wait_for(
                remote_reader.readline(), timeout=CONNECT_TIMEOUT
            )
            if line == b"\r\n" or not line:
                break

        if b"200" not in response:
            remote_writer.close()
            raise UpstreamUnreachable(host, port, f"Proxy CONNECT failed: {response.decode().strip()}")

        return remote_reader, remote_writer

    async def _socks5_tunnel(
        self,
        host: str,
        port: int,
        proxy_host: str,
        proxy_port: int,
        proxy_info: dict,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(proxy_host, proxy_port),
                timeout=CONNECT_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise UpstreamTimeout(proxy_host, proxy_port, CONNECT_TIMEOUT)
        except (ConnectionRefusedError, OSError) as e:
            raise UpstreamUnreachable(proxy_host, proxy_port, str(e))

        writer.write(b"\x05\x01\x00")
        await writer.drain()
        auth_response = await asyncio.wait_for(reader.readexactly(2), timeout=CONNECT_TIMEOUT)
        if auth_response != b"\x05\x00":
            writer.close()
            raise UpstreamUnreachable(proxy_host, proxy_port, "SOCKS5 auth method negotiation failed")

        import ipaddress
        import socket
        try:
            ip = ipaddress.ip_address(host)
            atyp = b"\x01"
            host_bytes = ip.packed
        except ValueError:
            atyp = b"\x03"
            host_bytes = bytes([len(host)]) + host.encode()

        port_bytes = port.to_bytes(2, "big")
        connect_request = b"\x05\x01\x00" + atyp + host_bytes + port_bytes
        writer.write(connect_request)
        await writer.drain()

        connect_response = await asyncio.wait_for(
            reader.readexactly(4), timeout=CONNECT_TIMEOUT
        )
        if connect_response[1] != 0x00:
            writer.close()
            raise UpstreamUnreachable(host, port, f"SOCKS5 connection failed: code {connect_response[1]}")

        atyp = connect_response[3]
        if atyp == 0x01:
            await reader.readexactly(6)
        elif atyp == 0x03:
            domain_len = ord(await reader.readexactly(1))
            await reader.readexactly(domain_len + 2)
        elif atyp == 0x04:
            await reader.readexactly(18)

        return reader, writer
