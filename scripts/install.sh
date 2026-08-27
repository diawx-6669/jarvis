#!/bin/bash
set -e

echo "🤖 Установка Jarvis..."

# Проверка Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 Устанавливаю Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Системная зависимость для pyaudio
echo "📦 Устанавливаю portaudio (нужно для микрофона)..."
brew install portaudio

# tkinter нужен для графического интерфейса (окошко с кругом)
# Важно: версия должна соответствовать версии python3 в системе
PY_MINOR=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "📦 Устанавливаю python-tk@${PY_MINOR} (для окна интерфейса)..."
brew install "python-tk@${PY_MINOR}" || brew install python-tk || true

# Виртуальное окружение Python
echo "🐍 Создаю виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Устанавливаю Python-зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Готово! Дальше:"
echo "   1. source venv/bin/activate"
echo "   2. python main.py"
echo ""
echo "⚠️  При первом запуске:"
echo "   - macOS спросит разрешение на доступ к микрофону - разреши в"
echo "     System Settings -> Privacy & Security -> Microphone"
echo "   - openWakeWord автоматически скачает свои модели (~10 сек, один раз)"
echo ""
echo "🗣️  Скажи 'Hey Jarvis' чтобы активировать ассистента."
