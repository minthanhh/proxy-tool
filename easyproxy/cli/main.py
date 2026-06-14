import typer

from easyproxy.cli import proxy as proxy_commands
from easyproxy.cli import status as status_commands
from easyproxy.cli import pool as pool_commands
from easyproxy.cli import rotate as rotate_commands
from easyproxy.cli import logs as logs_commands

app = typer.Typer(
    name="easyproxy",
    help="EasyProxy — Rotating proxy IP desktop app",
    no_args_is_help=True,
)

app.command(name="start")(proxy_commands.start)
app.command(name="stop")(proxy_commands.stop)
app.command(name="restart")(proxy_commands.restart)
app.command(name="status")(status_commands.status)
app.add_typer(pool_commands.app, name="pool")
app.command(name="rotate")(rotate_commands.rotate)
app.command(name="logs")(logs_commands.logs)
app.command(name="rotation-history")(logs_commands.rotation)
