import json
from typing import Optional
import wave
import vosk
import os


class Recognizer:
    def __init__(self) -> None:        
        vosk.SetLogLevel(-1)
        self.model = vosk.Model(os.path.join(os.path.dirname(__file__)) + "/vosk_models/vosk-model-small-en-us-0.15")

    def recognize(self, data: bytes) -> Optional[str]:
        rec = vosk.KaldiRecognizer(self.model, 44100)
        rec.SetWords(True)
        rec.AcceptWaveform(data)

        return json.loads(rec.FinalResult())["text"]
