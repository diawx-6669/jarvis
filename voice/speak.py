"""
Озвучивает текст через Microsoft Edge Neural TTS (бесплатно, без ключей,
без регистрации - официальный движок, который использует сам Edge).
Качество/интонации заметно выше системного macOS `say`.

Голоса на выбор (полный список: `edge-tts --list-voices`):
  ru-RU-DmitryNeural   - русский, мужской, глубокий   <- по умолчанию
  ru-RU-SvetlanaNeural - русский, женский
  en-GB-RyanNeural     - английский (UK), спокойный мужской, ближе всего
                         по духу к "ИИ-дворецкому" тембру, если захочешь
                         вести диалог по-английски
  en-GB-ThomasNeural   - английский (UK), более низкий/строгий мужской

Про "оригинальный голос Джарвиса из Тони Старка": клонировать голос
конкретного актёра/персонажа я не буду - это чужая узнаваемая голосовая
роль. Но PITCH пониже + спокойный размеренный темп дают похожий по духу
"невозмутимый ИИ-ассистент" характер. Если хочешь ещё ближе - можно
подключить платные ElevenLabs/Hume AI (у них голоса заметно "живее"),
скажи - подключу.
"""
import asyncio
import subprocess
import tempfile
import os
import edge_tts

VOICE = "ru-RU-DmitryNeural"
RATE = "+0%"      # "+15%" быстрее, "-10%" медленнее
PITCH = "-8Hz"     # ниже = голос глубже, более "механический"


def speak(text, voice=VOICE, rate=RATE, pitch=PITCH):
    print(f"🔊 Jarvis: {text}")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        out_path = f.name
    try:
        asyncio.run(_synthesize(text, voice, rate, pitch, out_path))
        subprocess.run(["afplay", out_path])
    finally:
        os.remove(out_path)


async def _synthesize(text, voice, rate, pitch, out_path):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(out_path)
