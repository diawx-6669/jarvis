"""
Jarvis - точка входа.
Голосовой цикл работает в фоновом потоке, окно интерфейса - в главном
(на macOS tkinter обязательно должен работать в главном потоке).
"""
import threading
from voice.wake_word import WakeWordListener
from voice.listen import listen_command
from voice.speak import speak
from brain.intent_parser import handle_command
from ui.gui import JarvisGUI


def voice_loop(gui: JarvisGUI):
    speak("Джарвис на связи")
    gui.set_text("Джарвис на связи. Жду 'Hey Jarvis'...")
    listener = WakeWordListener(keyword="hey_jarvis")

    try:
        while True:
            gui.set_state("idle")
            gui.set_text("Жду 'Hey Jarvis'...")
            listener.wait_for_wake_word()

            gui.set_state("listening")
            gui.set_text("Да? Слушаю...")
            speak("Да?")

            text = listen_command(language="ru")

            gui.set_state("thinking")
            gui.set_text(f"«{text}»" if text else "Не расслышал...")

            response = handle_command(text)

            gui.set_state("speaking")
            gui.set_text(response)
            speak(response)
    except KeyboardInterrupt:
        pass
    finally:
        listener.close()


def main():
    gui = JarvisGUI()

    # Голосовой цикл - в отдельном потоке, чтобы не блокировать окно
    t = threading.Thread(target=voice_loop, args=(gui,), daemon=True)
    t.start()

    gui.start()  # блокирует главный поток, рисует окно


if __name__ == "__main__":
    main()
