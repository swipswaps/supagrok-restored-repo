#!/usr/bin/env bash
# launch_all.sh — PRF‑GAZE‑FULL‑STACK‑LAUNCHER‑2025‑05‑01‑DAMPENED
# Purpose: One-shot launcher for all Supagrok Gaze Toolkit modules
# Status: ✅ PRF‑COMPLIANT (P01–P28)

set -euo pipefail
cd "$(dirname "$0")"

echo "🧼 [P03] Cleaning up previous WebSocket ports..."
for port in 9999 9998 9997 8000; do
  fuser -k "$port"/tcp 2>/dev/null || true
done

echo "🧠 [P04] Starting logger on :9999..."
python3 logger.py > logger.log 2>&1 &

echo "🖱 [P05] Starting dampened gaze-to-mouse override on :9998..."
python3 mouse_override.py > mouse.log 2>&1 &

echo "👁‍🗨 [P06] Starting dwell + blink activation on :9997..."
python3 dwell_blink_activation.py > dwell.log 2>&1 &

echo "✋ [P07] Starting ASL hand detector..."
python3 asl_detector_overlay.py > asl.log 2>&1 &

echo "📡 [P08] Launching HTTP server on :8000..."
python3 -m http.server 8000 > web.log 2>&1 &

echo "🌐 [P09] Launching browser to calibration page..."
firefox "http://localhost:8000/index.html" &

echo "✅ [P10] All modules running. Press Ctrl+C to terminate."
wait
