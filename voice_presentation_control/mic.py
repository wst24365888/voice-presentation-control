import typer
import pyaudio
from array import array
from voice_presentation_control import FORMAT, CHANNELS, RATE, CHUNK


app = typer.Typer(
    no_args_is_help=True,
    subcommand_metavar="COMMAND",
)

audio = pyaudio.PyAudio()


class Mic:
    def __init__(self, input_device_index: int) -> None:
        self.input_device_index = input_device_index

    def start(self) -> None:
        return audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            frames_per_buffer=CHUNK,
            input=True,
            input_device_index=self.input_device_index
        )


@app.command()
def list() -> None:
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')

    for i in range(0, numdevices):
        if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print("Input Device id ", i, " - ",
                  audio.get_device_info_by_host_api_device_index(0, i).get('name'))


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
        data_chunk = array('h', data)
        vol = max(data_chunk)
        print(vol)


if __name__ == "__main__":
    app()
