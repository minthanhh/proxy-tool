import httpx
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
PID_DIR = Path.home() / ".easyproxy"
PID_FILE = PID_DIR / "backend.pid"


def get_client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=10.0)


def read_pid() -> int | None:
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except (ValueError, OSError):
            return None
    return None


def write_pid(pid: int) -> None:
    PID_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid))


def remove_pid() -> None:
    PID_FILE.unlink(missing_ok=True)


def is_backend_running() -> bool:
    pid = read_pid()
    if pid is None:
        return False
    try:
        import os, signal
        os.kill(pid, 0)
        return True
    except (OSError, PermissionError):
        remove_pid()
        return False


def api_get(path: str, params: dict | None = None) -> dict | list:
    with get_client() as c:
        r = c.get(path, params=params)
        r.raise_for_status()
        return r.json()


def api_post(path: str, json: dict | None = None) -> dict | list:
    with get_client() as c:
        r = c.post(path, json=json)
        r.raise_for_status()
        return r.json()


def api_delete(path: str) -> dict | list:
    with get_client() as c:
        r = c.delete(path)
        r.raise_for_status()
        return r.json()
