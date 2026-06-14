import os
import signal
import subprocess
import sys
import time

import typer

from easyproxy.cli.client import (
    api_post,
    is_backend_running,
    read_pid,
    remove_pid,
    write_pid,
)

BACKEND_MODULE = "easyproxy.api.app"


def _start_backend() -> int | None:
    """Launch uvicorn as a subprocess, return PID or None on failure."""
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", f"{BACKEND_MODULE}:create_app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pid = proc.pid
        write_pid(pid)
        return pid
    except OSError as e:
        typer.echo(f"Error starting backend: {e}", err=True)
        return None


def _wait_for_health(timeout: int = 15) -> bool:
    """Poll /health until the backend responds or timeout."""
    from easyproxy.cli.client import get_client
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with get_client() as c:
                r = c.get("/health")
                if r.status_code == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def _stop_backend() -> bool:
    pid = read_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(30):
            try:
                os.kill(pid, 0)
                time.sleep(0.2)
            except OSError:
                break
        else:
            os.kill(pid, signal.SIGKILL)
        return True
    except (OSError, PermissionError) as e:
        typer.echo(f"Error stopping backend: {e}", err=True)
        return False
    finally:
        remove_pid()


def start(
    system_proxy: bool = typer.Option(False, "--system-proxy", help="Configure system proxy settings"),
):
    """Start the EasyProxy server (FastAPI backend + proxy engine)."""
    if is_backend_running():
        typer.echo("Backend is already running.")
    else:
        typer.echo("Starting backend...")
        pid = _start_backend()
        if pid is None:
            raise typer.Exit(code=1)
        if not _wait_for_health():
            typer.echo("Backend failed to start within timeout.", err=True)
            _stop_backend()
            raise typer.Exit(code=1)
        typer.echo(f"Backend started (PID {pid}).")

    try:
        body = {"system_proxy": system_proxy} if system_proxy else None
        result = api_post("/api/v1/proxy/start", body)
        typer.echo(f"Proxy running on port {result.get('port', 8080)}.")
        if ip := result.get("current_ip"):
            typer.echo(f"Current IP: {ip}")
    except Exception as e:
        typer.echo(f"Failed to start proxy engine: {e}", err=True)
        raise typer.Exit(code=1)


def stop(
    all: bool = typer.Option(False, "--all", help="Also stop the backend process"),
):
    """Stop the EasyProxy server gracefully."""
    try:
        result = api_post("/api/v1/proxy/stop")
        typer.echo(result.get("message", "Proxy stopped."))
    except Exception as e:
        typer.echo(f"Proxy engine may not be running: {e}")

    if all:
        if _stop_backend():
            typer.echo("Backend stopped.")
        else:
            typer.echo("No backend process found.")


def restart(
    system_proxy: bool = typer.Option(False, "--system-proxy", help="Configure system proxy settings"),
):
    """Restart the EasyProxy server."""
    typer.echo("Restarting...")
    try:
        api_post("/api/v1/proxy/stop")
    except Exception:
        pass
    _stop_backend()
    time.sleep(0.5)
    start(system_proxy=system_proxy)
