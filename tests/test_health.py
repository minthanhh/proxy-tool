from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from easyproxy.api.app import create_app
from easyproxy.pool.models import ProxyCreate, ProxyUpdate, ProxyStatus
from easyproxy.pool.manager import PoolManager
from easyproxy.pool.health import HealthCheckRunner


class _MockResponse:
    def __init__(self, status=200):
        self.status = status
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass


class _MockSession:
    def __init__(self, head_return=None, head_side_effect=None):
        self._head_return = head_return
        self._head_side_effect = head_side_effect

    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass

    def head(self, *args, **kwargs):
        if self._head_side_effect is not None:
            raise self._head_side_effect
        return self._head_return


@pytest.fixture
def app(isolate_config, isolate_db):
    return create_app()


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_and_manager(client):
    db = client.app.state.db
    manager = PoolManager(db)
    return db, manager


@pytest.fixture
async def seeded_manager(db_and_manager):
    db, manager = db_and_manager
    for i in range(3):
        await manager.add(ProxyCreate(address=f"10.0.0.{i+10}", port=8080))
    return manager


class TestHealthCheckRunner:
    @pytest.mark.asyncio
    async def test_check_all_returns_counts(self, seeded_manager):
        runner = HealthCheckRunner(seeded_manager, timeout_seconds=5)
        mock_session = _MockSession(head_return=_MockResponse(200))

        with patch("easyproxy.pool.health.aiohttp.ClientSession", return_value=mock_session):
            results = await runner.run_all()

        assert results["checked"] == 3
        assert results["alive"] == 3
        assert results["errors"] == 0

    @pytest.mark.asyncio
    async def test_success_updates_proxy(self, db_and_manager):
        db, manager = db_and_manager
        pid = await manager.add(ProxyCreate(address="10.0.0.20", port=8080))
        runner = HealthCheckRunner(manager, timeout_seconds=5)
        mock_session = _MockSession(head_return=_MockResponse(200))

        with patch("easyproxy.pool.health.aiohttp.ClientSession", return_value=mock_session):
            result = await runner.run_single(pid)

        assert result is not None
        assert result["status"] == "alive"
        assert result["latency_ms"] is not None
        assert result["success_count"] == 1
        assert result["consecutive_errors"] == 0

    @pytest.mark.asyncio
    async def test_failure_increments_errors(self, db_and_manager):
        db, manager = db_and_manager
        pid = await manager.add(ProxyCreate(address="10.0.0.21", port=8080))
        runner = HealthCheckRunner(manager, timeout_seconds=5, max_consecutive_errors=3)
        mock_session = _MockSession(head_side_effect=ConnectionError("refused"))

        with patch("easyproxy.pool.health.aiohttp.ClientSession", return_value=mock_session):
            await runner.run_single(pid)

        proxy = await manager.get(pid)
        assert proxy["error_count"] == 1
        assert proxy["consecutive_errors"] == 1
        assert proxy["status"] == "untested"

    @pytest.mark.asyncio
    async def test_three_failures_marks_dead(self, db_and_manager):
        db, manager = db_and_manager
        pid = await manager.add(ProxyCreate(address="10.0.0.22", port=8080))
        runner = HealthCheckRunner(manager, timeout_seconds=5, max_consecutive_errors=3)
        mock_session = _MockSession(head_side_effect=ConnectionError("refused"))

        with patch("easyproxy.pool.health.aiohttp.ClientSession", return_value=mock_session):
            for _ in range(3):
                await runner.run_single(pid)

        proxy = await manager.get(pid)
        assert proxy["consecutive_errors"] == 3
        assert proxy["status"] == "dead"

    @pytest.mark.asyncio
    async def test_run_single_nonexistent_returns_none(self, db_and_manager):
        db, manager = db_and_manager
        runner = HealthCheckRunner(manager)
        result = await runner.run_single(99999)
        assert result is None


class TestHealthAPI:
    def test_test_endpoint_returns_200(self, client):
        client.post("/api/v1/pool", json={"address": "10.0.0.30", "port": 8080})
        resp = client.post("/api/v1/pool/test")
        assert resp.status_code == 200

    def test_test_single_nonexistent(self, client):
        resp = client.post("/api/v1/pool/test?proxy_id=99999")
        assert resp.status_code == 404

    def test_test_endpoint_with_proxy_id(self, client):
        add = client.post("/api/v1/pool", json={"address": "10.0.0.31", "port": 8080})
        pid = add.json()["data"]["id"]
        resp = client.post(f"/api/v1/pool/test?proxy_id={pid}")
        assert resp.status_code == 200
        assert "data" in resp.json()
