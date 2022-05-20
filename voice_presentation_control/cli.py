import json
import os
from typing import Callable, Dict

import pyautogui
import typer

import voice_presentation_control.mic as mic
from voice_presentation_control import __app_name__, __version__
from voice_presentation_control.action_matcher import ActionMatcher
from voice_presentation_control.controller import Controller
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
    chunk: int = typer.Option(
        4096,
        "--chunk",
        "-c",
        help="Set record chunk.",
    ),
    lang: str = typer.Option(
        "en",
        "--language",
        "-l",
        help="Set language to recognize.",
    ),
    rate: int = typer.Option(
        44100,
        "--rate",
        "-r",
        help="Set input stream rate.",
    ),
) -> None:
    action_matcher = ActionMatcher()

    try:
        with open(os.path.join(os.path.dirname(__file__)) + "/configs/actions.json") as f:
            data = json.load(f)

            try:
                actions: Dict[str, str] = data[lang]
                for action_name, pyautogui_instruction in actions.items():
                    action: Callable[[str], None] = lambda bind_instruction=pyautogui_instruction: pyautogui.press(
                        bind_instruction
                    )
                    action_matcher.add_action(action_name=action_name, action=action)
            except KeyError:
                raise KeyError(f"Language '{lang}' is not set in actions.json")
    except FileNotFoundError:
        raise FileNotFoundError(f"Language '{lang}' is not supported.")

    controller = Controller(
        mic.Mic(input_device_index=input_device_index),
        threshold,
        chunk,
        rate,
        action_matcher,
        Recognizer(lang=lang),
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
