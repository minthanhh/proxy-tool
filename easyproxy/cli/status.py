import json
import sys

import typer

from easyproxy.cli.client import api_get, is_backend_running


def _fmt_uptime(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def _table(rows: list[tuple[str, str]], title: str = "") -> str:
    lines = []
    if title:
        lines.append(f"  {title}:")
    for key, val in rows:
        lines.append(f"    {key:<20} {val}")
    return "\n".join(lines)


def status(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show current server status."""
    if not is_backend_running():
        if json_output:
            print(json.dumps({"running": False, "reason": "backend_not_running"}))
        else:
            typer.echo("EasyProxy is stopped.")
        raise typer.Exit(code=1)

    try:
        health = api_get("/health")
        proxy = api_get("/api/v1/proxy/status")
        pool = api_get("/api/v1/pool/stats")
        rotations = api_get("/api/v1/rotation-log", {"per_page": "5"})
    except Exception as e:
        if json_output:
            print(json.dumps({"running": False, "error": str(e)}))
        else:
            typer.echo(f"Failed to get status: {e}", err=True)
        raise typer.Exit(code=1)

    if json_output:
        print(json.dumps({
            "backend": health,
            "proxy": proxy,
            "pool": pool,
            "recent_rotations": rotations.get("rotations", []),
        }, indent=2, default=str))
        return

    running = proxy.get("running", False)
    lines = []

    if running:
        lines.append("  Proxy: Running")
        lines.append(f"  Port:  {proxy.get('port', 8080)}")
        if ip := proxy.get("current_ip"):
            lines.append(f"  IP:    {ip}")
        if strategy := proxy.get("strategy"):
            lines.append(f"  Strategy:  {strategy}")
        if uptime := proxy.get("uptime_seconds"):
            lines.append(f"  Uptime:    {_fmt_uptime(uptime)}")
        if reqs := proxy.get("requests_served"):
            lines.append(f"  Requests:  {reqs}")
        if limits := proxy.get("rate_limits_detected"):
            lines.append(f"  Rate Limits: {limits}")
        if rots := proxy.get("rotations_performed"):
            lines.append(f"  Rotations: {rots}")
    else:
        lines.append("  Proxy: Stopped")

    lines.append("")
    lines.append("  Pool:")
    lines.append(f"    Total:  {pool.get('total', 0)}")
    lines.append(f"    Alive:  {pool.get('alive', 0)}")
    lines.append(f"    Dead:   {pool.get('dead', 0)}")

    rot_list = rotations.get("rotations", [])
    if rot_list:
        lines.append("")
        lines.append("  Recent Rotations:")
        for r in rot_list[:5]:
            reason = r.get("reason", "?")
            ts = r.get("timestamp", "")[11:19] if r.get("timestamp") else ""
            fro = r.get("from_proxy", "—")
            to = r.get("to_proxy", "—")
            ok = "✓" if r.get("retry_success") else "✗" if r.get("retry_success") is False else "?"
            lines.append(f"    {ts}  {fro:>18} → {to:<18}  {reason:<12} {ok}")

    typer.echo(f"\n{'EasyProxy Status':^60}\n{'='*60}")
    typer.echo("\n".join(lines))
    typer.echo("=" * 60)
