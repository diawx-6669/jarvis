"""
Простой разбор намерений по ключевым словам (rule-based).
Это MVP: для более умного понимания можно позже подключить Claude API
(см. docs/upgrade_to_llm.md), но для старта правил достаточно и это
работает без интернет-задержек на LLM.
"""
import re
from commands import system_commands as cmd


def handle_command(text: str) -> str:
    """
    Принимает распознанный текст, возвращает текст ответа.
    Если ничего не подошло - просит повторить.
    """
    if not text:
        return "Я не расслышал, повтори пожалуйста"

    text = text.lower().strip()

    # --- приветствие ---
    if any(w in text for w in ["привет", "здравствуй", "hello", "hi"]):
        return "Привет! Чем могу помочь?"

    # --- открыть гугл ---
    if "открой гугл" in text or "открой google" in text or "open google" in text:
        return cmd.open_google()

    # --- поиск в гугле: "найди в гугле X" / "погугли X" ---
    m = re.search(r"(?:найди в гугле|погугли|найди|search google for)\s+(.+)", text)
    if m:
        return cmd.search_google(m.group(1))

    # --- открыть сайт: "открой сайт X" / "открой X.com" ---
    m = re.search(r"открой сайт\s+(.+)", text)
    if m:
        return cmd.open_website(m.group(1))

    # --- открыть приложение: "открой X" (после других правил, чтобы не конфликтовать) ---
    m = re.search(r"открой\s+(.+)", text)
    if m:
        app_map = {
            "сафари": "Safari", "safari": "Safari",
            "заметки": "Notes", "почту": "Mail", "почта": "Mail",
            "музыку": "Music", "музыка": "Music",
            "календарь": "Calendar", "терминал": "Terminal",
            "хром": "Google Chrome", "chrome": "Google Chrome",
        }
        app = app_map.get(m.group(1).strip(), m.group(1).strip().title())
        return cmd.open_app(app)

    # --- громкость ---
    m = re.search(r"(?:сделай )?громкост[ьи]\s*(\d+)", text)
    if m:
        return cmd.set_volume(m.group(1))
    if "какая громкость" in text or "текущая громкость" in text:
        return cmd.get_volume()

    # --- сон / блокировка ---
    if "спать" in text or "усни" in text:
        return cmd.sleep_mac()
    if "заблокируй" in text or "блокировка экрана" in text:
        return cmd.lock_screen()

    # --- ничего не подошло ---
    return "Я пока не умею это делать, но ты можешь научить меня в brain/intent_parser.py"
