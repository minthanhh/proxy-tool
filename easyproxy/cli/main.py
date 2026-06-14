import typer

app = typer.Typer(
    name="easyproxy",
    help="EasyProxy — Rotating proxy IP desktop app",
    no_args_is_help=True,
)


@app.command()
def start():
    """Start the EasyProxy server (FastAPI backend + proxy engine)."""
    typer.echo("Starting EasyProxy...")


@app.command()
def stop():
    """Stop the EasyProxy server gracefully."""
    typer.echo("Stopping EasyProxy...")


@app.command()
def status():
    """Show current server status (running/stopped, active proxy count)."""
    typer.echo("EasyProxy is stopped.")


@app.command()
def pool():
    """List, add, or remove proxies from the pool."""
    typer.echo("Proxy pool management.")


@app.command()
def rotate():
    """Manually rotate to the next proxy in the pool."""
    typer.echo("Rotating proxy...")
