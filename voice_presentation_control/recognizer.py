import json
import os
from typing import Optional

import vosk


class Recognizer:
    def __init__(self) -> None:
        vosk.SetLogLevel(-1)
        self.model = vosk.Model(os.path.join(os.path.dirname(__file__)) + "/vosk_models/vosk-model-small-en-us-0.15")

    def recognize(self, data: bytes, rate: int) -> Optional[str]:
        rec = vosk.KaldiRecognizer(self.model, rate)
        rec.SetWords(True)
        rec.AcceptWaveform(data)

        return json.loads(rec.FinalResult())["text"]
