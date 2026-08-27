"""
Записывает команду после wake word и превращает её в текст.
Использует Google Speech Recognition (бесплатно, нужен интернет).
"""
import speech_recognition as sr


def listen_command(language="ru-RU", timeout=5, phrase_time_limit=8):
    """
    Слушает и возвращает распознанный текст команды, либо None если не понял.
    language: "ru-RU" для русского, "en-US" для английского
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        print("🎙️ Говори...")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            print("⏱️ Тишина, не услышал команду")
            return None

    try:
        text = recognizer.recognize_google(audio, language=language)
        print(f"📝 Распознано: {text}")
        return text.lower()
    except sr.UnknownValueError:
        print("❓ Не смог разобрать речь")
        return None
    except sr.RequestError as e:
        print(f"⚠️ Ошибка сервиса распознавания: {e}")
        return None
