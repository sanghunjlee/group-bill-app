"""This module provides the Group Bill app CLI."""
# gbill/cli.py

from typing import Optional
import typer
from gbill import __app_name__, __version__

app = typer.Typer()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f'{__app_name__} v{__version__}')
        raise typer.Exit()


@app.callback()
def main(
        version: Optional[bool] = typer.Option(
            None,
            '--version',
            '-v',
            help='show the application\'s version and exit.',
            callback=_version_callback,
            is_eager=True,
        )
) -> None:
    return
