import os
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".easyproxy"
CONFIG_FILE = CONFIG_DIR / "config.json"

ALLOWED_TOP_KEYS = {
    "proxy", "database", "logging", "rotation",
    "sticky_session", "health_check", "logs", "general",
}
ALLOWED_NESTED_KEYS = {
    "proxy.port", "proxy.bind_address", "proxy.auto_configure_system_proxy",
    "database.path",
    "logging.level", "logging.file", "logging.rotation",
    "rotation.strategy", "rotation.schedule_enabled", "rotation.schedule_interval_minutes",
    "rotation.auto_rotate_on_429", "rotation.retry_attempts",
    "sticky_session.enabled", "sticky_session.ttl_seconds", "sticky_session.reset_on_error",
    "health_check.interval_seconds", "health_check.test_url", "health_check.timeout_seconds",
    "logs.max_entries", "logs.log_level",
    "general.auto_start", "general.minimize_to_tray", "general.theme",
}

DEFAULTS: dict[str, Any] = {
    "proxy": {
        "port": 8080,
        "bind_address": "127.0.0.1",
        "auto_configure_system_proxy": True,
    },
    "database": {
        "path": str(CONFIG_DIR / "easyproxy.db"),
    },
    "logging": {
        "level": "info",
        "file": str(CONFIG_DIR / "logs" / "easyproxy.log"),
        "rotation": "10 MB",
    },
    "rotation": {
        "strategy": "round-robin",
        "schedule_enabled": False,
        "schedule_interval_minutes": 10,
        "auto_rotate_on_429": True,
        "retry_attempts": 3,
    },
    "sticky_session": {
        "enabled": True,
        "ttl_seconds": 300,
        "reset_on_error": True,
    },
    "health_check": {
        "interval_seconds": 60,
        "test_url": "http://httpbin.org/ip",
        "timeout_seconds": 10,
    },
    "logs": {
        "max_entries": 10000,
        "log_level": "info",
    },
    "general": {
        "auto_start": False,
        "minimize_to_tray": True,
        "theme": "system",
    },
}

ENV_PREFIX = "EXPROXY_"


def _env_to_key(env_name: str) -> list[str]:
    suffix = env_name.removeprefix(ENV_PREFIX).lower()
    return suffix.split("__")


def _deep_set(d: dict, keys: list[str], value: str) -> None:
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = _coerce(value)


def _coerce(value: str):
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _flat_keys(d: dict, prefix: str = "") -> list[str]:
    keys = []
    for k, v in d.items():
        full = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.extend(_flat_keys(v, full))
        else:
            keys.append(full)
    return keys


def _validate_config(config: dict[str, Any], source: str = "config"):
    for top_key in config:
        if top_key not in ALLOWED_TOP_KEYS:
            logger.warning(f"Unknown config key '{top_key}' in {source}, ignoring")


def load_config() -> dict[str, Any]:
    config: dict[str, Any] = {}
    deep_copy(DEFAULTS, config)

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            file_config = json.load(f)
        _validate_config(file_config, f"{CONFIG_FILE}")
        deep_merge(config, file_config)

    for env_name, env_value in os.environ.items():
        if env_name.startswith(ENV_PREFIX):
            keys = _env_to_key(env_name)
            dotted = ".".join(keys)
            if dotted not in ALLOWED_NESTED_KEYS:
                logger.warning(f"Unknown env var '{env_name}' -> config key '{dotted}', ignoring")
                continue
            _deep_set(config, keys, env_value)

    return config


def deep_copy(source: dict, target: dict) -> None:
    for key, value in source.items():
        if isinstance(value, dict):
            target[key] = {}
            deep_copy(value, target[key])
        else:
            target[key] = value


def deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


def save_config(config: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_config_path() -> Path:
    return CONFIG_FILE
