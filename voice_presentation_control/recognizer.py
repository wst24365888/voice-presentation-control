import json
import os
from typing import Optional

import vosk


class Recognizer:
    def __init__(self, lang: str, grammar: str) -> None:
        vosk.SetLogLevel(-1)
        self.grammar = grammar
        try:
            self.model = vosk.Model(os.path.join(os.path.dirname(__file__)) + f"/vosk_models/{lang}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Language '{lang}' is not supported.")

    def recognize(self, data: bytes, rate: int) -> Optional[str]:
        rec = vosk.KaldiRecognizer(self.model, rate, self.grammar)
        rec.SetWords(True)
        rec.AcceptWaveform(data)

        return json.loads(rec.FinalResult())["text"]
