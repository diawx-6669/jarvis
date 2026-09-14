"""Unit tests for the timer module — duration/label parsing and lifecycle."""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import timers


@pytest.fixture(autouse=True)
def clear_timers():
    timers.cancel_all()
    yield
    timers.cancel_all()


# ── Duration parsing ──────────────────────────────────────────────────


@pytest.mark.parametrize("text,expected", [
    ("set a timer for 10 minutes", 600),
    ("set a timer for 5 min", 300),
    ("timer for an hour", 3600),
    ("set a timer for two hours", 7200),
    ("set a timer for 30 seconds", 30),
    ("set a timer for 90 minutes", 5400),
])
def test_parse_duration_english(text, expected):
    assert timers.parse_duration(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("поставь таймер на 15 минут", 900),
    ("засеки 30 секунд", 30),
    ("засеки 3 часа", 10800),
])
def test_parse_duration_russian(text, expected):
    assert timers.parse_duration(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("set a timer for half an hour", 1800),
    ("set a timer for an hour and a half", 5400),
    ("поставь таймер на полтора часа", 5400),
])
def test_parse_duration_fractions(text, expected):
    assert timers.parse_duration(text) == expected


@pytest.mark.parametrize("text", [
    "set a timer for pasta",
    "what is the weather",
    "",
])
def test_parse_duration_returns_none_without_a_duration(text):
    assert timers.parse_duration(text) is None


def test_parse_duration_is_capped():
    assert timers.parse_duration("set a timer for 40 hours") == timers.MAX_DURATION


# ── Label parsing ─────────────────────────────────────────────────────


@pytest.mark.parametrize("text,expected", [
    ("set a timer for 10 minutes for the pasta", "pasta"),
    ("set a pasta timer", "pasta"),
    ("поставь таймер на 20 минут на курицу", "курицу"),
    ("set a timer for 10 minutes", ""),
    ("set a timer for an hour", ""),
])
def test_parse_label(text, expected):
    assert timers.parse_label(text) == expected


# ── Formatting ────────────────────────────────────────────────────────


@pytest.mark.parametrize("seconds,expected", [
    (1, "1 second"),
    (30, "30 seconds"),
    (60, "a minute"),
    (90, "a minute and 30 seconds"),
    (600, "10 minutes"),
    (3600, "an hour"),
    (5400, "an hour and 30 minutes"),
    (7200, "2 hours"),
])
def test_format_duration(seconds, expected):
    assert timers.format_duration(seconds) == expected


# ── Lifecycle ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_timer_fires_and_deregisters():
    fired = []

    async def on_fire(timer):
        fired.append(timer.label)

    await timers.start_timer(1, "pasta", on_fire)
    assert len(timers.list_timers()) == 1

    await asyncio.sleep(1.3)
    assert fired == ["pasta"]
    assert timers.list_timers() == []


@pytest.mark.asyncio
async def test_cancelled_timer_never_fires():
    fired = []

    async def on_fire(timer):
        fired.append(timer.label)

    timer = await timers.start_timer(1, "eggs", on_fire)
    assert timers.cancel_timer(timer.id) is timer

    await asyncio.sleep(1.3)
    assert fired == []
    assert timers.list_timers() == []


@pytest.mark.asyncio
async def test_cancel_without_id_cancels_the_soonest():
    async def on_fire(timer):
        pass

    await timers.start_timer(300, "later", on_fire)
    soonest = await timers.start_timer(60, "sooner", on_fire)

    assert timers.cancel_timer() is soonest
    assert [t.label for t in timers.list_timers()] == ["later"]


@pytest.mark.asyncio
async def test_cancel_returns_none_when_nothing_is_running():
    assert timers.cancel_timer() is None


@pytest.mark.asyncio
async def test_summarize_timers():
    async def on_fire(timer):
        pass

    assert timers.summarize_timers() == "No timers running, sir."

    await timers.start_timer(600, "pasta", on_fire)
    summary = timers.summarize_timers()
    assert "pasta" in summary
    assert "One timer" in summary
