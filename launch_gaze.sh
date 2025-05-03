#!/usr/bin/env bash
# launch_gaze.sh — PRF‑BROWSER‑LAUNCHER‑2025‑04‑30

set -euo pipefail
PORT=8000
LOG=gaze_browser.log
URL="http://localhost:$PORT/index.html"

function firefox_launch() {
  firefox --no-remote --private-window "$URL" &
}

function chromium_launch() {
  chromium --disable-background-timer-throttling --disable-gpu --no-first-run "$URL" &
}

if ! lsof -i :$PORT &>/dev/null; then
  python3 -m http.server "$PORT" &
  sleep 1
fi

command -v firefox &>/dev/null && firefox_launch || chromium_launch
