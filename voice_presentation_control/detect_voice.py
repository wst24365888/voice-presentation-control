# -*- coding: utf-8 -*-
import pyaudio
import wave
import numpy as np

def Monitor():
    CHUNK = 512
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 48000
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "cache.wav"
    while(True) :   
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
        print("开始缓存录音")
        frames = []
        while (True):
            print ('begin ')
            for i in range(0, 100):     #獲取一小段資料
                data = stream.read(CHUNK)
                frames.append(data)
            audio_data = np.fromstring(data, dtype=np.short)    #整合剛剛的一小段資料
            large_sample_count = np.sum( audio_data > 800 )
            temp = np.max(audio_data)       #找聲音最大值
            if temp > 800 :     #暫時設定聲音大小超過800代表有人說話
                print ("true")
                print ('当前阈值：',temp )
                # 真的錄製聲音
                for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK)
                    frames.append(data)
                break
            
            else :
                print("false")
                print ('当前阈值：',temp )
                frames = []     #清空資料
        stream.stop_stream()
        stream.close()
        p.terminate()
        #儲存成wav檔
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

if __name__ == '__main__':
    Monitor()