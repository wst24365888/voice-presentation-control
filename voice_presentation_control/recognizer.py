import json
from typing import Optional
import wave
import vosk
import os


class Recognizer:
    def __init__(self) -> None:        
        vosk.SetLogLevel(-1)
        self.model = vosk.Model(os.path.join(os.path.dirname(__file__)) + "/vosk_models/vosk-model-small-en-us-0.15")

    def recognize(self, filename: str) -> Optional[str]:
        wf = wave.open(filename, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            raise ValueError("Audio file must be WAV format mono PCM.")

        rec = vosk.KaldiRecognizer(self.model, 44100)
        rec.SetWords(True)

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break

            rec.AcceptWaveform(data)

        return json.loads(rec.FinalResult())["text"]
