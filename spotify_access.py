"""
Music playback via Spotify (desktop app), used specifically for the
"wake song" that plays when JARVIS starts up or hears a clap.

Unlike Music.app, Spotify's AppleScript dictionary has no "search my
library and play the first match" verb — it can only play a track it
already has a URI for. So instead of scripting, we:
  1. open the Spotify app straight to a search-results page for the
     query via the `spotify:search:<query>` URI, then
  2. use System Events to move focus onto the first result and press it.

This is the same tradeoff as the Apple Music search fallback in
music_access.py: it drives the real UI instead of a clean API, so it
depends on Spotify's window being frontmost and its layout not changing.
It requires Spotify.app installed and "Accessibility" permission granted
to the process running osascript (System Settings > Privacy & Security >
Accessibility). For a rock-solid version, using the Spotify Web API with
your own OAuth app would remove the UI-automation fragility entirely —
happy to build that instead if this proves flaky on your machine.
"""

import asyncio
import logging
import urllib.parse

log = logging.getLogger("jarvis.spotify")


async def _run(*args: str) -> tuple[bool, str]:
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode == 0, (stdout or stderr).decode().strip()


async def _run_osascript(script: str) -> tuple[bool, str]:
    return await _run("osascript", "-e", script)


async def play_song_spotify(query: str) -> dict:
    """Open Spotify to a search for `query` and attempt to start playback
    of the first result. Empty query just resumes whatever's loaded.
    """
    query = (query or "").strip()

    if not query:
        ok, _ = await _run_osascript('tell application "Spotify" to play')
        return {"success": ok, "confirmation": "Playing, sir." if ok else "Nothing queued, sir."}

    uri = "spotify:search:" + urllib.parse.quote(query)
    ok, err = await _run("open", "-a", "Spotify", uri)
    if not ok:
        log.error(f"failed to open Spotify for '{query}': {err}")
        return {"success": False, "confirmation": f"I couldn't open Spotify for {query}, sir."}

    await asyncio.sleep(1.8)  # give the search results time to render

    script = '''
    tell application "Spotify" to activate
    delay 0.3
    tell application "System Events"
        tell process "Spotify"
            key code 48 -- Tab, move focus into the results list
            delay 0.2
            key code 125 -- Down, land on the first result row
            delay 0.2
            key code 36 -- Return, play the focused row
        end tell
    end tell
    '''
    ok2, result = await _run_osascript(script)
    if ok2:
        return {"success": True, "confirmation": f"Playing {query} on Spotify, sir."}

    log.error(f"play_song_spotify UI automation for '{query}' failed: {result}")
    return {
        "success": False,
        "confirmation": f"Opened Spotify but couldn't start {query} automatically, sir.",
    }


async def pause_music_spotify() -> dict:
    ok, _ = await _run_osascript('tell application "Spotify" to pause')
    return {"success": ok, "confirmation": "Paused, sir." if ok else "Couldn't pause, sir."}
