"""
Слушает микрофон постоянно и ждёт слово "Jarvis" (встроенное ключевое слово Porcupine).
Как только услышал - возвращает управление вызывающему коду.
"""
import struct
import pvporcupine
import pyaudio
import os
from dotenv import load_dotenv

load_dotenv()

PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")


class WakeWordListener:
    def __init__(self, keyword="jarvis"):
        if not PICOVOICE_ACCESS_KEY:
            raise RuntimeError(
                "Нет PICOVOICE_ACCESS_KEY в config/.env. "
                "Зарегистрируйся бесплатно на https://console.picovoice.ai "
                "и вставь ключ в config/.env"
            )
        self.porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keywords=[keyword],
        )
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length,
        )

    def wait_for_wake_word(self):
        """Блокирует выполнение, пока не услышит 'Jarvis'."""
        print("👂 Слушаю... скажи 'Jarvis'")
        while True:
            pcm = self.stream.read(self.porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            result = self.porcupine.process(pcm)
            if result >= 0:
                print("✅ Услышал 'Jarvis'!")
                return True

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        self.porcupine.delete()
