#!/bin/bash
# Starts the JARVIS backend and frontend, then opens Chrome.
# Used both for manual runs and by the launchd autostart agent.

set -e

JARVIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$JARVIS_DIR"

mkdir -p logs

# Backend (FastAPI + WebSocket)
nohup python3 server.py --port 8340 --host 0.0.0.0 >> logs/backend.log 2>&1 &
echo $! > logs/backend.pid

# Frontend (Vite dev server)
cd "$JARVIS_DIR/frontend"
nohup npm run dev >> ../logs/frontend.log 2>&1 &
echo $! > ../logs/frontend.pid

# Give the dev server a moment to boot, then open Chrome
sleep 5
open -a "Google Chrome" "http://localhost:5173"
