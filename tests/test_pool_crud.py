import pytest
from fastapi.testclient import TestClient

from easyproxy.api.app import create_app
from easyproxy.pool.models import ProxyCreate, ProxyUpdate, ProxyProtocol, ProxyStatus
from easyproxy.pool.manager import PoolManager
from easyproxy.pool.importer import parse_txt, parse_csv, Importer


@pytest.fixture
def app(isolate_config, isolate_db):
    return create_app()


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


class TestPoolModels:
    def test_proxy_create_valid(self):
        p = ProxyCreate(address="192.168.1.1", port=8080)
        assert p.address == "192.168.1.1"
        assert p.port == 8080
        assert p.protocol == ProxyProtocol.HTTP
        assert p.source == "manual"

    def test_proxy_create_with_optional(self):
        p = ProxyCreate(
            address="proxy.example.com",
            port=3128,
            protocol=ProxyProtocol.SOCKS5,
            username="user",
            password="pass",
            region="US",
        )
        assert p.username == "user"
        assert p.region == "US"

    def test_proxy_create_invalid_address(self):
        with pytest.raises(ValueError):
            ProxyCreate(address="", port=8080)

    def test_proxy_create_invalid_ip_octets(self):
        with pytest.raises(ValueError):
            ProxyCreate(address="999.999.999.999", port=8080)

    def test_proxy_create_invalid_hostname_double_dot(self):
        with pytest.raises(ValueError):
            ProxyCreate(address="a..b", port=8080)

    def test_proxy_create_invalid_hostname_trailing_dot(self):
        with pytest.raises(ValueError):
            ProxyCreate(address="example.com.", port=8080)

    def test_proxy_create_invalid_hostname_edge_char(self):
        with pytest.raises(ValueError):
            ProxyCreate(address="-example.com", port=8080)

    def test_proxy_create_valid_hostname(self):
        p = ProxyCreate(address="proxy.example.com", port=3128)
        assert p.address == "proxy.example.com"

    def test_proxy_create_valid_short_hostname(self):
        p = ProxyCreate(address="a.co", port=80)
        assert p.address == "a.co"

    def test_proxy_create_valid_ipv6(self):
        p = ProxyCreate(address="::1", port=1080)
        assert p.address == "::1"

    def test_proxy_create_invalid_port(self):
        with pytest.raises(ValueError):
            ProxyCreate(address="1.2.3.4", port=0)

    def test_proxy_create_port_too_large(self):
        with pytest.raises(ValueError):
            ProxyCreate(address="1.2.3.4", port=65536)

    def test_proxy_update_allows_partial(self):
        u = ProxyUpdate(region="EU")
        assert u.region == "EU"
        assert u.address is None

    def test_proxy_update_allows_empty(self):
        u = ProxyUpdate()
        assert u.model_dump(exclude_none=True) == {}


@pytest.fixture
def db_and_manager(client):
    db = client.app.state.db
    manager = PoolManager(db)
    return db, manager


class TestPoolManager:
    @pytest.mark.asyncio
    async def test_add_proxy(self, db_and_manager):
        db, manager = db_and_manager
        p = ProxyCreate(address="10.0.0.1", port=3128)
        pid = await manager.add(p)
        assert pid > 0

    @pytest.mark.asyncio
    async def test_add_duplicate_raises(self, db_and_manager):
        db, manager = db_and_manager
        p = ProxyCreate(address="10.0.0.2", port=3128)
        await manager.add(p)
        with pytest.raises(ValueError, match="already exists"):
            await manager.add(p)

    @pytest.mark.asyncio
    async def test_get_proxy(self, db_and_manager):
        db, manager = db_and_manager
        p = ProxyCreate(address="10.0.0.3", port=8080)
        pid = await manager.add(p)
        proxy = await manager.get(pid)
        assert proxy is not None
        assert proxy["address"] == "10.0.0.3"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, db_and_manager):
        db, manager = db_and_manager
        proxy = await manager.get(99999)
        assert proxy is None

    @pytest.mark.asyncio
    async def test_list_proxies(self, db_and_manager):
        db, manager = db_and_manager
        for i in range(5):
            p = ProxyCreate(address=f"10.0.0.{i+10}", port=8080)
            await manager.add(p)
        proxies, total = await manager.list()
        assert total >= 5
        assert len(proxies) >= 5

    @pytest.mark.asyncio
    async def test_list_pagination(self, db_and_manager):
        db, manager = db_and_manager
        for i in range(10):
            p = ProxyCreate(address=f"10.0.0.{i+20}", port=8080)
            await manager.add(p)
        page1, total = await manager.list(page=1, per_page=3)
        assert len(page1) == 3
        page2, _ = await manager.list(page=2, per_page=3)
        assert len(page2) == 3
        assert page1[0]["id"] != page2[0]["id"]

    @pytest.mark.asyncio
    async def test_list_filter_by_protocol(self, db_and_manager):
        db, manager = db_and_manager
        await manager.add(ProxyCreate(address="10.0.0.30", port=8080, protocol=ProxyProtocol.HTTP))
        await manager.add(ProxyCreate(address="10.0.0.31", port=1080, protocol=ProxyProtocol.SOCKS5))
        proxies, total = await manager.list(protocol="socks5")
        assert total == 1
        assert proxies[0]["protocol"] == "socks5"

    @pytest.mark.asyncio
    async def test_update_proxy(self, db_and_manager):
        db, manager = db_and_manager
        p = ProxyCreate(address="10.0.0.4", port=8080)
        pid = await manager.add(p)
        updated = await manager.update(pid, ProxyUpdate(port=9090, region="US"))
        assert updated
        proxy = await manager.get(pid)
        assert proxy["port"] == 9090
        assert proxy["region"] == "US"

    @pytest.mark.asyncio
    async def test_update_nonexistent(self, db_and_manager):
        db, manager = db_and_manager
        result = await manager.update(99999, ProxyUpdate(region="EU"))
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_proxy(self, db_and_manager):
        db, manager = db_and_manager
        p = ProxyCreate(address="10.0.0.5", port=8080)
        pid = await manager.add(p)
        removed = await manager.remove(pid)
        assert removed
        proxy = await manager.get(pid)
        assert proxy is None

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self, db_and_manager):
        db, manager = db_and_manager
        result = await manager.remove(99999)
        assert result is False

    @pytest.mark.asyncio
    async def test_stats(self, db_and_manager):
        db, manager = db_and_manager
        p1 = ProxyCreate(address="10.0.0.6", port=8080)
        p2 = ProxyCreate(address="10.0.0.7", port=8080, protocol=ProxyProtocol.SOCKS5)
        pid1 = await manager.add(p1)
        await manager.add(p2)
        stats = await manager.stats()
        assert stats["total"] >= 2
        assert stats["alive"] == 0
        assert stats["dead"] == 0
        assert stats["untested"] >= 2
        assert "by_protocol" in stats
        assert "by_status" in stats

    @pytest.mark.asyncio
    async def test_stats_counts_correctly(self, db_and_manager):
        db, manager = db_and_manager
        pid = await manager.add(ProxyCreate(address="10.0.0.8", port=8080))
        await manager.update(pid, ProxyUpdate(status=ProxyStatus.ALIVE))
        pid2 = await manager.add(ProxyCreate(address="10.0.0.9", port=8080))
        await manager.update(pid2, ProxyUpdate(status=ProxyStatus.DEAD))
        await manager.add(ProxyCreate(address="10.0.0.11", port=8080))
        stats = await manager.stats()
        assert stats["alive"] == 1
        assert stats["dead"] == 1
        assert stats["untested"] == 1

    @pytest.mark.asyncio
    async def test_update_status(self, db_and_manager):
        db, manager = db_and_manager
        pid = await manager.add(ProxyCreate(address="10.0.0.10", port=8080))
        await manager.update(pid, ProxyUpdate(status=ProxyStatus.ALIVE))
        proxy = await manager.get(pid)
        assert proxy["status"] == "alive"


class TestPoolAPI:
    def test_add_proxy_api(self, client):
        resp = client.post(
            "/api/v1/pool",
            json={"address": "192.168.1.100", "port": 8080},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["address"] == "192.168.1.100"
        assert data["port"] == 8080

    def test_add_duplicate_api(self, client):
        client.post("/api/v1/pool", json={"address": "192.168.1.101", "port": 8080})
        resp = client.post("/api/v1/pool", json={"address": "192.168.1.101", "port": 8080})
        assert resp.status_code == 409

    def test_list_proxies_api(self, client):
        for i in range(3):
            client.post("/api/v1/pool", json={"address": f"10.0.0.{i}", "port": 8080})
        resp = client.get("/api/v1/pool")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 3
        assert len(body["data"]) >= 3

    def test_list_pagination_api(self, client):
        for i in range(5):
            client.post("/api/v1/pool", json={"address": f"10.0.0.{i+50}", "port": 8080})
        resp = client.get("/api/v1/pool?page=1&per_page=2")
        assert len(resp.json()["data"]) == 2
        assert resp.json()["total_pages"] >= 3

    def test_get_proxy_api(self, client):
        add = client.post("/api/v1/pool", json={"address": "10.0.0.200", "port": 8080})
        pid = add.json()["data"]["id"]
        resp = client.get(f"/api/v1/pool/{pid}")
        assert resp.status_code == 200
        assert resp.json()["data"]["address"] == "10.0.0.200"

    def test_get_nonexistent_api(self, client):
        resp = client.get("/api/v1/pool/99999")
        assert resp.status_code == 404

    def test_update_proxy_api(self, client):
        add = client.post("/api/v1/pool", json={"address": "10.0.0.201", "port": 8080})
        pid = add.json()["data"]["id"]
        resp = client.put(f"/api/v1/pool/{pid}", json={"port": 9090, "region": "EU"})
        assert resp.status_code == 200
        assert resp.json()["data"]["port"] == 9090
        assert resp.json()["data"]["region"] == "EU"

    def test_update_nonexistent_api(self, client):
        resp = client.put("/api/v1/pool/99999", json={"region": "AS"})
        assert resp.status_code == 404

    def test_delete_proxy_api(self, client):
        add = client.post("/api/v1/pool", json={"address": "10.0.0.202", "port": 8080})
        pid = add.json()["data"]["id"]
        resp = client.delete(f"/api/v1/pool/{pid}")
        assert resp.status_code == 200
        get_resp = client.get(f"/api/v1/pool/{pid}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_api(self, client):
        resp = client.delete("/api/v1/pool/99999")
        assert resp.status_code == 404

    def test_stats_api(self, client):
        resp = client.get("/api/v1/pool/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "alive" in data
        assert "by_protocol" in data

    def test_list_filter_api(self, client):
        client.post("/api/v1/pool", json={"address": "10.0.0.210", "port": 8080, "protocol": "socks5"})
        resp = client.get("/api/v1/pool?protocol=socks5")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


class TestImport:
    def test_parse_txt_simple(self):
        proxies = parse_txt("192.168.1.1:8080\n10.0.0.1:3128\n")
        assert len(proxies) == 2
        assert proxies[0].address == "192.168.1.1"
        assert proxies[0].port == 8080
        assert proxies[1].port == 3128

    def test_parse_txt_extended(self):
        proxies = parse_txt("proxy.example.com:3128:http:user:pass:US\n")
        assert len(proxies) == 1
        assert proxies[0].address == "proxy.example.com"
        assert proxies[0].protocol == ProxyProtocol.HTTP
        assert proxies[0].username == "user"
        assert proxies[0].password == "pass"
        assert proxies[0].region == "US"
        assert proxies[0].source == "file"

    def test_parse_txt_skips_comments_and_empty(self):
        proxies = parse_txt("# comment\n\n192.168.1.1:8080\n  \n")
        assert len(proxies) == 1

    def test_parse_txt_invalid_line(self):
        proxies = parse_txt("invalid\n192.168.1.1:8080\n")
        assert len(proxies) == 1

    def test_parse_txt_invalid_port(self):
        proxies = parse_txt("192.168.1.1:abc\n192.168.1.2:8080\n")
        assert len(proxies) == 1

    def test_parse_csv_no_header(self):
        content = "192.168.1.1,8080\n10.0.0.1,3128,http,user,pass,US\n"
        proxies = parse_csv(content)
        assert len(proxies) == 2
        assert proxies[0].address == "192.168.1.1"
        assert proxies[0].port == 8080
        assert proxies[1].region == "US"
        assert proxies[1].username == "user"

    def test_parse_csv_with_header(self):
        content = "ip,port,protocol,username,password,region\n192.168.1.1,8080,http,,,US\n"
        proxies = parse_csv(content)
        assert len(proxies) == 1
        assert proxies[0].address == "192.168.1.1"
        assert proxies[0].region == "US"

    def test_parse_csv_invalid_row(self):
        content = "192.168.1.1,8080\nsinglefield\n"
        proxies = parse_csv(content)
        assert len(proxies) == 1

    @pytest.mark.asyncio
    async def test_import_txt_via_importer(self, db_and_manager):
        db, manager = db_and_manager
        importer = Importer(manager)
        result = await importer.import_txt("10.0.0.100:8080\n10.0.0.101:3128\n")
        assert result["imported"] == 2
        assert result["skipped"] == 0

    @pytest.mark.asyncio
    async def test_import_txt_skips_duplicates(self, db_and_manager):
        db, manager = db_and_manager
        importer = Importer(manager)
        result = await importer.import_txt("10.0.0.200:8080\n10.0.0.200:8080\n")
        assert result["imported"] == 1
        assert result["skipped"] == 1

    @pytest.mark.asyncio
    async def test_import_csv_via_importer(self, db_and_manager):
        db, manager = db_and_manager
        importer = Importer(manager)
        result = await importer.import_csv("10.0.0.102,8080\n10.0.0.103,3128,http,,,EU\n")
        assert result["imported"] == 2
        assert result["skipped"] == 0

    def test_import_api_txt(self, client):
        resp = client.post("/api/v1/pool/import", json={
            "format": "txt",
            "content": "10.0.0.120:8080\n10.0.0.121:3128\n",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 2

    def test_import_api_csv(self, client):
        resp = client.post("/api/v1/pool/import", json={
            "format": "csv",
            "content": "10.0.0.130,8080\n10.0.0.131,3128,http\n",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 2

    def test_import_api_invalid_format(self, client):
        resp = client.post("/api/v1/pool/import", json={
            "format": "json",
            "content": "{}",
        })
        assert resp.status_code == 400

    def test_import_api_duplicates_skipped(self, client):
        client.post("/api/v1/pool", json={"address": "10.0.0.140", "port": 8080})
        resp = client.post("/api/v1/pool/import", json={
            "format": "txt",
            "content": "10.0.0.140:8080\n10.0.0.141:8080\n",
        })
        data = resp.json()
        assert data["imported"] == 1
        assert data["skipped"] == 1
