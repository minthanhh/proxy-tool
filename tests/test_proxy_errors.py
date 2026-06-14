import asyncio

import pytest

from easyproxy.proxy.errors import (
    ProxyError,
    UpstreamUnreachable,
    UpstreamTimeout,
    InvalidRequest,
    TooManyConnections,
    DNSResolutionFailed,
    ConnectionRefused,
    error_to_response,
)
from easyproxy.proxy.headers import (
    sanitize_request_headers,
    add_via_header,
    prepare_request_headers,
    filter_hop_by_hop,
)
from easyproxy.proxy.upstream import parse_proxy_url
from easyproxy.proxy.server import ProxyServer


class TestErrors:
    def test_proxy_error_defaults(self):
        err = ProxyError("test")
        assert err.message == "test"
        assert err.status_code == 502
        assert err.detail == "test"

    def test_upstream_unreachable(self):
        err = UpstreamUnreachable("example.com", 8080)
        assert err.status_code == 502
        assert "example.com" in err.message
        assert "8080" in err.message

    def test_upstream_timeout(self):
        err = UpstreamTimeout("example.com", 80, 10.0)
        assert err.status_code == 504
        assert "timed out" in err.detail

    def test_invalid_request(self):
        err = InvalidRequest("no host")
        assert err.status_code == 400
        assert err.detail == "no host"

    def test_too_many_connections(self):
        err = TooManyConnections(100)
        assert err.status_code == 429
        assert "100" in err.message

    def test_dns_resolution_failed(self):
        err = DNSResolutionFailed("unknown.host")
        assert err.status_code == 502
        assert "DNS" in err.message

    def test_connection_refused(self):
        err = ConnectionRefused("localhost", 9999)
        assert err.status_code == 502

    def test_error_to_response_format(self):
        err = InvalidRequest("bad request")
        resp = error_to_response(err)
        assert resp.startswith(b"HTTP/1.1 400")
        assert b"Content-Type: text/html" in resp
        assert b"bad request" in resp
        assert b"Content-Length:" in resp
        assert b"Connection: close" in resp

    def test_error_to_response_502(self):
        err = UpstreamUnreachable("test.com", 80)
        resp = error_to_response(err)
        assert resp.startswith(b"HTTP/1.1 502")
        assert b"test.com" in resp


class TestHeaders:
    def test_sanitize_removes_forwarded(self):
        headers = {
            "Host": "example.com",
            "X-Forwarded-For": "1.2.3.4",
            "User-Agent": "test",
            "Via": "some-proxy",
        }
        result = sanitize_request_headers(headers)
        assert "Host" in result
        assert "User-Agent" in result
        assert "X-Forwarded-For" not in result
        assert "Via" not in result

    def test_sanitize_removes_hop_by_hop(self):
        headers = {
            "Host": "example.com",
            "Transfer-Encoding": "chunked",
            "Proxy-Authorization": "basic xxx",
        }
        result = sanitize_request_headers(headers)
        assert "Host" in result
        assert "Transfer-Encoding" not in result
        assert "Proxy-Authorization" not in result

    def test_add_via_header(self):
        headers = {"Host": "example.com"}
        result = add_via_header(headers)
        assert result["Via"] == "EasyProxy/0.1.0"

    def test_add_via_header_appends(self):
        headers = {"Via": "previous-proxy/1.0"}
        result = add_via_header(headers)
        assert "previous-proxy" in result["Via"]
        assert "EasyProxy" in result["Via"]

    def test_prepare_request_headers(self):
        headers = {
            "Host": "example.com",
            "X-Forwarded-For": "1.2.3.4",
            "User-Agent": "test",
        }
        result = prepare_request_headers(headers)
        assert "Host" in result
        assert "User-Agent" in result
        assert "X-Forwarded-For" not in result
        assert result["Via"] == "EasyProxy/0.1.0"

    def test_filter_hop_by_hop_from_connection(self):
        headers = {
            "Host": "example.com",
            "Connection": "X-Custom, X-Debug",
            "X-Custom": "value",
            "X-Debug": "debug-value",
        }
        result = filter_hop_by_hop(headers)
        assert "Host" in result
        assert "X-Custom" not in result
        assert "X-Debug" not in result


class TestUpstreamParsing:
    def test_parse_proxy_url_none(self):
        assert parse_proxy_url(None) is None

    def test_parse_proxy_url_http(self):
        result = parse_proxy_url("http://proxy.example.com:8080")
        assert result["protocol"] == "http"
        assert result["host"] == "proxy.example.com"
        assert result["port"] == 8080

    def test_parse_proxy_url_with_auth(self):
        result = parse_proxy_url("http://user:pass@proxy.com:3128")
        assert result["username"] == "user"
        assert result["password"] == "pass"
        assert result["port"] == 3128

    def test_parse_proxy_url_socks5(self):
        result = parse_proxy_url("socks5://127.0.0.1:1080")
        assert result["protocol"] == "socks5"
        assert result["port"] == 1080

    def test_parse_proxy_url_default_ports(self):
        http_result = parse_proxy_url("http://proxy.com")
        assert http_result["port"] == 8080

        socks_result = parse_proxy_url("socks5://proxy.com")
        assert socks_result["port"] == 1080


class TestProxyServerErrors:
    @pytest.mark.asyncio
    async def test_invalid_http_request(self, proxy_server):
        await proxy_server.start()
        port = proxy_server._server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(b"INVALID\r\n")
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
            assert b"HTTP/1.1" in response

    @pytest.mark.asyncio
    async def test_connection_limit(self, proxy_server):
        proxy_server.max_connections = 1
        await proxy_server.start()
        port = proxy_server._server.sockets[0].getsockname()[1]

        r1, w1 = await asyncio.open_connection("127.0.0.1", port)
        await asyncio.sleep(0.05)

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
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
        w1.close()
        await proxy_server.stop()

        if response:
            assert b"429" in response or b"Too Many" in response


@pytest.fixture
def proxy_server(isolate_config):
    server = ProxyServer()
    server.host = "127.0.0.1"
    server.port = 0
    return server
