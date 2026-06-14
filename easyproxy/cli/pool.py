import json

import typer
from typing import Optional

from easyproxy.cli.client import api_get, api_post, api_delete

app = typer.Typer(help="Manage proxy pool.")


@app.command()
def list(
    alive: bool = typer.Option(False, "--alive", help="Show only alive"),
    dead: bool = typer.Option(False, "--dead", help="Show only dead"),
    protocol: Optional[str] = typer.Option(None, "--protocol", help="Filter by protocol (http/https/socks5)"),
):
    """List proxies in the pool."""
    params: dict[str, str] = {"per_page": "200"}
    if alive:
        params["status"] = "alive"
    elif dead:
        params["status"] = "dead"
    if protocol:
        params["protocol"] = protocol

    try:
        data = api_get("/api/v1/pool", params)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    proxies = data.get("proxies", [])
    if not proxies:
        typer.echo("No proxies found.")
        return

    header = f"{'ID':<4} {'Address':<20} {'Proto':<7} {'Region':<6} {'Status':<9} {'Latency':<8} {'Source':<12}"
    sep = "-" * len(header)
    typer.echo(header)
    typer.echo(sep)
    for p in proxies:
        addr = f"{p['address']}:{p['port']}"
        lat = f"{p.get('latency_ms', '—')}ms" if p.get("latency_ms") else "—"
        typer.echo(
            f"{p['id']:<4} {addr:<20} {p['protocol'].upper():<7} "
            f"{p.get('region', '—'):<6} {p['status']:<9} {lat:<8} "
            f"{p.get('source', '—'):<12}"
        )
    typer.echo(f"\nTotal: {data.get('total', len(proxies))}")


@app.command()
def add(
    address: str = typer.Argument(..., help="IP or hostname"),
    port: int = typer.Argument(..., help="Port number"),
    protocol: str = typer.Option("http", "--protocol", "-p", help="Protocol"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="ISO region code"),
):
    """Add a single proxy to the pool."""
    body = {"address": address, "port": port, "protocol": protocol, "source": "cli"}
    if region:
        body["region"] = region
    try:
        result = api_post("/api/v1/pool", body)
        typer.echo(f"Proxy added (ID {result.get('proxy_id')}).")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def remove(
    proxy_id: int = typer.Argument(..., help="Proxy ID to remove"),
):
    """Remove a proxy from the pool."""
    try:
        api_delete(f"/api/v1/pool/{proxy_id}")
        typer.echo(f"Proxy #{proxy_id} removed.")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command(name="import")
def import_(
    file: str = typer.Argument(..., help="Path to proxy file (.txt or .csv)"),
    protocol: str = typer.Option("http", "--protocol", help="Default protocol for TXT entries"),
    region: Optional[str] = typer.Option(None, "--region", help="Default region for TXT entries"),
):
    """Import proxies from a file."""
    from pathlib import Path
    path = Path(file)
    if not path.exists():
        typer.echo(f"File not found: {file}", err=True)
        raise typer.Exit(code=1)

    content = path.read_text()
    fmt = "csv" if path.suffix.lower() == ".csv" else "txt"

    body = {"format": fmt, "content": content, "protocol": protocol}
    if region:
        body["region"] = region

    try:
        result = api_post("/api/v1/pool/import", body)
        typer.echo(f"Imported: {result.get('imported', 0)}, Skipped: {result.get('skipped', 0)}")
        if errors := result.get("errors"):
            for err in errors:
                typer.echo(f"  Error: {err}", err=True)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def test(
    proxy_id: Optional[int] = typer.Option(None, "--id", help="Test specific proxy ID"),
):
    """Test proxy health."""
    body = None
    if proxy_id:
        body = {"proxy_ids": [proxy_id]}
    try:
        result = api_post("/api/v1/pool/test", body)
        typer.echo(f"Testing started: {result}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def stats():
    """Show pool statistics."""
    try:
        data = api_get("/api/v1/pool/stats")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Total:   {data.get('total', 0)}")
    typer.echo(f"Alive:   {data.get('alive', 0)}")
    typer.echo(f"Dead:    {data.get('dead', 0)}")
    if avg := data.get("average_latency_ms"):
        typer.echo(f"Avg Latency: {avg}ms")
    if med := data.get("median_latency_ms"):
        typer.echo(f"Med Latency: {med}ms")
    if proto := data.get("by_protocol"):
        typer.echo(f"\nBy Protocol: {json.dumps(proto)}")
    if region := data.get("by_region"):
        typer.echo(f"By Region:   {json.dumps(region)}")
