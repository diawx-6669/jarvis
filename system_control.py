"""
JARVIS System Control — volume, screen lock, display sleep, battery.

Native macOS control via AppleScript and pmset. No extra dependencies,
no OAuth, same pattern as the other *_access modules.

Deliberately limited to reversible, non-destructive operations: nothing
here can shut the machine down or lose the user's work.
"""

import asyncio
import logging
import re

from actions import applescript_escape

log = logging.getLogger("jarvis.system")

VOLUME_STEP = 12


async def _run(*args: str, timeout: float = 5.0) -> tuple[bool, str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode == 0, (stdout or stderr).decode().strip()
    except asyncio.TimeoutError:
        log.warning(f"{args[0]} timed out")
        return False, ""
    except Exception as e:
        log.warning(f"{args[0]} error: {e}")
        return False, ""


async def _osascript(script: str) -> tuple[bool, str]:
    return await _run("osascript", "-e", script)


# ── Volume ────────────────────────────────────────────────────────────


async def get_volume() -> int | None:
    """Current output volume, 0-100. None if it can't be read."""
    ok, out = await _osascript("output volume of (get volume settings)")
    if not ok:
        return None
    try:
        return int(out)
    except ValueError:
        # Returns "missing value" when output goes to a device AppleScript
        # can't introspect (some Bluetooth headsets, AirPlay).
        return None


async def is_muted() -> bool:
    ok, out = await _osascript("output muted of (get volume settings)")
    return ok and out.strip().lower() == "true"


async def set_volume(level: int) -> dict:
    """Set output volume to an absolute 0-100 level."""
    level = max(0, min(100, int(level)))
    ok, _ = await _osascript(f"set volume output volume {level}")
    if ok and level > 0:
        # Setting a level while muted leaves it silent — unmute so the
        # user actually hears the change they asked for.
        await _osascript("set volume without output muted")
    return {
        "success": ok,
        "level": level,
        "confirmation": f"Volume at {level} percent, sir." if ok else "I couldn't change the volume, sir.",
    }


async def adjust_volume(delta: int) -> dict:
    """Nudge the volume up or down by `delta` points."""
    current = await get_volume()
    if current is None:
        return {"success": False, "level": None, "confirmation": "I can't read the current volume, sir."}
    return await set_volume(current + delta)


async def set_muted(muted: bool) -> dict:
    state = "with" if muted else "without"
    ok, _ = await _osascript(f"set volume {state} output muted")
    if muted:
        confirmation = "Muted, sir." if ok else "I couldn't mute it, sir."
    else:
        confirmation = "Sound is back, sir." if ok else "I couldn't unmute it, sir."
    return {"success": ok, "muted": muted, "confirmation": confirmation}


# ── Screen ────────────────────────────────────────────────────────────


async def lock_screen() -> dict:
    """Lock the screen (Control-Command-Q), leaving everything running."""
    ok, _ = await _osascript(
        'tell application "System Events" to keystroke "q" using {command down, control down}'
    )
    return {
        "success": ok,
        "confirmation": "Locking up, sir." if ok else "I couldn't lock the screen, sir.",
    }


async def sleep_display() -> dict:
    """Put the display to sleep. The machine keeps running."""
    ok, _ = await _run("pmset", "displaysleepnow")
    return {
        "success": ok,
        "confirmation": "Display off, sir." if ok else "I couldn't put the display to sleep, sir.",
    }


# ── Battery ───────────────────────────────────────────────────────────


async def get_battery() -> dict | None:
    """Battery percentage, charging state and estimated time remaining.

    Returns None on a machine with no battery (Mac mini, Mac Studio).
    """
    ok, out = await _run("pmset", "-g", "batt")
    if not ok or "InternalBattery" not in out:
        return None

    # Line format: " -InternalBattery-0 (id=...)\t87%; discharging; 4:32 remaining"
    percent_match = re.search(r"(\d+)%", out)
    status_match = re.search(r"\d+%;\s*([a-z ]+)", out)
    time_match = re.search(r"(\d+:\d\d)\s+remaining", out)
    status = status_match.group(1).strip() if status_match else ""

    return {
        "percent": int(percent_match.group(1)) if percent_match else None,
        "charging": status == "charging",
        "charged": status in ("charged", "finishing charge"),
        "time_remaining": time_match.group(1) if time_match else None,
    }


async def battery_summary() -> str:
    """Voice-friendly one-liner about battery state."""
    batt = await get_battery()
    if not batt:
        return "This Mac runs on mains power, sir — no battery to report."

    percent = batt["percent"]
    if percent is None:
        return "I can't read the battery level, sir."

    if batt["charged"]:
        return f"Battery is full at {percent} percent, sir."

    if batt["charging"]:
        return f"Battery at {percent} percent and charging, sir."

    if batt["time_remaining"]:
        hours, _, minutes = batt["time_remaining"].partition(":")
        hours, minutes = int(hours), int(minutes)
        if hours:
            left = f"{hours} hour{'s' if hours != 1 else ''} and {minutes} minutes"
        else:
            left = f"{minutes} minutes"
        warning = " I'd plug in, sir." if percent <= 20 else ""
        return f"Battery at {percent} percent, about {left} remaining.{warning}"

    return f"Battery at {percent} percent, sir."


# ── Notifications ─────────────────────────────────────────────────────


async def notify(title: str, message: str) -> bool:
    """Post a macOS notification — used when JARVIS needs to be seen, not heard."""
    ok, _ = await _osascript(
        f'display notification "{applescript_escape(message)}" '
        f'with title "{applescript_escape(title)}"'
    )
    return ok
