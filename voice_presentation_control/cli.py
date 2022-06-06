import json
import os
import platform
import subprocess
from enum import Enum
from typing import Callable, Dict, List, Union

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


class SupportedLanguage(str, Enum):
    en = "en"
    zh = "zh"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} {__version__}")
        raise typer.Exit()


@app.command()
def config():
    config_file = os.path.join(os.path.dirname(__file__)) + "/configs/actions.json"

    if platform.system() == "Windows":
        os.startfile(config_file)  # type: ignore
    elif platform.system() == "Darwin":
        os.system("open " + config_file)
    else:
        subprocess.call(["xdg-open", config_file])


@app.command()
def start(
    input_device_index: int = typer.Option(
        1,
        "--input-device-index",
        "-i",
        help="Set input device index. Check your devices by `vpc mic list`.",
    ),
    vol_threshold: int = typer.Option(
        1000,
        "--vol-threshold",
        "-v",
        help="Set volume threshold. Test your environment by `vpc mic test`.",
    ),
    zcr_threshold: float = typer.Option(
        0.075,
        "--zcr-threshold",
        "-z",
        help="Set zcr threshold.",
    ),
    chunk: int = typer.Option(
        4096,
        "--chunk",
        "-c",
        help="Set record chunk.",
    ),
    rate: int = typer.Option(
        44100,
        "--rate",
        "-r",
        help="Set input stream rate.",
    ),
    max_record_seconds: int = typer.Option(
        3,
        "--max-record-seconds",
        "-s",
        help="Set max record seconds if your custom command is long.",
    ),
    lang: SupportedLanguage = typer.Option(
        "en",
        "--language",
        "-l",
        help="Set language to recognize.",
    ),
) -> None:
    action_matcher = ActionMatcher()
    actions: Dict[str, Union[str, List[str]]] = {}

    try:
        with open(os.path.join(os.path.dirname(__file__)) + "/configs/actions.json", encoding="utf-8") as f:
            data: dict = json.load(f)

            if data.get(lang):
                actions = data[lang]
            else:
                typer.echo(f"Language '{lang}' is not set in actions.json")
                raise typer.Exit()
    except FileNotFoundError:
        raise FileNotFoundError("Config file not found.")

    for action_name, pyautogui_instruction in actions.items():
        action: Callable[[Union[str, List[str]]], None]

        if type(pyautogui_instruction) is str:
            action = lambda bind_instruction=pyautogui_instruction: pyautogui.press(bind_instruction)  # noqa: E731
        else:
            action = lambda bind_instruction=pyautogui_instruction: pyautogui.hotkey(*bind_instruction)  # noqa: E731

        action_matcher.add_action(action_name=action_name, action=action)

    grammar: str = ""

    if lang == SupportedLanguage.en:
        grammar = '["{}", "[unk]"]'.format('", "'.join(actions.keys()))
    elif lang == SupportedLanguage.zh:
        action_names: List[str] = []
        for action_name in actions.keys():
            for character in action_name:
                action_names.append(character)
        grammar = '["{}", "[unk]"]'.format('", "'.join(action_names))

    controller = Controller(
        mic.Mic(input_device_index=input_device_index),
        vol_threshold,
        zcr_threshold,
        chunk,
        rate,
        max_record_seconds,
        action_matcher,
        Recognizer(lang=lang, grammar=grammar),
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
