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

TMP_FRAME_SECOND = 0.5
MAX_SILENT_SECOND = 0.5


class Controller:
    def __init__(
        self,
        mic: Mic,
        threshold: float,
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
        self.record_frame_q = Queue(maxsize=int(self.rate / self.chunk * (TMP_FRAME_SECOND + self.max_record_seconds)))
        self.executor = ThreadPoolExecutor(max_workers=cpu_count())

    def put_queue(self, _queue: Queue, item: bytes) -> None:
        if _queue.full():
            _queue.get()
        _queue.put(item)

    def get_zcr(self,data):

        data=np.array(data)
        data = data -np.mean(data)
        data1 = np.array(data[1:])
        data2 = np.array(data[:-1])

        zcr = np.sum(np.multiply(data1,data2)<=0)/(len(data)-1)

        return round(zcr,2)
    def get_eng(self,data):

        data=np.array(data)

        data_mean = round(np.sum(np.abs(data)))
        data_std = round(np.std(data))
        return data_mean,data_std

    def start(self) -> None:
        stream = self.mic.start(self.chunk, self.rate)
        while True:
            data = stream.read(self.chunk)
            self.put_queue(self.tmp_frame_q, data)

            data_chunk = array("h", data)
            zcr = self.get_zcr(data_chunk)
            max_vol = max(data_chunk)
            # d_mean,d_std =self.get_eng(data_chunk)
            # print(zcr,max_vol,d_mean,d_std,sep='\t|')

            if zcr>self.threshold or  max_vol>750:
                # print("recording triggered")

                silent_flag = 0
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
                    # d_mean,d_std =self.get_eng(data_chunk)
                    # print(zcr,max_vol,d_mean,d_std,sep='\t|')

                    if max_vol>750 :
                        silent_flag = 0
                    else:
                        silent_flag += 1

                    if self.record_frame_q.full():
                        # sliding window
                        if progress_counter % int((self.rate / self.chunk) * self.chunk_sliding_step) == 0:
                            record_frames = list(self.record_frame_q.queue)
                            self.executor.submit(self.get_recognizer_result, record_frames)

                if not self.record_frame_q.full():
                    # for very short record
                    record_frames = list(self.record_frame_q.queue)
                    self.executor.submit(self.get_recognizer_result, record_frames)

                record_frame_dq: deque = self.record_frame_q.queue
                record_frame_dq.clear()
                # assert self.tmp_frame_q.empty()
                assert self.record_frame_q.empty()

    def get_recognizer_result(self, record_frames: List[bytes]) -> None:
        #self.save_frames_to_wav(b"".join(record_frames))
        record_wav_bytes = self.audio_preprocess(record_frames)
        #self.save_frames_to_wav(record_wav_bytes)
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
        min_threshold: int = 0
        max_volume_value: int = 16000
        max_values  = max(abs(np.array(wave_values)))
        wave_values_process = (wave_values/max_values)*max_volume_value
        wave_values_arr = array("h", wave_values_process.astype(int))

        return wave_values_arr

    def denoise(self, wave_values: np.ndarray) -> np.ndarray:
        wave_values = logmmse.logmmse(data=wave_values, sampling_rate=self.rate, noise_threshold=0.15, window_size=0)

        return wave_values

    def freqs_process(self, fft_wave: np.ndarray) -> np.ndarray:
        sample_num = len(fft_wave)

        times = np.arange(sample_num) / self.rate
        vib_fft = np.fft.fft(fft_wave)
        fft_freqs = np.fft.fftfreq(sample_num, times[1] - times[0])

        # filter
        fft_filter = vib_fft.copy()
        noise_indices = np.where((abs(fft_freqs)>8000) & (abs(fft_freqs)<10000))
        fft_filter[noise_indices] = fft_filter[noise_indices]*0.5#.1

        noise_indices = np.where(abs(fft_freqs)>=10000)
        fft_filter[noise_indices] = fft_filter[noise_indices]*0.1#.05

        noise_indices = np.where(abs(fft_freqs)>=15000)
        fft_filter[noise_indices] = fft_filter[noise_indices]*0

        filter_wave_ifft = np.fft.ifft(fft_filter).real

        return filter_wave_ifft.astype(int)

    def audio_preprocess(self, record_frames: List[bytes]) -> bytes:
        wave_values = np.array(array("h", b"".join(record_frames)))

        wave_values = self.freqs_process(wave_values)
        #wave_values = self.denoise(wave_values)
        wave_values_arr = self.volume_process(wave_values)

        return wave_values_arr.tobytes()
