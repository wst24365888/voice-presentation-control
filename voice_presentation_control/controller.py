import wave
from array import array
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from multiprocessing import cpu_count
from queue import Queue
from typing import List
import numpy as np

import pyaudio

from voice_presentation_control.action_matcher import ActionMatcher
from voice_presentation_control.mic import Mic
from voice_presentation_control.recognizer import Recognizer

audio = pyaudio.PyAudio()

TMP_FRAME_SECOND = 1 / 1.5
MAX_SILENT_SECOND = 0.5


class Controller:
    def __init__(
        self,
        mic: Mic,
        threshold: int,
        chunk: int,
        rate: int,
        max_record_seconds: int,
        action_matcher: ActionMatcher,
        recognizer: Recognizer,
    ) -> None:
        self.mic = mic
        self.threshold = threshold
        self.chunk = chunk
        self.rate = rate
        self.action_matcher = action_matcher
        self.recognizer = recognizer

        self.max_record_seconds = max_record_seconds  # must be two times longer than max_instruction_seconds
        self.chunk_sliding_step = self.max_record_seconds / 1.5

        self.tmp_frame_q = Queue(maxsize=int(self.rate / self.chunk * TMP_FRAME_SECOND))
        self.record_frame_q = Queue(maxsize=int(self.rate / self.chunk * self.max_record_seconds))

        self.executor = ThreadPoolExecutor(max_workers=cpu_count())



    def put_queue(self, _queue: Queue, item: bytes) -> None:
        if _queue.full():
            _queue.get()
        _queue.put(item)

    def adjust_volume(self, record_frames: list, std_vol: int) -> None:
        # find max volume in frames
        max_amp = 0
        for f in record_frames:
            data_chunk = array("h", f)
            max_amp = max(max_amp,max(data_chunk))
        #volume_scaler = (std_vol/max_amp)

        # find min volume in frames
        min_amp = 32767
        for f in record_frames:
            data_chunk = array("h", f)
            min_amp = min(min_amp, min(data_chunk))

        interval = max_amp + min_amp

        # adjust volume by normalization
        for i in range(0, len(record_frames)):
            data_chunk = array("h", record_frames[i])
            for j in range(0, len(data_chunk)):
                #data_chunk[j] = int(float(data_chunk[j]) * volume_scaler)

                temp_data_chunk = float(data_chunk[j] - min_amp) / interval * max_amp
                if temp_data_chunk > 32767:
                    temp_data_chunk = 32767
                data_chunk[j] = int(temp_data_chunk)
            record_frames[i] = array.tobytes(data_chunk)

    def start(self) -> None:
        self.stream = self.mic.start(self.chunk, self.rate)
        self.standard_volume = 10000

        while True:
            data = self.stream.read(self.chunk)
            self.put_queue(self.tmp_frame_q, data)

            data_chunk = array("h", data)
            max_vol = max(data_chunk)

            if max_vol >= self.threshold:

                # print("recording triggered")

                silent_flag = 0
                progress_counter = len(list(self.tmp_frame_q.queue))

                while self.tmp_frame_q.qsize() > 0:
                    self.put_queue(self.record_frame_q, self.tmp_frame_q.get())

                while silent_flag < self.rate / self.chunk * MAX_SILENT_SECOND:
                    progress_counter += 1

                    data = self.stream.read(self.chunk)
                    self.put_queue(self.record_frame_q, data)

                    data_chunk = array("h", data)
                    max_vol = max(data_chunk)

                    if max_vol < self.threshold:
                        silent_flag += 1
                    else:
                        silent_flag = 0

                    if self.record_frame_q.full():
                        # sliding window
                        if progress_counter % int((self.rate / self.chunk) * self.chunk_sliding_step) == 0:
                            record_frames = list(self.record_frame_q.queue)
                            # adjust volume before getting recognizer result
                            self.adjust_volume(record_frames, self.standard_volume)

                            self.executor.submit(self.get_recognizer_result, record_frames)

                if not self.record_frame_q.full():
                    # for very short record
                    record_frames = list(self.record_frame_q.queue)
                    # adjust volume before getting recognizer result
                    #self.save_frames_to_wav(record_frames, 0)
                    self.adjust_volume(record_frames, self.standard_volume)
                    #self.save_frames_to_wav(record_frames, 1)
                    self.executor.submit(self.get_recognizer_result, record_frames)

                record_frame_dq: deque = self.record_frame_q.queue
                record_frame_dq.clear()

                assert self.tmp_frame_q.empty()
                assert self.record_frame_q.empty()

    def get_recognizer_result(self, record_frames: List[bytes]) -> None:
        result = self.recognizer.recognize(b"".join(record_frames), self.rate)
        # self.save_frames_to_wav(record_frames)
        if result is not None:
            print(result, end=" ", flush=True)
            msg = self.action_matcher.match(result)
            print(f"({msg})", flush=True)

    def save_frames_to_wav(self, frames: List[bytes], num_files : int) -> None:
        #num_files = len(glob("voice_presentation_control/wav_files/*.wav"))
        #wavefile = wave.open(f"voice_presentation_control/wav_files/test_save_{num_files}.wav", "wb")
        wavefile = wave.open(f"./wav_files/test_save_{num_files}.wav", "wb")

        wavefile.setnchannels(1)
        wavefile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        wavefile.writeframes(b"".join(frames))
