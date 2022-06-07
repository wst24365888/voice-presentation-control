import wave
from array import array
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
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

TMP_FRAME_SECOND = 0.5
MAX_SILENT_SECOND = 0.5
MIN_LOUD_SECOND = 0.4


class Controller:
    def __init__(
        self,
        mic: Mic,
        vol_threshold: int,
        zcr_threshold: float,
        chunk: int,
        rate: int,
        max_record_seconds: int,
        action_matcher: ActionMatcher,
        recognizer: Recognizer,
    ) -> None:
        self.mic = mic
        self.vol_threshold = vol_threshold
        self.zcr_threshold = zcr_threshold
        self.chunk = chunk
        self.rate = rate
        self.action_matcher = action_matcher
        self.recognizer = recognizer

        self.max_record_seconds = max_record_seconds  # must be two times longer than max_instruction_seconds
        self.chunk_sliding_step = self.max_record_seconds / 1.5

        self.tmp_frame_q = Queue(maxsize=int(self.rate / self.chunk * TMP_FRAME_SECOND))
        self.record_frame_q = Queue(maxsize=int(self.rate / self.chunk * (TMP_FRAME_SECOND + self.max_record_seconds)))
        self.executor = ThreadPoolExecutor(max_workers=cpu_count())

    def put_queue(self, _queue: Queue, item: bytes) -> None:
        if _queue.full():
            _queue.get()
        _queue.put(item)

    def get_zcr(self, data: array) -> float:
        data_arr = np.array(data)
        data_arr = data_arr - np.mean(data_arr)
        data_front = np.array(data[1:])
        data_back = np.array(data[:-1])

        zcr: float = np.sum(np.multiply(data_front, data_back) <= 0) / (len(data) - 1)

        return round(zcr, 2)

    def start(self) -> None:
        stream = self.mic.start(self.chunk, self.rate)
        loud_flag: int = 0

        while True:
            data = stream.read(self.chunk)
            self.put_queue(self.tmp_frame_q, data)

            data_chunk = array("h", data)
            zcr = self.get_zcr(data_chunk)
            max_vol = max(data_chunk)

            if zcr > self.zcr_threshold or max_vol > self.vol_threshold:
                loud_flag += 1
            else:
                loud_flag = 0

            if loud_flag >= self.rate / self.chunk * MIN_LOUD_SECOND:
                # print("recording triggered")

                silent_flag: int = 0

                progress_counter = len(list(self.tmp_frame_q.queue))

                while self.tmp_frame_q.qsize() > 0:
                    self.put_queue(self.record_frame_q, self.tmp_frame_q.get())

                while silent_flag < self.rate / self.chunk * MAX_SILENT_SECOND:
                    progress_counter += 1

                    data = stream.read(self.chunk)
                    self.put_queue(self.record_frame_q, data)
                    self.put_queue(self.tmp_frame_q, data)

                    data_chunk = array("h", data)
                    zcr = self.get_zcr(data_chunk)
                    max_vol = max(data_chunk)

                    if max_vol > self.vol_threshold:
                        silent_flag = 0
                    else:
                        silent_flag += 1

                    if progress_counter % int((self.rate / self.chunk) * self.chunk_sliding_step) == 0:
                        record_frames = list(self.record_frame_q.queue)
                        future: Future[bool] = self.executor.submit(self.get_recognizer_result, record_frames)

                        if future.result():
                            record_frame_dq: deque = self.record_frame_q.queue
                            record_frame_dq.clear()

                            assert self.record_frame_q.empty()

                # print("recording stopped")

                loud_flag = 0

                record_frames = list(self.record_frame_q.queue)
                self.executor.submit(self.get_recognizer_result, record_frames)

                record_frame_dq: deque = self.record_frame_q.queue
                record_frame_dq.clear()

                assert self.record_frame_q.empty()

    def get_recognizer_result(self, record_frames: List[bytes]) -> bool:
        # self.save_frames_to_wav(b"".join(record_frames))
        record_wav_bytes = self.audio_preprocess(record_frames)
        # self.save_frames_to_wav(record_wav_bytes)
        result = self.recognizer.recognize(record_wav_bytes, self.rate)

        hit: bool = False

        if result is not None:
            hit, msg = self.action_matcher.match(result)

            if result != "":
                print(f"{result} ({msg})", flush=True)

        return hit

    def save_frames_to_wav(self, frames: bytes) -> None:
        num_files = len(glob("voice_presentation_control/wav_files/*.wav"))

        wavefile = wave.open(f"voice_presentation_control/wav_files/test_save_{num_files}.wav", "wb")
        wavefile.setnchannels(1)
        wavefile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        wavefile.writeframes(frames)

    def volume_process(self, wave_values: np.ndarray) -> array:
        max_volume_value: int = 16000
        max_values = max(abs(np.array(wave_values)))
        wave_values_process = (wave_values / max_values) * max_volume_value
        wave_values_arr = array("h", wave_values_process.astype(int))

        return wave_values_arr

    def freqs_process(self, fft_wave: np.ndarray) -> np.ndarray:
        sample_num = len(fft_wave)

        times = np.arange(sample_num) / self.rate
        vib_fft = np.fft.fft(fft_wave)
        fft_freqs = np.fft.fftfreq(sample_num, times[1] - times[0])

        # filter
        fft_filter = vib_fft.copy()
        fft_filter = fft_filter / 10

        noise_indices = np.where(((abs(fft_freqs) >= 100) & (abs(fft_freqs) < 200)))  # n
        fft_filter[noise_indices] = fft_filter[noise_indices] * 10

        noise_indices = np.where(((abs(fft_freqs) >= 1500) & (abs(fft_freqs) < 2000)))  # p
        fft_filter[noise_indices] = fft_filter[noise_indices] * 2

        noise_indices = np.where(((abs(fft_freqs) >= 3000) & (abs(fft_freqs) < 3500)))  # n
        fft_filter[noise_indices] = fft_filter[noise_indices] * 5

        noise_indices = np.where(((abs(fft_freqs) >= 5000) & (abs(fft_freqs) < 8000)))  # x
        fft_filter[noise_indices] = fft_filter[noise_indices]

        noise_indices = np.where((abs(fft_freqs) > 8000))
        fft_filter[noise_indices] = fft_filter[noise_indices] * 0  # .1

        filter_wave_ifft = np.fft.ifft(fft_filter).real

        return filter_wave_ifft.astype(int)

    def audio_preprocess(self, record_frames: List[bytes]) -> bytes:
        wave_values = np.array(array("h", b"".join(record_frames)))

        wave_values = self.freqs_process(wave_values)
        wave_values_arr = self.volume_process(wave_values)

        return wave_values_arr.tobytes()
