import wave
from array import array
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from multiprocessing import cpu_count
from queue import Queue
from typing import List

import logmmse
import numpy as np
import pyaudio

from voice_presentation_control.action_matcher import ActionMatcher
from voice_presentation_control.mic import Mic
from voice_presentation_control.recognizer import Recognizer

audio = pyaudio.PyAudio()

TMP_FRAME_SECOND = 1 / 1.5
MAX_SILENT_SECOND = 0.5
MAX_LOUD_SECOND = 0.5


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

    def start(self) -> None:
        stream = self.mic.start(self.chunk, self.rate)
        loud_flag = 0

        while True:
            data = stream.read(self.chunk)
            self.put_queue(self.tmp_frame_q, data)

            data_chunk = array("h", data)
            max_vol = max(data_chunk)
            if max_vol >= self.threshold:
                # print("recording triggered")

                silent_flag = 0
                loud_flag += 1
                # save the temp queue into record frame if max_vol >= threshold for 0.5 seconds
                while loud_flag >= self.rate / self.chunk * MAX_LOUD_SECOND:
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
                                self.executor.submit(self.get_recognizer_result, record_frames)

                    # print("recording stopped")

                    if not self.record_frame_q.full():
                        # for very short record
                        record_frames = list(self.record_frame_q.queue)
                        self.executor.submit(self.get_recognizer_result, record_frames)

                    record_frame_dq: deque = self.record_frame_q.queue
                    record_frame_dq.clear()
                    loud_flag = 0

                    assert self.tmp_frame_q.empty()
                    assert self.record_frame_q.empty()
            else:
                loud_flag = 0
                tmp_frame_dq: deque = self.tmp_frame_q.queue
                tmp_frame_dq.clear()

    def get_recognizer_result(self, record_frames: List[bytes]) -> None:
        # self.save_frames_to_wav(b"".join(record_frames))

        record_wav_bytes = self.audio_preprocess(record_frames)
        # self.save_frames_to_wav(record_wav_bytes)

        result = self.recognizer.recognize(record_wav_bytes, self.rate)

        if result is not None:
            print(result, end=" ", flush=True)
            msg = self.action_matcher.match(result)
            print(f"({msg})", flush=True)

    def save_frames_to_wav(self, frames: bytes) -> None:
        num_files = len(glob("voice_presentation_control/wav_files/*.wav"))
        wavefile = wave.open(f"voice_presentation_control/wav_files/test_save_{num_files}.wav", "wb")
        wavefile.setnchannels(1)
        wavefile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        wavefile.writeframes(frames)

    def volume_process(self, wave_values: np.ndarray) -> array:
        def volume_process_func(wave_value: int) -> int:
            if wave_value <= min_threshold and wave_value >= -min_threshold:
                wave_value = 0
            elif wave_value > min_threshold:
                wave_value = int((wave_value - min_threshold) / max_g * max_volume_value)
            elif wave_value < 0:
                wave_value = int((wave_value + min_threshold) / min_g * max_volume_value)
            return wave_value

        min_threshold: int = 40
        max_volume_value: int = 15000

        max_w: int = max(wave_values)
        min_w: int = min(wave_values)
        max_g: int = max_w - min_threshold
        min_g: int = abs(min_w) - min_threshold

        wave_values_map = map(volume_process_func, wave_values)
        wave_values_arr = array("h", wave_values_map)

        return wave_values_arr

    def denoise(self, wave_values: np.ndarray) -> np.ndarray:
        wave_values = logmmse.logmmse(data=wave_values, sampling_rate=self.rate, noise_threshold=0.2, window_size=67)

        return wave_values

    def freqs_process(self, fft_wave: np.ndarray) -> np.ndarray:
        sample_num = len(fft_wave)

        times = np.arange(sample_num) / self.rate
        vib_fft = np.fft.fft(fft_wave)
        fft_freqs = np.fft.fftfreq(sample_num, times[1] - times[0])

        # filter
        fft_filter = vib_fft.copy()
        noise_indices = np.where((abs(fft_freqs) > 6000) & (abs(fft_freqs) < 12000))
        fft_filter[noise_indices] = fft_filter[noise_indices] * 0.4

        noise_indices = np.where(abs(fft_freqs) >= 12000)
        fft_filter[noise_indices] = fft_filter[noise_indices] * 0.05

        noise_indices = np.where((abs(fft_freqs) <= 6000) & (abs(fft_freqs) > 3000))
        fft_filter[noise_indices] = fft_filter[noise_indices] * 0.8

        noise_indices = np.where((abs(fft_freqs) <= 3000))
        fft_filter[noise_indices] = fft_filter[noise_indices]

        filter_wave_ifft = np.fft.ifft(fft_filter).real

        return filter_wave_ifft.astype(int)

    def audio_preprocess(self, record_frames: List[bytes]) -> bytes:
        wave_values = np.array(array("h", b"".join(record_frames)))
        wave_values = self.denoise(wave_values)
        wave_values = self.freqs_process(wave_values)
        wave_values_arr = self.volume_process(wave_values)

        return wave_values_arr.tobytes()
