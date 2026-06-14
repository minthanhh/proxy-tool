import os
import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def test_config_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def test_config_data():
    return {
        "proxy": {"port": 9999, "bind_address": "0.0.0.0"},
        "rotation": {"strategy": "least-used"},
    }


@pytest.fixture
def test_config_file(test_config_dir, test_config_data):
    path = test_config_dir / "config.json"
    path.write_text(json.dumps(test_config_data))
    return path


@pytest.fixture
def isolate_config(monkeypatch, test_config_dir):
    monkeypatch.setattr("easyproxy.config.CONFIG_DIR", test_config_dir)
    monkeypatch.setattr("easyproxy.config.CONFIG_FILE", test_config_dir / "config.json")
    monkeypatch.setattr(
        "easyproxy.config.DEFAULTS",
        {
            "proxy": {"port": 8080, "bind_address": "127.0.0.1", "auto_configure_system_proxy": True},
            "database": {"path": str(test_config_dir / "easyproxy.db")},
            "logging": {"level": "info", "file": str(test_config_dir / "logs" / "easyproxy.log"), "rotation": "10 MB"},
            "rotation": {
                "strategy": "round-robin",
                "schedule_enabled": False,
                "schedule_interval_minutes": 10,
                "auto_rotate_on_429": True,
                "retry_attempts": 3,
            },
            "sticky_session": {"enabled": True, "ttl_seconds": 300, "reset_on_error": True},
            "health_check": {"interval_seconds": 60, "test_url": "http://httpbin.org/ip", "timeout_seconds": 10},
            "logs": {"max_entries": 10000, "log_level": "info"},
            "general": {"auto_start": False, "minimize_to_tray": True, "theme": "system"},
        },
    )


@pytest.fixture
def isolate_db(monkeypatch, test_config_dir):
    monkeypatch.setattr("easyproxy.database.load_config", lambda: {
        "database": {"path": str(test_config_dir / "test_easyproxy.db")},
    })
