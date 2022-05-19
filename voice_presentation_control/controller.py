from array import array
import os
import pyaudio

from queue import Queue

from voice_presentation_control.action_matcher import ActionMatcher
from voice_presentation_control.mic import Mic
from voice_presentation_control.recognizer import Recognizer
import numpy
import wave

audio = pyaudio.PyAudio()

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
        self.frames_q = Queue(maxsize=int(self.rate / self.chunk)//1.5)

    def start(self) -> None:
        self.stream = self.mic.start(self.chunk, self.rate)

        while True:
            data = self.stream.read(self.chunk)
            data_chunk = array("h", data)
            vol = max(data_chunk)
            if self.frames_q.full():
                self.frames_q.get()
            self.frames_q.put(data)

            if vol >= self.threshold:
                # print("recording triggered")

                frames = list(self.frames_q.queue)
                flag = 0

                for _ in range(0, int(self.rate / self.chunk)*3):# * RECORD_SECONDS)):
                    data = self.stream.read(self.chunk)
                    frames.append(data)
                    data_chunk = array("h", data)
                    vol = max(data_chunk)

                    if vol < self.threshold:
                        flag += 1
                    else:
                        flag = 0

                    if flag >= int(self.rate / self.chunk):
                        print("recording stopped")
                        break
                self.frames_q.empty()
                #save_frames_to_wav(frames)
                result = self.recognizer.recognize(b"".join(frames), self.rate)
                if result is not None:
                    print(result, end=" ", flush=True)
                    hit = self.action_matcher.match(result)

                    if hit:
                        print("(HIT)", end=" ", flush=True)

                # os.remove(FILE_NAME)

def save_frames_to_wav(frames):
    wavefile = wave.open('voice_presentation_control/wave_tmp/test_save.wav', 'wb')
    wavefile.setnchannels(1)
    wavefile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wavefile.setframerate(44100)
    for frame in frames:
        wavefile.writeframes(frame)

