#!/bin/bash
LABEL="com.jarvis.assistant"
PLIST_DEST="$HOME/Library/LaunchAgents/${LABEL}.plist"

launchctl unload "$PLIST_DEST" 2>/dev/null || true
rm -f "$PLIST_DEST"
echo "Autostart removed."
