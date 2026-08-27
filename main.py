"""
Jarvis - точка входа.
Цикл: слушай wake word -> слушай команду -> разбери -> выполни -> ответь голосом -> повтори
"""
from voice.wake_word import WakeWordListener
from voice.listen import listen_command
from voice.speak import speak
from brain.intent_parser import handle_command


def main():
    speak("Джарвис на связи", rate=190)
    listener = WakeWordListener(keyword="jarvis")

    try:
        while True:
            listener.wait_for_wake_word()
            speak("Да?", rate=200)
            text = listen_command(language="ru-RU")
            response = handle_command(text)
            speak(response)
    except KeyboardInterrupt:
        print("\n👋 Останавливаю Jarvis")
    finally:
        listener.close()


if __name__ == "__main__":
    main()
