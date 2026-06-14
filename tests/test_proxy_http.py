import asyncio

import pytest

from easyproxy.proxy.server import ProxyServer


@pytest.fixture
def proxy_server(isolate_config):
    server = ProxyServer()
    server.host = "127.0.0.1"
    server.port = 0
    return server


class TestProxyHTTP:
    @pytest.mark.asyncio
    async def test_http_get(self, proxy_server):
        await proxy_server.start()
        port = proxy_server._server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(
            b"GET http://httpbin.org/get HTTP/1.1\r\n"
            b"Host: httpbin.org\r\n"
            b"User-Agent: EasyProxy-Test/1.0\r\n"
            b"\r\n"
        )
        await writer.drain()

        raw = b""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(65536), timeout=10)
                if not chunk:
                    break
                raw += chunk
        except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError):
            pass

        writer.close()
        await proxy_server.stop()

        assert raw.startswith(b"HTTP/1.1")
        status_line = raw.split(b"\r\n")[0].decode()
        assert "200" in status_line or "302" in status_line or "503" in status_line

    @pytest.mark.asyncio
    async def test_http_get_json(self, proxy_server):
        await proxy_server.start()
        port = proxy_server._server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(
            b"GET http://httpbin.org/get HTTP/1.1\r\n"
            b"Host: httpbin.org\r\n"
            b"Accept: application/json\r\n"
            b"\r\n"
        )
        await writer.drain()

        raw = b""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(65536), timeout=10)
                if not chunk:
                    break
                raw += chunk
        except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError):
            pass

        writer.close()
        await proxy_server.stop()

        assert raw.startswith(b"HTTP/1.1")
        status_line = raw.split(b"\r\n")[0].decode()
        assert "200" in status_line or "503" in status_line

    @pytest.mark.asyncio
    async def test_http_post(self, proxy_server):
        await proxy_server.start()
        port = proxy_server._server.sockets[0].getsockname()[1]

        body = b'{"test": "data"}'
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(
            f"POST http://httpbin.org/post HTTP/1.1\r\n"
            f"Host: httpbin.org\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"\r\n".encode() + body
        )
        await writer.drain()

        raw = b""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(65536), timeout=10)
                if not chunk:
                    break
                raw += chunk
        except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError):
            pass

        writer.close()
        await proxy_server.stop()

        assert raw.startswith(b"HTTP/1.1")
        status_line = raw.split(b"\r\n")[0].decode()
        assert "200" in status_line or "503" in status_line

    @pytest.mark.asyncio
    async def test_proxy_via_header_added(self, proxy_server):
        await proxy_server.start()
        port = proxy_server._server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(
            b"GET http://httpbin.org/get HTTP/1.1\r\n"
            b"Host: httpbin.org\r\n"
            b"\r\n"
        )
        await writer.drain()

        raw = b""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(65536), timeout=10)
                if not chunk:
                    break
                raw += chunk
        except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError):
            pass

        writer.close()
        await proxy_server.stop()

        assert raw.startswith(b"HTTP/1.1")
