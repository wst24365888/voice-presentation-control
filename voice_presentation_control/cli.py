import typer
from voice_presentation_control import __app_name__, __version__
from voice_presentation_control import action_matcher
from voice_presentation_control.actor import Actor
from voice_presentation_control.controller import Controller
import voice_presentation_control.mic as mic
from voice_presentation_control.action_matcher import ActionMatcher
from voice_presentation_control.recognizer import Recognizer


app = typer.Typer(
    no_args_is_help=True,
    subcommand_metavar="COMMAND",
    add_completion=False,
)

app.add_typer(mic.app, name="mic")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} {__version__}")
        raise typer.Exit()


@app.command()
def start(
    input_device_index: int = typer.Option(
        1,
        "--input-device-index",
        "-i",
        help="Set input device index. Check your devices by `vpc mic list`.",
    ),
    threshold: int = typer.Option(
        3000,
        "--threshold",
        "-t",
        help="Set threshold. Test your environment by `vpc mic test`.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show the detailed log of voice-presentation-control.",
    ),
) -> None:
    actor = Actor(verbose=verbose)
    action_matcher = ActionMatcher()

    action_matcher.add_action("next page", actor.press_down)
    action_matcher.add_action("last page", actor.press_up)

    controller = Controller(
        mic.Mic(input_device_index),
        threshold,
        action_matcher,
        Recognizer(),
    )
    controller.start()


@app.callback()
def voice_presentation_control(
    _: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        help="Show the version of voice-presentation-control.",
    ),
) -> None:
    pass


def start_cli() -> None:
    app(prog_name="vpc")
