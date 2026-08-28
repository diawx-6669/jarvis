#!/bin/bash
# Installs JARVIS as a macOS LaunchAgent so it starts automatically every
# time you log in (open your laptop and unlock it).
#
# Run once:  bash scripts/install_autostart.sh
# Undo with: bash scripts/uninstall_autostart.sh

set -e

JARVIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.jarvis.assistant"
PLIST_DEST="$HOME/Library/LaunchAgents/${LABEL}.plist"

chmod +x "$JARVIS_DIR/scripts/start_jarvis.sh" "$JARVIS_DIR/scripts/stop_jarvis.sh"

mkdir -p "$HOME/Library/LaunchAgents"
sed "s#__JARVIS_DIR__#${JARVIS_DIR}#g" "$JARVIS_DIR/scripts/com.jarvis.assistant.plist.template" > "$PLIST_DEST"

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo "Installed. JARVIS will now start automatically every time you log in."
echo "Plist: $PLIST_DEST"
echo "To test right now:   launchctl start ${LABEL}"
echo "To remove:            bash scripts/uninstall_autostart.sh"
