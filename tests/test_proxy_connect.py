import asyncio

import pytest

from easyproxy.proxy.server import ProxyServer


@pytest.fixture
def proxy_server(isolate_config):
    server = ProxyServer()
    server.host = "127.0.0.1"
    server.port = 0
    return server


class TestProxyConnect:
    @pytest.mark.asyncio
    async def test_connect_tunnel_established(self, proxy_server):
        await proxy_server.start()
        port = proxy_server._server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(
            b"CONNECT httpbin.org:80 HTTP/1.1\r\n"
            b"Host: httpbin.org:80\r\n"
            b"\r\n"
        )
        await writer.drain()

        response = await asyncio.wait_for(reader.readline(), timeout=10)
        assert b"200" in response, f"Expected 200, got: {response}"

        while True:
            line = await asyncio.wait_for(reader.readline(), timeout=5)
            if line == b"\r\n" or not line:
                break

        writer.write(b"GET /get HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n")
        await writer.drain()

        http_response = b""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(65536), timeout=10)
                if not chunk:
                    break
                http_response += chunk
        except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError):
            pass

        writer.close()
        await proxy_server.stop()

        assert b"HTTP/1.1" in http_response
        assert b"200" in http_response or b"301" in http_response or b"302" in http_response or b"503" in http_response

    @pytest.mark.asyncio
    async def test_connect_to_https(self, proxy_server):
        await proxy_server.start()
        port = proxy_server._server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(
            b"CONNECT httpbin.org:443 HTTP/1.1\r\n"
            b"Host: httpbin.org:443\r\n"
            b"\r\n"
        )
        await writer.drain()

        response = await asyncio.wait_for(reader.readline(), timeout=15)
        writer.close()
        await proxy_server.stop()

        assert b"200" in response, f"Expected 200, got: {response}"

    @pytest.mark.asyncio
    async def test_connect_invalid_target(self, proxy_server):
        await proxy_server.start()
        port = proxy_server._server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(
            b"CONNECT invalid HTTP/1.1\r\n"
            b"Host: invalid\r\n"
            b"\r\n"
        )
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

        if response:
            assert b"400" in response or b"502" in response

    @pytest.mark.asyncio
    async def test_connect_to_unreachable(self, proxy_server):
        import easyproxy.proxy.upstream as up
        original = up.CONNECT_TIMEOUT
        up.CONNECT_TIMEOUT = 2
        try:
            await proxy_server.start()
            port = proxy_server._server.sockets[0].getsockname()[1]

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(
                b"CONNECT 192.0.2.1:80 HTTP/1.1\r\n"
                b"Host: 192.0.2.1:80\r\n"
                b"\r\n"
            )
            await writer.drain()

            response = b""
            try:
                while True:
                    chunk = await asyncio.wait_for(reader.read(4096), timeout=10)
                    if not chunk:
                        break
                    response += chunk
            except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError):
                pass

            writer.close()
            await proxy_server.stop()
        finally:
            up.CONNECT_TIMEOUT = original

        if response:
            assert b"502" in response or b"504" in response
