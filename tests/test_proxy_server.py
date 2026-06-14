import asyncio

import pytest

from easyproxy.proxy.server import ProxyServer


@pytest.fixture
def proxy_server(isolate_config):
    server = ProxyServer()
    server.host = "127.0.0.1"
    server.port = 0
    return server


class TestProxyServer:
    @pytest.mark.asyncio
    async def test_start_stop(self, proxy_server):
        await proxy_server.start()
        assert proxy_server._server is not None
        assert proxy_server.active_connections == 0
        await proxy_server.stop()
        assert proxy_server._server is None

    @pytest.mark.asyncio
    async def test_accepts_connection(self, proxy_server):
        await proxy_server.start()
        port = proxy_server._server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(b"GET http://example.com/ HTTP/1.1\r\nHost: example.com\r\n\r\n")
        await writer.drain()

        response = b""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=3)
                if not chunk:
                    break
                response += chunk
        except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError):
            pass

        writer.close()
        await proxy_server.stop()

        assert b"HTTP/1.1" in response

    @pytest.mark.asyncio
    async def test_active_connection_count(self, proxy_server):
        await proxy_server.start()
        port = proxy_server._server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        await asyncio.sleep(0.1)
        assert proxy_server.active_connections >= 1
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

        await asyncio.sleep(0.1)
        await proxy_server.stop()

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, proxy_server):
        await proxy_server.start()
        port = proxy_server._server.sockets[0].getsockname()[1]

        connections = []
        for _ in range(3):
            r, w = await asyncio.open_connection("127.0.0.1", port)
            connections.append((r, w))

        await asyncio.sleep(0.05)
        assert proxy_server.active_connections >= 3

        for r, w in connections:
            w.close()
            try:
                await w.wait_closed()
            except Exception:
                pass

        await proxy_server.stop()
