#!/bin/bash
# Stops the JARVIS backend and frontend processes started by start_jarvis.sh

JARVIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$JARVIS_DIR"

for pidfile in logs/backend.pid logs/frontend.pid; do
  if [ -f "$pidfile" ]; then
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid"
      echo "Stopped process $pid ($pidfile)"
    fi
    rm -f "$pidfile"
  fi
done
