import os
import time
import wave
import pyaudio
from array import array
from voice_presentation_control.action_matcher import ActionMatcher
from voice_presentation_control.mic import Mic
from voice_presentation_control.recognizer import Recognizer
from voice_presentation_control import FORMAT, CHANNELS, RATE, CHUNK, RECORD_SECONDS

audio = pyaudio.PyAudio()


class Controller:
    def __init__(self, mic: Mic, threshold: int, action_matcher: ActionMatcher, recognizer: Recognizer) -> None:
        self.mic = mic
        self.threshold = threshold
        self.action_matcher = action_matcher
        self.recognizer = recognizer

    def start(self) -> None:
        self.stream = self.mic.start()

        while True:
            data = self.stream.read(CHUNK)
            data_chunk = array('h', data)
            vol = max(data_chunk)

            if vol >= self.threshold:
                # print("recording triggered")

                frames = [data]
                flag = 0

                for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = self.stream.read(CHUNK)
                    frames.append(data)
                    data_chunk = array('h', data)
                    vol = max(data_chunk)

                    if vol < self.threshold:
                        flag += 1
                    else:
                        flag = 0

                    if flag >= 20:
                        # print("recording stopped")
                        break

                # print("recording saved")

                # FILE_NAME = f"./RECORDING-" + \
                #     time.strftime("%Y%m%d-%H%M%S") + ".wav"

                result = self.recognizer.recognize(b''.join(frames))
                if result is not None:
                    print(result, end=' ', flush=True)
                    hit = self.action_matcher.match(result)

                    if hit:
                        print("(HIT)", end=' ', flush=True)

                # os.remove(FILE_NAME)
