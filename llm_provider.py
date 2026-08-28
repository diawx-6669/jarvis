"""
Переходник Groq -> интерфейс Anthropic.

Весь остальной код проекта (server.py, screen.py, memory.py, planner.py)
написан под anthropic.AsyncAnthropic и везде вызывает:

    response = await client.messages.create(model=..., max_tokens=..., system=..., messages=...)
    text = response.content[0].text

Чтобы не переписывать это в каждом файле, этот класс прикидывается
anthropic.AsyncAnthropic, но внутри ходит в бесплатный Groq
(https://console.groq.com, OpenAI-совместимый API, ключ без карты).

Ограничение: Anthropic поддерживает картинки в messages (используется в
screen.py для анализа скриншота). Groq-модели из бесплатного текстового
тарифа их не понимают - в этом случае шим кидает исключение, а screen.py
уже сам ловит её и откатывается на текстовое описание открытых окон
(так и было задумано в оригинальном коде, ничего дополнительно чинить не нужно).
"""
import types
from groq import AsyncGroq


class _FakeTextBlock:
    def __init__(self, text: str):
        self.text = text


class _FakeUsage:
    def __init__(self, input_tokens: int, output_tokens: int):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _FakeAnthropicResponse:
    def __init__(self, groq_completion):
        text = groq_completion.choices[0].message.content or ""
        self.content = [_FakeTextBlock(text)]
        usage = getattr(groq_completion, "usage", None)
        self.usage = _FakeUsage(
            input_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            output_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
        )


class _MessagesAPI:
    def __init__(self, groq_client: AsyncGroq, model: str):
        self._client = groq_client
        self._model = model

    async def create(self, model=None, max_tokens=1024, system=None, messages=None, **kwargs):
        oai_messages = []
        if system:
            oai_messages.append({"role": "system", "content": system})

        for m in messages or []:
            content = m.get("content")
            if isinstance(content, list):
                # Anthropic-стиль content blocks (текст +/- картинка)
                if any(block.get("type") == "image" for block in content):
                    raise RuntimeError(
                        "Groq free tier здесь не понимает картинки - "
                        "вызывающий код должен откатиться на текстовый fallback"
                    )
                content = "\n".join(
                    block.get("text", "") for block in content if block.get("type") == "text"
                )
            oai_messages.append({"role": m["role"], "content": content})

        completion = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=oai_messages,
        )
        return _FakeAnthropicResponse(completion)


class GroqAnthropicShim:
    """Подставляется вместо anthropic.AsyncAnthropic везде в проекте."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self._client = AsyncGroq(api_key=api_key)
        self.messages = _MessagesAPI(self._client, model)
