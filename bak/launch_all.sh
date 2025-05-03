#!/usr/bin/env bash
# launch_all.sh — PRF‑GAZE‑FULL‑STACK‑LAUNCHER‑2025‑05‑01

set -euo pipefail
cd "$(dirname "$0")"

echo "🧼 Cleaning up previous ports..."
fuser -k 9999/tcp 2>/dev/null || true
fuser -k 9998/tcp 2>/dev/null || true
fuser -k 9997/tcp 2>/dev/null || true
fuser -k 8000/tcp 2>/dev/null || true

echo "🧠 Starting logger..."
python3 logger.py > logger.log 2>&1 &

echo "🖱 Starting gaze-to-mouse..."
python3 mouse_override.py > mouse.log 2>&1 &

echo "👁‍🗨 Starting dwell + blink..."
python3 dwell_blink_activation.py > dwell.log 2>&1 &

echo "✋ Starting ASL overlay..."
python3 asl_detector_overlay.py > asl.log 2>&1 &

echo "📡 Starting HTTP server..."
python3 -m http.server 8000 > web.log 2>&1 &

echo "🌐 Opening browser..."
firefox "http://localhost:8000/index.html" &

echo "✅ All services running."
wait
