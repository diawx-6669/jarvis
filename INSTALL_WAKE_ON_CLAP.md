# JARVIS: wake on clap

1. Extract this update over the existing JARVIS folder.
2. Start it once with `bash scripts/start_jarvis.sh`.
3. In Chrome, open `http://localhost:5173`, click the page once, and allow
   **Microphone** access when macOS/Chrome asks. This permission is required
   for voice recognition and clap detection.
4. Install automatic launch once with `bash scripts/install_autostart.sh`.

JARVIS now starts in English without a language-selection screen. You can
still say “switch to Russian” or “переключись на русский” at any time.

One sharp clap wakes JARVIS. On wake it asks the macOS Music app to play
“Should I Stay Or Should I Go” by The Clash. The track itself is not included:
it must be in your Music library or playable through your Apple Music account.

If macOS asks whether JARVIS may control Music, approve it. If the clap does
not trigger reliably, select the intended microphone in Chrome’s site settings
for `localhost` and raise its input level in macOS Sound settings.
