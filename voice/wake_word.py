"""
Слушает микрофон постоянно и ждёт фразу "Hey Jarvis" через openWakeWord.
Полностью бесплатно, работает локально, НЕ требует регистрации и ключей.
"""
import numpy as np
import pyaudio
from openwakeword.model import Model
import openwakeword

CHUNK = 1280  # openWakeWord ожидает блоки по 80мс при 16кГц
RATE = 16000


class WakeWordListener:
    def __init__(self, keyword="hey_jarvis"):
        # При первом запуске openWakeWord скачивает свои модели автоматически
        openwakeword.utils.download_models()
        self.model = Model(wakeword_models=[keyword])
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            rate=RATE,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=CHUNK,
        )

    def wait_for_wake_word(self, threshold=0.5):
        """Блокирует выполнение, пока не услышит 'Hey Jarvis'."""
        print("👂 Слушаю... скажи 'Hey Jarvis'")
        while True:
            audio_bytes = self.stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            predictions = self.model.predict(audio_data)
            for mdl_name, score in predictions.items():
                if score > threshold:
                    print(f"✅ Услышал '{mdl_name}' (score={score:.2f})!")
                    return True

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
