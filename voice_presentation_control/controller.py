from array import array

import pyaudio

from voice_presentation_control.action_matcher import ActionMatcher
from voice_presentation_control.mic import Mic
from voice_presentation_control.recognizer import Recognizer

audio = pyaudio.PyAudio()

LONGEST_RECORDING_SECONDS = 2**15


class Controller:
    def __init__(
        self,
        mic: Mic,
        threshold: int,
        chunk: int,
        rate: int,
        action_matcher: ActionMatcher,
        recognizer: Recognizer,
    ) -> None:
        self.mic = mic
        self.threshold = threshold
        self.chunk = chunk
        self.rate = rate
        self.action_matcher = action_matcher
        self.recognizer = recognizer

    def start(self) -> None:
        self.stream = self.mic.start(self.chunk, self.rate)

        while True:
            data = self.stream.read(self.chunk)
            data_chunk = array("h", data)
            vol = max(data_chunk)

            if vol >= self.threshold:
                # recording triggered
                frames = [data]
                flag = 0

                for _ in range(0, int(self.rate / self.chunk * LONGEST_RECORDING_SECONDS)):
                    data = self.stream.read(self.chunk)
                    frames.append(data)
                    data_chunk = array("h", data)
                    vol = max(data_chunk)

                    if vol < self.threshold:
                        flag += 1
                    else:
                        flag = 0

                    # recording stopped
                    if flag >= 20:
                        break

                result = self.recognizer.recognize(b"".join(frames), self.rate)
                if result is not None:
                    print(result, end=" ", flush=True)
                    hit = self.action_matcher.match(result)

                    if hit:
                        print("(HIT)", end=" ", flush=True)
