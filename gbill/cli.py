"""This module provides the Group Bill app CLI."""
# gbill/cli.py

from pathlib import Path
from typing import List, Any, Optional
import typer
from gbill import (
    ERRORS, __app_name__, __version__, config, db, gbill,
)


VALID_TYPES = ['amount', 'participant']


app = typer.Typer()


def _add_file_callback(filepath: str) -> None:
    if filepath:
        typer.secho(
            f'Importing from the file: {filepath}',
            fg=typer.colors.BLUE
        )
        typer.secho(
            f'Currently this feature is not implemented.',
            fg=typer.colors.RED
        )
        raise typer.Exit()


def _type_complete(incomplete: str) -> List[str]:
    completion = []
    for _ in VALID_TYPES:
        if _.startswith(incomplete):
            completion.append(_)
    return completion


def _type_callback(value: str) -> str:
    if value.lower() not in VALID_TYPES:
        raise typer.BadParameter(f'Please enter value from: {VALID_TYPES}')
    return value


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
        filepath: Optional[str] = typer.Option(
            None,
            '--path',
            '-p',
            callback=_add_file_callback,
            is_eager=True
        )
) -> None:
    """Add a new bill"""

    def _get_input(prompt: str, force: bool = False) -> str:
        while True:
            ret = typer.prompt(prompt)
            if ret.lower().strip() in ['q', 'quit', 'quit()']:
                return ''
            if force:
                break
            confirm = typer.confirm(f'Is the input {ret} correct?')
            if confirm:
                break
        return ret

    participant = _get_input('Enter participant(s) (separate each entry with ","): ')
    amount = _get_input('Enter amount: ')

    biller = get_bill()
    try:
        v_amount = float(amount)
    except ValueError:
        typer.secho(
            f"""The new amount entered ({amount}) is not a number.""",
            fg=typer.colors.RED
        )
        raise typer.Exit(1)
    bill, error = biller.add([participant], v_amount)
    if error:
        typer.secho(
            f'Adding bill failed with "{ERRORS[error]}"',
            fg=typer.colors.RED
        )
        raise typer.Exit(1)
    else:
        typer.secho(
            f"""bill: "{bill['Participant']}" was added """
            f"""with amount: ${bill['Amount']:.2f}""",
            fg=typer.colors.GREEN,
        )


@app.command(name='edit')
def edit(
        bill_id: int = typer.Argument(...),
        edit_type: str = typer.Option(
            ...,
            prompt=f'Which value ({"|".join([_.capitalize() for _ in VALID_TYPES])})'
                   f' do you want to edit?',
            autocompletion=_type_complete,
            callback=_type_callback,
        )
) -> None:
    """Edit an existing bill"""
    biller = get_bill()
    if edit_type == VALID_TYPES[0]: # AMOUNT
        new_amount = typer.prompt('Enter the new amount:')
        try:
            val_amount = float(new_amount)
        except ValueError:
            typer.secho(
                f"""The new amount entered ({new_amount}) is not a number.""",
                fg=typer.colors.RED
            )
            raise typer.Exit(1)
        bill, error = biller.edit_amount(bill_id, val_amount)
        if error:
            typer.secho(
                f'Editing bill (ID={bill_id}) failed with "{ERRORS[error]}"',
                fg=typer.colors.RED
            )
            raise typer.Exit(1)
        else:
            typer.secho(
                f"""Amount value of bill (ID={bill_id}) was edited: """
                f"""It is now: ${bill['Amount']:.2f}""",
                fg=typer.colors.GREEN,
            )
    elif edit_type == VALID_TYPES[1]: # PARTICIPANT
        new_val = typer.prompt('Enter the new participants list:')
        bill, error = biller.edit_participant(bill_id, new_val)
        if error:
            typer.secho(
                f'Editing bill (ID={bill_id}) failed with "{ERRORS[error]}"',
                fg=typer.colors.RED
            )
            raise typer.Exit(1)
        else:
            typer.secho(
                f"""Participant value of bill (ID={bill_id}) was edited: """
                f"""It is now: {bill['Participant']}""",
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
            f'| ${amount:.2f}{(len(columns[1]) - len(str(int(amount))) - 6) * " "}'
            f'| {parts}',
            fg=typer.colors.BLUE,
        )
    typer.secho('-' * len(headers) + '\n', fg=typer.colors.BLUE)


@app.command()
def remove(
        bill_id: int = typer.Argument(...),
        force: bool = typer.Option(
            False,
            '--force',
            '-f',
            help='Force deletion without confirmation.',
        ),
) -> None:
    """Remove a bill using its BILL_ID"""
    biller = get_bill()

    def _remove():
        bill, error = biller.remove(bill_id)
        if error:
            typer.secho(
                f'Removing bill # {bill_id} failed with "{ERRORS[error]}"',
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)
        else:
            typer.secho(
                f'bill # {bill_id}: \'{bill}\' was removed',
                fg=typer.colors.GREEN,
            )

    if force:
        _remove()
    else:
        bill_list = biller.get_bill_list()
        try:
            bill = bill_list[bill_id-1]
        except IndexError:
            typer.secho(
                'Invalid BILL_ID',
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)
        delete = typer.confirm(
            f'Delete bill # {bill_id}: {bill}?'
        )
        if delete:
            _remove()
        else:
            typer.echo('Operation canceled.')


@app.command(name='clear')
def remove_all(
        force: bool = typer.Option(
            ...,
            prompt='Delete all bills?',
            help='Force delete without confirmation.'
        ),
) -> None:
    """Remove all bills."""
    biller = get_bill()
    if force:
        error = biller.remove_all().error
        if error:
            typer.secho(
                f'Removing bills failed with "{ERRORS[error]}"',
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)
        else:
            typer.secho(
                'All bills were removed',
                fg=typer.colors.GREEN
            )
    else:
        typer.echo('Operation canceled')


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
