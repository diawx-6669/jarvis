"""
Функции, которые реально что-то делают на Mac.
Каждая функция возвращает текст, который Jarvis скажет в ответ.
"""
import subprocess
import webbrowser
import urllib.parse


def open_website(url):
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Открываю {url}"


def open_google():
    webbrowser.open("https://www.google.com")
    return "Открываю Google"


def search_google(query):
    q = urllib.parse.quote(query)
    webbrowser.open(f"https://www.google.com/search?q={q}")
    return f"Ищу в Google: {query}"


def open_app(app_name):
    """Открывает приложение macOS по имени, например 'Safari', 'Notes', 'Music'."""
    try:
        subprocess.run(["open", "-a", app_name], check=True)
        return f"Открываю {app_name}"
    except subprocess.CalledProcessError:
        return f"Не нашёл приложение {app_name}"


def set_volume(level):
    """level: 0-100"""
    level = max(0, min(100, int(level)))
    subprocess.run(["osascript", "-e", f"set volume output volume {level}"])
    return f"Громкость {level} процентов"


def get_volume():
    result = subprocess.run(
        ["osascript", "-e", "output volume of (get volume settings)"],
        capture_output=True, text=True
    )
    vol = result.stdout.strip()
    return f"Текущая громкость {vol} процентов"


def sleep_mac():
    subprocess.run(["osascript", "-e", 'tell application "System Events" to sleep'])
    return "Ухожу в сон"


def lock_screen():
    subprocess.run(["osascript", "-e",
                     'tell application "System Events" to keystroke "q" using {control down, command down}'])
    return "Блокирую экран"
