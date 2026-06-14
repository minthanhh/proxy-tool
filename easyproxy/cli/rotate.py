from typing import Optional

import typer

from easyproxy.cli.client import api_post


def rotate(
    strategy: Optional[str] = typer.Option(None, "--strategy", help="Rotation strategy"),
    interval: Optional[int] = typer.Option(None, "--interval", help="Set schedule interval (minutes)"),
    scheduled: bool = typer.Option(False, "--scheduled", help="Toggle scheduled rotation"),
):
    """Manually rotate to the next proxy in the pool."""
    body: dict = {}
    if strategy:
        body["strategy"] = strategy
    if interval is not None:
        body["interval_minutes"] = interval
    if scheduled:
        body["schedule_enabled"] = True

    try:
        result = api_post("/api/v1/proxy/rotate", body if body else None)
        fro = result.get("from", result.get("previous_ip", "—"))
        to = result.get("to", result.get("current_ip", "—"))
        typer.echo(f"Rotated: {fro} → {to}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
