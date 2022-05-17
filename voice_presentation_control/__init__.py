import pyaudio

__app_name__ = "voice_presentation_control"
__version__ = "0.2.1"

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 2 ** 10
