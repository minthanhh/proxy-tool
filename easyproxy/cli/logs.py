import time
from typing import Optional

import typer

from easyproxy.cli.client import api_get


def logs(
    tail: int = typer.Option(10, "--tail", help="Number of recent logs"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow mode (poll every 2s)"),
    method: Optional[str] = typer.Option(None, "--method", "-m", help="Filter by HTTP method"),
    status: Optional[int] = typer.Option(None, "--status", "-s", help="Filter by status code"),
    proxy: Optional[str] = typer.Option(None, "--proxy", help="Filter by proxy address"),
    since: Optional[str] = typer.Option(None, "--since", help="Start time (ISO 8601)"),
    until: Optional[str] = typer.Option(None, "--until", help="End time (ISO 8601)"),
):
    """Show request logs."""
    params: dict[str, str] = {"per_page": str(tail)}
    if method:
        params["method"] = method
    if status is not None:
        params["status"] = str(status)
    if proxy:
        params["proxy_address"] = proxy
    if since:
        params["since"] = since
    if until:
        params["until"] = until

    seen = set()

    while True:
        try:
            data = api_get("/api/v1/proxy/logs", params)
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            if not follow:
                raise typer.Exit(code=1)
            time.sleep(2)
            continue

        entries = data.get("logs", [])
        new_entries = [e for e in entries if e.get("id") not in seen]
        for e in reversed(new_entries):
            ts = e.get("timestamp", "")[11:19] if e.get("timestamp") else ""
            method_str = e.get("method", "?").ljust(6)
            code = e.get("status_code", 0)
            dur = f"{e.get('duration_ms', 0)}ms"
            url = e.get("url", "")
            proxy_addr = e.get("proxy_address", "")
            typer.echo(f"{ts}  {method_str} {code} {dur:>7}  {url}  [{proxy_addr}]")
            seen.add(e.get("id"))

        if not follow:
            break
        time.sleep(2)


def rotation(
    tail: int = typer.Option(10, "--tail", "-n", help="Number of recent rotations"),
):
    """Show rotation history."""
    params: dict[str, str] = {"per_page": str(tail)}
    try:
        data = api_get("/api/v1/rotation-log", params)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    entries = data.get("rotations", [])
    if not entries:
        typer.echo("No rotations recorded yet.")
        return

    for e in entries:
        ts = e.get("timestamp", "")[11:19] if e.get("timestamp") else ""
        reason = e.get("reason", "?").ljust(12)
        fro = e.get("from_proxy", "—").ljust(18)
        to = e.get("to_proxy", "—")
        ok = "✓" if e.get("retry_success") else "✗" if e.get("retry_success") is False else "?"
        typer.echo(f"{ts}  {fro} → {to:<18} {reason} {ok}")
