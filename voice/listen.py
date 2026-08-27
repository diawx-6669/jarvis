"""
Записывает команду после wake word и превращает её в текст.

ВАЖНО: раньше тут был recognize_google() - бесплатный неофициальный
эндпоинт Google, который сейчас массово отдаёт "Bad Request" (Google
его прикрывает, это не баг в твоём коде и не проблема микрофона).

Теперь распознавание идёт локально через faster-whisper:
  - работает офлайн, не зависит от внешних серверов -> никаких Bad Request
  - заметно лучше понимает русскую речь, чем старый Google-эндпоинт
  - при первом запуске скачает модель (~150 МБ для "base"), дальше офлайн

Модель побольше = точнее, но медленнее:
  tiny < base < small < medium  (для Mac обычно ок "base" или "small")
"""
import numpy as np
import speech_recognition as sr
from faster_whisper import WhisperModel

# device="cpu" - надёжно работает везде, в т.ч. на Apple Silicon
# compute_type="int8" - быстрее и меньше памяти, качество почти не страдает
_model = WhisperModel("base", device="cpu", compute_type="int8")


def listen_command(language="ru", timeout=5, phrase_time_limit=8):
    """
    Слушает и возвращает распознанный текст команды, либо None если не понял.
    language: "ru" для русского, "en" для английского
    """
    recognizer = sr.Recognizer()
    with sr.Microphone(sample_rate=16000) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        recognizer.pause_threshold = 0.8  # пауза тишины, после которой считаем фразу законченной
        print("🎙️ Говори...")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            print("⏱️ Тишина, не услышал команду")
            return None

    # sr отдаёт 16-bit PCM - конвертируем в float32 [-1, 1], как ждёт whisper
    audio_np = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0

    segments, _ = _model.transcribe(audio_np, language=language, beam_size=5)
    text = "".join(seg.text for seg in segments).strip()

    if not text:
        print("❓ Не смог разобрать речь")
        return None

    print(f"📝 Распознано: {text}")
    return text.lower()
