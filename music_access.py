"""
Music playback via Apple Music (Music.app), controlled through AppleScript —
same pattern as calendar_access.py / notes_access.py: no OAuth, no API keys,
just native macOS automation.

If the exact track/artist isn't found in the user's library, we fall back to
just pressing play on whatever's queued, and to searching Apple Music's
catalog (if the user has an active subscription) as a second attempt.
"""

import asyncio
import logging

log = logging.getLogger("jarvis.music")


async def _run_osascript(script: str) -> tuple[bool, str]:
    proc = await asyncio.create_subprocess_exec(
        "osascript", "-e", script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode == 0, (stdout or stderr).decode().strip()


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


async def play_song(query: str) -> dict:
    """Search the user's Music.app library for `query` (song and/or artist)
    and play the first match. Empty query just resumes/plays whatever is
    already loaded.
    """
    query = (query or "").strip()

    if not query:
        script = 'tell application "Music" to play'
        ok, _ = await _run_osascript(script)
        return {
            "success": ok,
            "confirmation": "Playing, sir." if ok else "Nothing queued to play, sir.",
        }

    escaped = _escape(query)
    script = f'''
    tell application "Music"
        activate
        set theTracks to (every track of library playlist 1 whose name contains "{escaped}" or artist contains "{escaped}")
        if (count of theTracks) > 0 then
            play (item 1 of theTracks)
            return "played:" & (name of item 1 of theTracks) & " - " & (artist of item 1 of theTracks)
        else
            return "notfound"
        end if
    end tell
    '''
    ok, result = await _run_osascript(script)

    if ok and result.startswith("played:"):
        info = result[len("played:"):]
        return {"success": True, "confirmation": f"Playing {info}, sir."}

    if ok and result == "notfound":
        log.info(f"'{query}' not found in local library, trying Apple Music search")
        return await _search_apple_music(query)

    log.error(f"play_song('{query}') failed: {result}")
    return {"success": False, "confirmation": f"I couldn't play {query}, sir."}


async def _search_apple_music(query: str) -> dict:
    """Fallback: use Apple Music's own search UI via System Events, for
    tracks not present in the local library (requires an active subscription).
    """
    escaped = _escape(query)
    script = f'''
    tell application "Music" to activate
    delay 0.3
    tell application "System Events"
        tell process "Music"
            keystroke "f" using {{command down}}
            delay 0.3
            keystroke "{escaped}"
            delay 0.6
            key code 36
        end tell
    end tell
    '''
    ok, result = await _run_osascript(script)
    return {
        "success": ok,
        "confirmation": f"Searching Apple Music for {query}, sir." if ok else f"I couldn't find {query}, sir.",
    }


async def pause_music() -> dict:
    ok, _ = await _run_osascript('tell application "Music" to pause')
    return {"success": ok, "confirmation": "Paused, sir." if ok else "Couldn't pause, sir."}


async def next_track() -> dict:
    ok, _ = await _run_osascript('tell application "Music" to next track')
    return {"success": ok, "confirmation": "Skipping, sir." if ok else "Couldn't skip, sir."}


async def stop_music() -> dict:
    ok, _ = await _run_osascript('tell application "Music" to stop')
    return {"success": ok, "confirmation": "Stopped, sir." if ok else "Couldn't stop, sir."}
