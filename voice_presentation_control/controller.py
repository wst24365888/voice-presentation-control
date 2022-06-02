import wave
from array import array
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from multiprocessing import cpu_count
from queue import Queue
from typing import List

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

    def adjust_volume(self, record_frames: list) -> list:
        max_amp = max(list(map(lambda f: max(array("h", f)), record_frames)))
        min_amp = min(list(map(lambda f: min(array("h", f)), record_frames)))

        mid = (max_amp + min_amp) / 2
        gain = (max_amp - min_amp) / 2

        def formula(x): int(float(x - mid) / gain * 32727)
        def normalize(f): array.tobytes(array("h", list(map(formula, array("h", f)))))
        record_frames = list(map(normalize, record_frames))

        return record_frames

    def start(self) -> None:
        stream = self.mic.start(self.chunk, self.rate)

        while True:
            data = stream.read(self.chunk)
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

                    data = stream.read(self.chunk)
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
                            record_frames = self.adjust_volume(record_frames)
                            self.executor.submit(self.get_recognizer_result, record_frames)

                if not self.record_frame_q.full():
                    # for very short record
                    record_frames = list(self.record_frame_q.queue)
                    #self.save_frames_to_wav(record_frames)
                    record_frames = self.adjust_volume(record_frames)
                    #self.save_frames_to_wav(record_frames)
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

    def save_frames_to_wav(self, frames: List[bytes]) -> None:
        num_files = len(glob("voice_presentation_control/wav_files/*.wav"))
        wavefile = wave.open(f"voice_presentation_control/wav_files/test_save_{num_files}.wav", "wb")
        wavefile.setnchannels(1)
        wavefile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        wavefile.writeframes(b"".join(frames))
