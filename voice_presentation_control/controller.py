from array import array
import os
import pyaudio
from threading import Thread

from queue import Queue

from voice_presentation_control.action_matcher import ActionMatcher
from voice_presentation_control.mic import Mic
from voice_presentation_control.recognizer import Recognizer
import numpy
import wave

audio = pyaudio.PyAudio()
MAX_RECORD_SECOND=2

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
        self.tmp_frame_q = Queue(maxsize=int(self.rate / self.chunk)//1.5)
        self.record_frame_q = Queue(maxsize=int(self.rate / self.chunk)*MAX_RECORD_SECOND)
    def put_queue(self,_queue,item)->None:
        if _queue.full():
                _queue.get()
        _queue.put(item)

    def start(self) -> None:
        self.stream = self.mic.start(self.chunk, self.rate)

        while True:
            data = self.stream.read(self.chunk)
            data_chunk = array("h", data)
            vol = max(data_chunk)
            self.put_queue(self.tmp_frame_q,data)

            if vol >= self.threshold:
                # print("recording triggered")

                for qv in list(self.tmp_frame_q.queue):
                    self.put_queue(self.record_frame_q,qv)

                flag = 0
                counter=len(list(self.tmp_frame_q.queue))-1
                while flag<int(self.rate / self.chunk)*1.5:
                    counter+=1
                    data = self.stream.read(self.chunk)
                    self.put_queue(self.record_frame_q,data)
                    data_chunk = array("h", data)
                    vol = max(data_chunk)

                    if vol < self.threshold:
                        flag += 1
                    else:
                        flag = 0

                    if self.record_frame_q.full():
                        if counter % int((self.rate / self.chunk)*MAX_RECORD_SECOND/2) == 0:
                            record_frames=list(self.record_frame_q.queue)
                            Thread(target=self.get_recognizer_result,args=(record_frames,)).start()
                            #print("recording stopped")
                            #save_frames_to_wav(frames)


                self.tmp_frame_q.queue.clear()
                self.record_frame_q.queue.clear()

    def get_recognizer_result(self,record_frames):
        result = self.recognizer.recognize(b"".join(record_frames), self.rate)
        #save_frames_to_wav(record_frames)
        if result is not None:
            print(result, end=" ", flush=True)
            hit = self.action_matcher.match(result)
            if hit:
                print("(HIT)", end=" ", flush=True)

def save_frames_to_wav(frames):
    wavefile = wave.open('voice_presentation_control/wave_tmp/test_save.wav', 'wb')
    wavefile.setnchannels(1)
    wavefile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wavefile.setframerate(44100)
    for frame in frames:
        wavefile.writeframes(frame)