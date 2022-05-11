from enum import Enum
import typer
from typing import Optional
from voice_presentation_control import __app_name__, __version__


app = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=True,
    subcommand_metavar="",
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} {__version__}")
        raise typer.Exit()


@app.callback()
def voice_presentation_control(
    _: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the version of compose_viz.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    pass


def start_cli() -> None:
    app(prog_name=__app_name__)
