"""
JARVIS Timers — spoken countdowns ("set a timer for ten minutes").

Timers live in memory as asyncio tasks: a restart clears them, which is
the right tradeoff for something that rarely outlives a conversation.
When one fires it calls back into the server so JARVIS says it out loud.
"""

import asyncio
import itertools
import logging
import re
import time
from dataclasses import dataclass
from typing import Awaitable, Callable

log = logging.getLogger("jarvis.timers")

MAX_DURATION = 12 * 3600

_UNIT_SECONDS = {
    "second": 1, "seconds": 1, "sec": 1, "secs": 1,
    "секунда": 1, "секунды": 1, "секунду": 1, "секунд": 1,
    "minute": 60, "minutes": 60, "min": 60, "mins": 60,
    "минута": 60, "минуты": 60, "минуту": 60, "минут": 60,
    "hour": 3600, "hours": 3600, "hr": 3600, "hrs": 3600,
    "час": 3600, "часа": 3600, "часов": 3600,
}

_WORD_NUMBERS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "fifteen": 15,
    "twenty": 20, "thirty": 30, "forty": 40, "forty-five": 45, "fifty": 50,
    "sixty": 60, "ninety": 90,
    "один": 1, "одну": 1, "два": 2, "две": 2, "три": 3, "четыре": 4,
    "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9,
    "десять": 10, "пятнадцать": 15, "двадцать": 20, "тридцать": 30,
    "сорок": 40, "пятьдесят": 50, "шестьдесят": 60, "полтора": 1,
}

_counter = itertools.count(1)


@dataclass
class Timer:
    id: int
    label: str
    seconds: int
    fires_at: float
    task: asyncio.Task | None = None

    @property
    def remaining(self) -> int:
        return max(0, int(round(self.fires_at - time.time())))


_active: dict[int, Timer] = {}


def parse_duration(text: str) -> int | None:
    """Parse a spoken duration into seconds. None if there isn't one.

    Handles "10 minutes", "an hour and a half", "1 hour 30", "5 минут".
    """
    t = text.lower().strip()
    total = 0

    # "half an hour" / "полчаса" have no number attached to the unit
    if "half an hour" in t or "полчаса" in t:
        total += 1800
        t = t.replace("half an hour", "").replace("полчаса", "")
    if "and a half" in t or "с половиной" in t:
        # Applies to whatever unit follows; hours is the only sane reading.
        if "hour" in t or "час" in t:
            total += 1800
        elif "minute" in t or "минут" in t:
            total += 30

    # Scan token by token: a unit word takes its amount from the token before
    # it. Pairing with a regex instead would consume tokens in the wrong pairs
    # ("на полтора часа" would pair "на"+"полтора" and lose the hours).
    tokens = re.findall(r"[\wа-яё\-]+", t)
    for i, token in enumerate(tokens):
        unit = _UNIT_SECONDS.get(token)
        if unit is None or i == 0:
            continue
        previous = tokens[i - 1]
        if previous.isdigit():
            amount = int(previous)
        else:
            amount = _WORD_NUMBERS.get(previous)
            if amount is None:
                continue
            # "полтора часа" = one and a half hours
            if previous in ("полтора", "полторы"):
                total += unit // 2
        total += amount * unit

    if total <= 0:
        return None
    return min(total, MAX_DURATION)


_UNIT_WORDS = r"(?:seconds?|secs?|minutes?|mins?|hours?|hrs?|секунд\w*|минут\w*|час\w*)"

_LABEL_PATTERNS = [
    # "...for 10 minutes for the pasta" / "...на 10 минут на пасту"
    rf"{_UNIT_WORDS}\s+(?:for|to|на|для)\s+(?:the\s+)?(.+)$",
    # "set a pasta timer" / "поставь таймер на пасту" (no duration in between)
    r"^(?:set|start)\s+(?:a|an)?\s*(.+?)\s+timer\b",
]


_LABEL_STOPWORDS = {"a", "an", "the", "my", "me", "it", "this", "that",
                    "на", "мне", "это", "таймер"}


def parse_label(text: str) -> str:
    """Pull a label ("pasta") out of a spoken timer request. '' if there isn't one."""
    t = text.lower().strip()
    for pattern in _LABEL_PATTERNS:
        match = re.search(pattern, t)
        if not match:
            continue
        label = match.group(1).strip(" .,!?")
        # A trailing duration ("for 5 minutes") is not a label.
        if re.fullmatch(rf"[\d\s]*{_UNIT_WORDS}[\s\d]*", label):
            continue
        words = [w for w in label.split() if w not in _LABEL_STOPWORDS]
        if 1 <= len(words) <= 4:
            return " ".join(words)
    return ""


def format_duration(seconds: int) -> str:
    """Voice-friendly duration: 90 -> 'a minute and 30 seconds'."""
    if seconds < 60:
        return "1 second" if seconds == 1 else f"{seconds} seconds"

    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        head = "a minute" if minutes == 1 else f"{minutes} minutes"
        return f"{head} and {secs} seconds" if secs else head

    hours, minutes = divmod(minutes, 60)
    head = "an hour" if hours == 1 else f"{hours} hours"
    return f"{head} and {minutes} minutes" if minutes else head


async def start_timer(
    seconds: int,
    label: str,
    on_fire: Callable[[Timer], Awaitable[None]],
) -> Timer:
    """Start a countdown. `on_fire` is awaited when it elapses."""
    seconds = max(1, min(int(seconds), MAX_DURATION))
    timer_id = next(_counter)
    timer = Timer(
        id=timer_id,
        label=label.strip(),
        seconds=seconds,
        fires_at=time.time() + seconds,
    )

    async def _run():
        try:
            await asyncio.sleep(seconds)
        except asyncio.CancelledError:
            return
        _active.pop(timer_id, None)
        try:
            await on_fire(timer)
        except Exception as e:
            log.error(f"Timer {timer_id} callback failed: {e}")

    timer.task = asyncio.create_task(_run())
    _active[timer_id] = timer
    log.info(f"Timer {timer_id} set for {seconds}s ({label or 'no label'})")
    return timer


def list_timers() -> list[Timer]:
    return sorted(_active.values(), key=lambda t: t.fires_at)


def cancel_timer(timer_id: int | None = None) -> Timer | None:
    """Cancel one timer, or the soonest one when no id is given."""
    if timer_id is None:
        timers = list_timers()
        if not timers:
            return None
        timer = timers[0]
    else:
        timer = _active.get(timer_id)
        if timer is None:
            return None

    timer.task.cancel()
    _active.pop(timer.id, None)
    log.info(f"Timer {timer.id} cancelled")
    return timer


def cancel_all() -> int:
    count = len(_active)
    for timer in list(_active.values()):
        timer.task.cancel()
    _active.clear()
    return count


def summarize_timers() -> str:
    """Voice-friendly summary of what's currently running."""
    timers = list_timers()
    if not timers:
        return "No timers running, sir."

    if len(timers) == 1:
        timer = timers[0]
        label = f" for {timer.label}" if timer.label else ""
        return f"One timer{label}, {format_duration(timer.remaining)} left, sir."

    parts = []
    for timer in timers[:3]:
        label = f"{timer.label}: " if timer.label else ""
        parts.append(f"{label}{format_duration(timer.remaining)}")
    return f"{len(timers)} timers running, sir. " + ". ".join(parts) + "."
