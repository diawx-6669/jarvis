"""
Озвучивает текст через встроенную в macOS команду `say`.
Голоса можно посмотреть командой в терминале: say -v '?'
Для русского хорошо подходит голос "Milena" или "Yuri".
"""
import subprocess


def speak(text, voice="Yuri", rate=185):
    """
    text: что сказать
    voice: имя голоса macOS (Milena/Yuri - русские голоса, Samantha - английский)
    rate: скорость речи (слов в минуту)
    """
    print(f"🔊 Jarvis: {text}")
    subprocess.run(["say", "-v", voice, "-r", str(rate), text])
