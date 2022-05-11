import typer
from typing import Optional
from voice_presentation_control import __app_name__, __version__
from voice_presentation_control.perform_action import PerformAction


app = typer.Typer(
    invoke_without_command=True,
    subcommand_metavar="",
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} {__version__}")
        raise typer.Exit()


@app.callback()
def voice_presentation_control(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show the detailed log of voice-presentation-control.",
    ),
    _: Optional[bool] = typer.Option(
        None,
        "--version",
        help="Show the version of voice-presentation-control.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    perform_action = PerformAction(verbose=verbose)


def start_cli() -> None:
    app(prog_name="vpc")
