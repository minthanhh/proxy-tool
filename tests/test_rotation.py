import pytest
from fastapi.testclient import TestClient

from easyproxy.api.app import create_app
from easyproxy.pool.models import ProxyCreate, ProxyUpdate, ProxyStatus
from easyproxy.pool.manager import PoolManager
from easyproxy.rotation.engine import RotationEngine


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


class TestRotationEngine:
    @pytest.mark.asyncio
    async def test_rotate_picks_first_alive(self, db_and_manager):
        db, manager = db_and_manager
        pid = await manager.add(ProxyCreate(address="10.0.0.1", port=8080))
        await manager.update(pid, ProxyUpdate(status=ProxyStatus.ALIVE))
        engine = RotationEngine(manager)
        result = await engine.rotate()
        assert result["to"]["id"] == pid

    @pytest.mark.asyncio
    async def test_rotate_round_robin(self, db_and_manager):
        db, manager = db_and_manager
        pid1 = await manager.add(ProxyCreate(address="10.0.0.2", port=8080))
        pid2 = await manager.add(ProxyCreate(address="10.0.0.3", port=8080))
        await manager.update(pid1, ProxyUpdate(status=ProxyStatus.ALIVE))
        await manager.update(pid2, ProxyUpdate(status=ProxyStatus.ALIVE))
        engine = RotationEngine(manager)
        r1 = await engine.rotate()
        assert r1["to"]["id"] == pid1
        r2 = await engine.rotate()
        assert r2["from"]["id"] == pid1
        assert r2["to"]["id"] == pid2

    @pytest.mark.asyncio
    async def test_rotate_wraps_around(self, db_and_manager):
        db, manager = db_and_manager
        pid1 = await manager.add(ProxyCreate(address="10.0.0.4", port=8080))
        pid2 = await manager.add(ProxyCreate(address="10.0.0.5", port=8080))
        await manager.update(pid1, ProxyUpdate(status=ProxyStatus.ALIVE))
        await manager.update(pid2, ProxyUpdate(status=ProxyStatus.ALIVE))
        engine = RotationEngine(manager)
        await engine.rotate()
        await engine.rotate()
        r3 = await engine.rotate()
        assert r3["from"]["id"] == pid2
        assert r3["to"]["id"] == pid1

    @pytest.mark.asyncio
    async def test_rotate_no_alive_raises(self, db_and_manager):
        db, manager = db_and_manager
        await manager.add(ProxyCreate(address="10.0.0.6", port=8080))
        engine = RotationEngine(manager)
        with pytest.raises(RuntimeError, match="No alive proxies"):
            await engine.rotate()

    @pytest.mark.asyncio
    async def test_rotate_logs_rotation(self, db_and_manager):
        db, manager = db_and_manager
        pid = await manager.add(ProxyCreate(address="10.0.0.7", port=8080))
        await manager.update(pid, ProxyUpdate(status=ProxyStatus.ALIVE))
        engine = RotationEngine(manager)
        await engine.rotate()
        rows = await manager.conn.execute_fetchall("SELECT * FROM rotation_log")
        assert len(rows) == 1
        assert rows[0]["reason"] == "manual"
        assert rows[0]["to_proxy_id"] == pid


class TestRotationAPI:
    def test_rotate_returns_503_when_no_alive(self, client):
        client.post("/api/v1/pool", json={"address": "10.0.0.10", "port": 8080})
        resp = client.post("/api/v1/proxy/rotate")
        assert resp.status_code == 503

    def test_rotate_success(self, client):
        add = client.post("/api/v1/pool", json={"address": "10.0.0.11", "port": 8080})
        pid = add.json()["data"]["id"]
        client.put(f"/api/v1/pool/{pid}", json={"status": "alive"})
        resp = client.post("/api/v1/proxy/rotate")
        assert resp.status_code == 200
        data = resp.json()
        assert "from" in data
        assert "to" in data
        assert data["to"]["id"] == pid
