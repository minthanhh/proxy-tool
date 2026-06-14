import os
import json
import logging
from pathlib import Path

import pytest

from easyproxy.config import (
    load_config,
    save_config,
    get_config_path,
    _env_to_key,
    _coerce,
    deep_copy,
    deep_merge,
)


@pytest.fixture(autouse=True)
def reset_logger():
    logger = logging.getLogger("easyproxy.config")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())


class TestLoadDefaults:
    def test_returns_all_top_keys(self, isolate_config):
        cfg = load_config()
        assert set(cfg.keys()) == {
            "proxy", "database", "logging", "rotation",
            "sticky_session", "health_check", "logs", "general",
        }

    def test_proxy_defaults(self, isolate_config):
        cfg = load_config()
        assert cfg["proxy"]["port"] == 8080
        assert cfg["proxy"]["bind_address"] == "127.0.0.1"
        assert cfg["proxy"]["auto_configure_system_proxy"] is True

    def test_rotation_defaults(self, isolate_config):
        cfg = load_config()
        assert cfg["rotation"]["strategy"] == "round-robin"
        assert cfg["rotation"]["schedule_enabled"] is False
        assert cfg["rotation"]["auto_rotate_on_429"] is True

    def test_sticky_session_defaults(self, isolate_config):
        cfg = load_config()
        assert cfg["sticky_session"]["enabled"] is True
        assert cfg["sticky_session"]["ttl_seconds"] == 300


class TestEnvOverride:
    def test_env_override_port(self, isolate_config, monkeypatch):
        monkeypatch.setenv("EXPROXY_PROXY__PORT", "9090")
        cfg = load_config()
        assert cfg["proxy"]["port"] == 9090

    def test_env_override_nested(self, isolate_config, monkeypatch):
        monkeypatch.setenv("EXPROXY_ROTATION__STRATEGY", "least-used")
        cfg = load_config()
        assert cfg["rotation"]["strategy"] == "least-used"

    def test_env_override_boolean(self, isolate_config, monkeypatch):
        monkeypatch.setenv("EXPROXY_PROXY__AUTO_CONFIGURE_SYSTEM_PROXY", "false")
        cfg = load_config()
        assert cfg["proxy"]["auto_configure_system_proxy"] is False

    def test_env_unknown_key_warns(self, isolate_config, monkeypatch, caplog):
        caplog.set_level(logging.WARNING, logger="easyproxy.config")
        monkeypatch.setenv("EXPROXY_INVALID__KEY", "test")
        load_config()
        assert "Unknown env var" in caplog.text
        assert "invalid.key" in caplog.text

    def test_env_unknown_key_skipped(self, isolate_config, monkeypatch):
        monkeypatch.setenv("EXPROXY_BOGUS", "test")
        cfg = load_config()
        assert "bogus" not in cfg


class TestFileOverride:
    def test_file_overrides_default(self, isolate_config, test_config_dir, test_config_data):
        path = test_config_dir / "config.json"
        path.write_text(json.dumps(test_config_data))
        cfg = load_config()
        assert cfg["proxy"]["port"] == 9999
        assert cfg["rotation"]["strategy"] == "least-used"

    def test_file_unknown_key_warns(self, isolate_config, test_config_dir, caplog):
        caplog.set_level(logging.WARNING, logger="easyproxy.config")
        path = test_config_dir / "config.json"
        path.write_text(json.dumps({"unknown_section": {"key": "val"}}))
        load_config()
        assert "Unknown config key" in caplog.text
        assert "unknown_section" in caplog.text


class TestSaveConfig:
    def test_save_and_reload(self, isolate_config, test_config_dir):
        cfg = load_config()
        cfg["proxy"]["port"] = 7777
        save_config(cfg)
        assert (test_config_dir / "config.json").exists()
        reloaded = load_config()
        assert reloaded["proxy"]["port"] == 7777

    def test_get_config_path(self, isolate_config, test_config_dir):
        assert get_config_path() == test_config_dir / "config.json"


class TestHelpers:
    def test_env_to_key(self):
        assert _env_to_key("EXPROXY_PROXY__PORT") == ["proxy", "port"]
        assert _env_to_key("EXPROXY_ROTATION__STRATEGY") == ["rotation", "strategy"]

    def test_coerce_bool(self):
        assert _coerce("true") is True
        assert _coerce("TRUE") is True
        assert _coerce("yes") is True
        assert _coerce("1") is True
        assert _coerce("false") is False
        assert _coerce("no") is False
        assert _coerce("0") is False

    def test_coerce_int(self):
        assert _coerce("42") == 42
        assert _coerce("0") is False

    def test_coerce_float(self):
        assert _coerce("3.14") == 3.14

    def test_coerce_string(self):
        assert _coerce("hello") == "hello"

    def test_deep_copy(self):
        source = {"a": {"b": 1, "c": [2]}, "d": 3}
        target = {}
        deep_copy(source, target)
        assert target == source
        target["a"]["b"] = 99
        assert source["a"]["b"] == 1

    def test_deep_merge(self):
        base = {"a": {"b": 1, "c": 2}, "d": 3}
        override = {"a": {"b": 99}, "e": 4}
        deep_merge(base, override)
        assert base == {"a": {"b": 99, "c": 2}, "d": 3, "e": 4}
