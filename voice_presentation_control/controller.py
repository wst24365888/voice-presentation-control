import wave
from array import array
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from multiprocessing import cpu_count
from queue import Queue
from typing import List
import librosa
import numpy as np
import logmmse

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
                            self.executor.submit(self.get_recognizer_result, record_frames)
                            print('predict')

                if not self.record_frame_q.full():
                    # for very short record
                    record_frames = list(self.record_frame_q.queue)
                    self.executor.submit(self.get_recognizer_result, record_frames)

                record_frame_dq: deque = self.record_frame_q.queue
                record_frame_dq.clear()

                assert self.tmp_frame_q.empty()
                assert self.record_frame_q.empty()

    def get_recognizer_result(self, record_frames: List[bytes]) -> None:

        record_wav_values = self.audio_preprocess(record_frames)
        record_wav_values =b"".join(record_frames)
        result = self.recognizer.recognize(record_wav_values, self.rate)
        #self.save_frames_to_wav(record_wav_values)
        #new_record_frames = [ f*2 for f in record_frames]
        #self.save_frames_to_wav(new_record_frames)
        if result is not None:
            print(result, end=" ", flush=True)
            msg = self.action_matcher.match(result)
            print(f"({msg})", flush=True)

    def save_frames_to_wav(self, frames: List[bytes]) -> None:
        num_files = len(glob("C:/UserD/Program/Project_Python/voice-presentation-control/voice_presentation_control/wave_files/*.wav"))
        wavefile = wave.open(f"C:/UserD/Program/Project_Python/voice-presentation-control/voice_presentation_control/wave_files/test_save_{num_files}.wav", "w")
        wavefile.setnchannels(1)
        wavefile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        wavefile.writeframes(frames)


    def volume_process(self,wave_values):
        def volume_process_func(wave_values):
            if wave_values<= min_threshold and wave_values>= -min_threshold :
                wave_values=0
            elif wave_values>min_threshold:
                wave_values = int((wave_values-min_threshold)/max_g*max_volume_value)
            elif wave_values < 0:
                wave_values = int((wave_values+min_threshold)/min_g*max_volume_value)
            return wave_values
        min_threshold=40
        max_volume_value=15000
        max_w=max(wave_values)
        min_w=min(wave_values)
        max_g = max_w-min_threshold
        min_g = abs(min_w)-min_threshold
        wave_values = map(volume_process_func,wave_values)
        wave_values=array('h',list(wave_values))
        return wave_values

    def denoise(self,wave_values):
        wave_values = np.array(array('h',wave_values))
        wave_values = logmmse.logmmse(data=wave_values, sampling_rate=self.rate,noise_threshold=0.2,window_size=67)
        wave_values=array('h',wave_values)
        return wave_values

    def freqs_process(self,wave_values):
        fft_wave=np.array(array('h',wave_values))
        sample_num = len(fft_wave)
        sample_rate = 44100
        audio_max = np.max(abs(fft_wave))
        times = np.arange(sample_num)/sample_rate
        vib_fft = np.fft.fft(fft_wave)
        fft_freqs =np.fft.fftfreq(sample_num,times[1]-times[0])
        vib_fft_pow = np.abs(vib_fft)
        # filter
        fft_filter = vib_fft.copy()
        noise_indices = np.where((abs(fft_freqs)>6000) & (abs(fft_freqs)<12000))
        fft_filter[noise_indices] = fft_filter[noise_indices]*0.4

        noise_indices = np.where(abs(fft_freqs)>=12000)
        fft_filter[noise_indices] = fft_filter[noise_indices]*0.05

        noise_indices = np.where((abs(fft_freqs)<=6000) & (abs(fft_freqs)>3000))
        fft_filter[noise_indices] = fft_filter[noise_indices]*0.8

        noise_indices = np.where((abs(fft_freqs)<=3000))
        fft_filter[noise_indices] = fft_filter[noise_indices]

        filter_wave_ifft = np.fft.ifft(fft_filter).real
        filter_wave = array('h',filter_wave_ifft.astype(int))

        return filter_wave

    def audio_preprocess(self,wave_values):
        wave_values = [np.array(array('h',i)) for i in wave_values]
        wave_values = np.concatenate(wave_values,axis=0)
        wave_values=self.denoise(wave_values)
        wave_values=self.freqs_process(wave_values)
        wave_values=self.volume_process(wave_values)
        return wave_values
