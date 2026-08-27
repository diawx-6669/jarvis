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

# Виртуальное окружение Python
echo "🐍 Создаю виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Устанавливаю Python-зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

# Настройка .env
if [ ! -f config/.env ]; then
    cp config/.env.example config/.env
    echo ""
    echo "⚠️  ВАЖНО: нужен бесплатный ключ Picovoice для wake word 'Jarvis'"
    echo "   1. Зарегистрируйся: https://console.picovoice.ai"
    echo "   2. Скопируй Access Key"
    echo "   3. Вставь его в файл config/.env вместо PASTE_YOUR_KEY_HERE"
    echo ""
fi

echo "✅ Готово! Дальше:"
echo "   1. Отредактируй config/.env (см. выше)"
echo "   2. source venv/bin/activate"
echo "   3. python main.py"
echo ""
echo "⚠️  При первом запуске macOS спросит разрешение на доступ к микрофону -"
echo "   разреши в System Settings -> Privacy & Security -> Microphone"
