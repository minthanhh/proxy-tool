import json

import pytest
from fastapi.testclient import TestClient

from easyproxy.api.app import create_app


@pytest.fixture
def app(isolate_config, isolate_db):
    return create_app()


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_contains_version(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert "version" in data
        assert data["status"] == "ok"

    def test_health_contains_pool(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert "pool" in data
        assert "total" in data["pool"]
        assert "alive" in data["pool"]
        assert "dead" in data["pool"]

    def test_health_uptime_increases(self, client):
        resp1 = client.get("/health")
        u1 = resp1.json()["uptime_seconds"]
        import time
        time.sleep(0.01)
        resp2 = client.get("/health")
        u2 = resp2.json()["uptime_seconds"]
        assert u2 >= u1


class TestDocs:
    def test_swagger_ui(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_openapi_json(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["info"]["title"] == "EasyProxy"
        assert "version" in data["info"]


class TestCORS:
    def test_cors_headers(self, client):
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3002",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers

    def test_cors_has_allow_origin_header(self, client):
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers


class TestRequestID:
    def test_request_id_header(self, client):
        resp = client.get("/health")
        assert "x-request-id" in resp.headers
        assert len(resp.headers["x-request-id"]) == 8

    def test_request_id_unique(self, client):
        r1 = client.get("/health")
        r2 = client.get("/health")
        assert r1.headers["x-request-id"] != r2.headers["x-request-id"]


class TestTiming:
    def test_timing_header(self, client):
        resp = client.get("/health")
        assert "x-process-time-ms" in resp.headers
        assert int(resp.headers["x-process-time-ms"]) >= 0


class TestErrorResponses:
    def test_not_found_returns_rfc7807(self, client):
        resp = client.get("/nonexistent")
        assert resp.status_code == 404
        data = resp.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert data["status"] == 404
        assert "detail" in data
        assert "instance" in data

    def test_invalid_method_returns_405(self, client):
        resp = client.post("/health")
        assert resp.status_code == 405
        data = resp.json()
        assert "detail" in data


class TestWebSocket:
    def test_websocket_connect(self, app):
        from fastapi.testclient import TestClient as WSClient

        with WSClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                data = ws.receive_json()
                assert data["type"] == "ping"

    def test_websocket_ping_pong(self, app):
        from fastapi.testclient import TestClient as WSClient

        with WSClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                _ = ws.receive_json()  # consume initial server ping
                ws.send_json({"type": "ping"})
                data = ws.receive_json()
                assert data["type"] == "pong"

    def test_websocket_receives_events(self, app):
        from easyproxy.api.events import get_event_bus
        from fastapi.testclient import TestClient as WSClient

        event_bus = get_event_bus()

        with WSClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.receive_json()  # consume initial server ping

                event_bus.publish_nowait({"type": "test_event", "data": {"hello": "world"}})
                data = ws.receive_json()
                assert data["type"] == "test_event"
                assert data["data"]["hello"] == "world"

    def test_websocket_multiple_clients(self, app):
        from easyproxy.api.events import get_event_bus
        from fastapi.testclient import TestClient as WSClient

        event_bus = get_event_bus()

        with WSClient(app) as client1, WSClient(app) as client2:
            with client1.websocket_connect("/ws") as ws1:
                with client2.websocket_connect("/ws") as ws2:
                    ws1.receive_json()  # consume initial server pings
                    ws2.receive_json()

                    event_bus.publish_nowait({"type": "broadcast"})
                    assert ws1.receive_json()["type"] == "broadcast"
                    assert ws2.receive_json()["type"] == "broadcast"


class TestEventBus:
    def test_subscriber_count(self):
        from easyproxy.api.events import get_event_bus

        bus = get_event_bus()
        q1 = bus.subscribe()
        q2 = bus.subscribe()
        assert bus.subscriber_count >= 2
        bus.unsubscribe(q1)
        bus.unsubscribe(q2)

    def test_publish_nowait(self):
        from easyproxy.api.events import get_event_bus
        import asyncio

        bus = get_event_bus()
        q = bus.subscribe()
        bus.publish_nowait({"type": "instant"})
        result = asyncio.run(q.get())
        assert result["type"] == "instant"
        bus.unsubscribe(q)
