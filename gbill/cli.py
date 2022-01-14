"""This module provides the Group Bill app CLI."""
# gbill/cli.py

from pathlib import Path
from typing import List, Optional
import typer
from gbill import (
    ERRORS, AMOUNT_FLAG, PARTICIPANT_FLAG,
    __app_name__, __version__,
    config, db, gbill,
)

app = typer.Typer()


@app.command()
def init(
        db_path: str = typer.Option(
            str(db.DEFAULT_DB_FILE_PATH),
            '--db-path',
            '-db',
            prompt='gbill database location?',
        ),
) -> None:
    """Initialize the gbill database."""
    app_init_error = config.init_app(db_path)
    if app_init_error:
        typer.secho(
            f'Creating config file failed with "{ERRORS[app_init_error]}"',
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    db_init_error = db.init_database(Path(db_path))
    if db_init_error:
        typer.secho(
            f'Creating database failed with "{ERRORS[db_init_error]}"',
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    else:
        typer.secho(f'The gbill database is {db_path}', fg=typer.colors.GREEN)


@app.command()
def add(
    participant: List[str] = typer.Argument(...),
    amount: float = typer.Option(
        ...,
        '--amount',
        '-a',
        min=0.00,
    )
) -> None:
    """Add a new bill"""
    biller = get_bill()
    bill, error = biller.add(participant, amount)
    if error:
        typer.secho(
            f'Adding bill failed with "{ERRORS[error]}"',
            fg=typer.colors.RED
        )
        raise typer.Exit(1)
    else:
        typer.secho(
            f"""bill: "{bill['Participant']}" was added """
            f"""with amount: ${amount:.2f}""",
            fg=typer.colors.GREEN,
        )


@app.command(name='list')
def list_all() -> None:
    """List all bills"""
    biller = get_bill()
    bill_list = biller.get_bill_list()
    if len(bill_list) == 0:
        typer.secho(
            'There are no bill in the bill list yet', fg=typer.colors.RED
        )
        raise typer.Exit()
    typer.secho('\nbill list:\n', fg=typer.colors.BLUE, bold=True)
    columns = (
        'ID.  ',
        '| Amount  ',
        '| Participants      ',
    )
    headers = ''.join(columns)
    typer.secho(headers, fg=typer.colors.BLUE, bold=True)
    typer.secho('-' * len(headers), fg=typer.colors.BLUE)
    for i, bill in enumerate(bill_list, 1):
        parts, amount = bill.values()
        typer.secho(
            f'{i}{(len(columns[0]) - len(str(i))) * " "}'
            f'| ${amount:.2f}{(len(columns[1]) - len(str(round(amount, 2))) - 3) * " "}'
            f'| {parts}',
            fg=typer.colors.BLUE,
        )
    typer.secho('-' * len(headers) + '\n', fg=typer.colors.BLUE)


def get_bill() -> gbill.Biller:
    if config.CONFIG_FILE_PATH.exists():
        db_path = db.get_database_path(config.CONFIG_FILE_PATH)
    else:
        typer.secho(
            'Config file not found. Please, run "gbill init"',
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    if db_path.exists():
        return gbill.Biller(db_path)
    else:
        typer.secho(
            'Database not found. Please, run "gbill init"',
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)


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
