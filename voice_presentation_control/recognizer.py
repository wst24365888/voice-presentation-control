from pyparsing import Optional
import speech_recognition as sr


class Recognizer:
    def __init__(self) -> None:
        self.r = sr.Recognizer()

    def recognize(self, filename: str) -> Optional[str]:
        with sr.AudioFile(filename) as source:
            audio = self.r.record(source)

        try:
            return self.r.recognize_sphinx(audio)
        except sr.UnknownValueError:
            # print("Audio parse error.")
            pass
        except sr.RequestError as e:
            # print("Sphinx error: {0}".format(e))
            pass
