#!/bin/bash
# Starts the JARVIS backend and frontend, then opens Chrome.
# Used both for manual runs and by the launchd autostart agent.

set -e

JARVIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$JARVIS_DIR"

mkdir -p logs

# Backend (FastAPI + WebSocket). Avoid a second copy when launchd retries.
if ! lsof -nP -iTCP:8340 -sTCP:LISTEN >/dev/null 2>&1; then
  nohup python3 server.py --port 8340 --host 0.0.0.0 >> logs/backend.log 2>&1 &
  echo $! > logs/backend.pid
fi

# Frontend (Vite dev server). Replace an unrelated/stale process that would
# otherwise make Chrome show a 404 page on JARVIS's port.
if lsof -nP -iTCP:5173 -sTCP:LISTEN >/dev/null 2>&1 && ! curl -fsS http://localhost:5173/ 2>/dev/null | grep -q 'orb-canvas'; then
  lsof -tiTCP:5173 -sTCP:LISTEN | xargs kill
  sleep 1
fi
if ! lsof -nP -iTCP:5173 -sTCP:LISTEN >/dev/null 2>&1; then
  cd "$JARVIS_DIR/frontend"
  nohup npm run dev >> ../logs/frontend.log 2>&1 &
  echo $! > ../logs/frontend.pid
fi

# Give the dev server a moment to boot, then open Chrome
sleep 5
open -a "Google Chrome" "http://localhost:5173"
