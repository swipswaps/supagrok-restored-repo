#!/bin/bash
# PRF-D3PLOT-TEST-LAUNCHER
# Auto-healing launcher: logger + HTTP server + logs_index.tsv updater + browser

set -euo pipefail

D3_DIR="$(dirname "$(realpath "$0")")"
cd "$D3_DIR"

LOG_FILE="logs_index.tsv"
LOGGER_SCRIPT="supagrok_logger_daemon.py"
PLOT_FILE="plot_logs.html"
PORT=8000
LOCK_FILE="/tmp/supagrok_launcher.lock"

# 🧼 Kill old instances
if [ -f "$LOCK_FILE" ]; then
    OLD_PID=$(cat "$LOCK_FILE")
    if ps -p "$OLD_PID" > /dev/null; then
        echo "⚠️ Killing stale launcher PID $OLD_PID"
        kill -9 "$OLD_PID"
    fi
    rm -f "$LOCK_FILE"
fi
echo $$ > "$LOCK_FILE"

# Kill stale http.server
if lsof -i TCP:$PORT | grep LISTEN; then
    echo "🛑 Killing old HTTP server on port $PORT..."
    fuser -k ${PORT}/tcp || true
fi

# 🚀 Start HTTP server
echo "🌐 Starting HTTP server on port $PORT..."
nohup python3 -m http.server $PORT > /dev/null 2>&1 &

# 🧠 Start logger
if ! pgrep -f "$LOGGER_SCRIPT" > /dev/null; then
    echo "🧠 Launching Supagrok Logger Daemon..."
    nohup python3 "$LOGGER_SCRIPT" > /dev/null 2>&1 &
else
    echo "ℹ️ Logger already running."
fi

# 🧬 Update logs_index.tsv
echo "📈 Updating logs_index.tsv..."
python3 update_logs_index.py

# 🌍 Open chart
echo "🌍 Opening plot: http://localhost:$PORT/$PLOT_FILE"
xdg-open "http://localhost:$PORT/$PLOT_FILE"
