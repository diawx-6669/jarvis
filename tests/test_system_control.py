"""Unit tests for system_control — battery parsing and volume clamping."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import system_control


DISCHARGING = (
    "Now drawing from 'Battery Power'\n"
    " -InternalBattery-0 (id=4653155)\t87%; discharging; 4:32 remaining present: true"
)
CHARGING = (
    "Now drawing from 'AC Power'\n"
    " -InternalBattery-0 (id=4653155)\t62%; charging; 1:12 remaining present: true"
)
CHARGED = (
    "Now drawing from 'AC Power'\n"
    " -InternalBattery-0 (id=4653155)\t100%; charged; 0:00 remaining present: true"
)
LOW = (
    "Now drawing from 'Battery Power'\n"
    " -InternalBattery-0 (id=4653155)\t12%; discharging; 0:23 remaining present: true"
)
DESKTOP = "Now drawing from 'AC Power'"


def _pmset(output: str, ok: bool = True):
    return patch.object(system_control, "_run", AsyncMock(return_value=(ok, output)))


@pytest.mark.asyncio
async def test_battery_discharging():
    with _pmset(DISCHARGING):
        batt = await system_control.get_battery()
    assert batt["percent"] == 87
    assert batt["charging"] is False
    assert batt["charged"] is False
    assert batt["time_remaining"] == "4:32"


@pytest.mark.asyncio
async def test_battery_charging():
    with _pmset(CHARGING):
        batt = await system_control.get_battery()
    assert batt["percent"] == 62
    assert batt["charging"] is True
    assert batt["charged"] is False


@pytest.mark.asyncio
async def test_battery_charged():
    with _pmset(CHARGED):
        batt = await system_control.get_battery()
    assert batt["charged"] is True
    assert batt["charging"] is False


@pytest.mark.asyncio
async def test_no_battery_on_a_desktop():
    with _pmset(DESKTOP):
        assert await system_control.get_battery() is None


@pytest.mark.asyncio
async def test_battery_summary_mentions_percentage_and_time():
    with _pmset(DISCHARGING):
        summary = await system_control.battery_summary()
    assert "87 percent" in summary
    assert "4 hours and 32 minutes" in summary


@pytest.mark.asyncio
async def test_battery_summary_warns_when_low():
    with _pmset(LOW):
        summary = await system_control.battery_summary()
    assert "12 percent" in summary
    assert "plug in" in summary


@pytest.mark.asyncio
async def test_battery_summary_on_a_desktop():
    with _pmset(DESKTOP):
        summary = await system_control.battery_summary()
    assert "mains power" in summary


# ── Volume ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("requested,expected", [
    (150, 100),
    (-20, 0),
    (55, 55),
])
async def test_set_volume_clamps_to_range(requested, expected):
    script = AsyncMock(return_value=(True, ""))
    with patch.object(system_control, "_osascript", script):
        result = await system_control.set_volume(requested)

    assert result["level"] == expected
    assert f"set volume output volume {expected}" in script.await_args_list[0].args[0]


@pytest.mark.asyncio
async def test_adjust_volume_is_relative_to_current():
    with patch.object(system_control, "get_volume", AsyncMock(return_value=40)), \
         patch.object(system_control, "_osascript", AsyncMock(return_value=(True, ""))):
        result = await system_control.adjust_volume(15)
    assert result["level"] == 55


@pytest.mark.asyncio
async def test_adjust_volume_fails_gracefully_when_level_is_unreadable():
    with patch.object(system_control, "get_volume", AsyncMock(return_value=None)):
        result = await system_control.adjust_volume(10)
    assert result["success"] is False


@pytest.mark.asyncio
async def test_get_volume_handles_missing_value():
    with patch.object(system_control, "_osascript", AsyncMock(return_value=(True, "missing value"))):
        assert await system_control.get_volume() is None
