from array import array

import pyaudio
import typer

from voice_presentation_control import CHANNELS, CHUNK, FORMAT, RATE

app = typer.Typer(
    no_args_is_help=True,
    subcommand_metavar="COMMAND",
)

audio = pyaudio.PyAudio()


class Mic:
    def __init__(self, input_device_index: int) -> None:
        self.input_device_index = input_device_index

    def start(self) -> pyaudio.Stream:
        return audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            frames_per_buffer=CHUNK,
            input=True,
            input_device_index=self.input_device_index,
        )


@app.command()
def list() -> None:
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get("deviceCount")

    if numdevices is None:
        typer.echo("No devices found")
        return

    for i in range(0, int(numdevices)):
        maxInputChannels = audio.get_device_info_by_host_api_device_index(0, i).get("maxInputChannels")
        if maxInputChannels is None:
            continue

        if (int(maxInputChannels)) > 0:
            print(
                "Input Device id ",
                i,
                " - ",
                audio.get_device_info_by_host_api_device_index(0, i).get("name"),
            )


@app.command()
def test(
    input_device_index: int = typer.Option(
        1,
        "--input-device-index",
        "-i",
        help="Set input device index. Check your devices by `vpc mic list`.",
    ),
) -> None:
    stream = Mic(input_device_index).start()

    while True:
        data = stream.read(CHUNK)
        data_chunk = array("h", data)
        vol = max(data_chunk)
        print(vol)


if __name__ == "__main__":
    app()
