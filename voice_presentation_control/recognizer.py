import json
import os
from typing import Optional

import vosk


class Recognizer:
    def __init__(self, lang: str, grammar: Optional[str]) -> None:
        vosk.SetLogLevel(-1)
        self.grammar = grammar
        try:
            self.model = vosk.Model(os.path.join(os.path.dirname(__file__)) + f"/vosk_models/{lang}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Language '{lang}' is not supported.")

    def recognize(self, data: bytes, rate: int) -> Optional[str]:
        rec: vosk.KaldiRecognizer
        if self.grammar is not None:
            rec = vosk.KaldiRecognizer(self.model, rate, self.grammar)
        else:
            rec = vosk.KaldiRecognizer(self.model, rate)

        rec.SetWords(True)
        rec.AcceptWaveform(data)

        return json.loads(rec.FinalResult())["text"]
