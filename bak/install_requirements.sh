#!/usr/bin/env bash
# install_requirements.sh — PRF‑AUTO‑INSTALL‑GAZE‑TOOLKIT‑2025‑05‑01
# Purpose: Ensure all dependencies for Supagrok Gaze Toolkit are installed.
# PRF Status: ✅ PRF‑COMPLIANT (P01–P28)

set -euo pipefail

echo "🔍 [P01] Checking for Python 3..."
command -v python3 >/dev/null || { echo "❌ Python 3 not found"; exit 1; }

echo "📦 [P02] Ensuring pip is installed..."
python3 -m ensurepip --upgrade || sudo apt-get install -y python3-pip

REQUIRED_PY_MODULES=(websockets pyautogui pynput opencv-python numpy)

echo "🔧 [P03–P05] Installing required Python packages via pip..."
for pkg in "${REQUIRED_PY_MODULES[@]}"; do
    echo "▶ Checking $pkg..."
    if ! python3 -c "import $pkg" &>/dev/null; then
        echo "⚙ Attempting pip install: $pkg"
        pip3 install --user "$pkg" || {
            echo "⚠ pip install failed for $pkg — trying apt fallback..."
            sudo apt-get update && sudo apt-get install -y "python3-${pkg}" || {
                echo "❌ Failed to install $pkg with both pip and apt"; exit 1;
            }
        }
    else
        echo "✅ $pkg already installed"
    fi
done

echo "🔐 [P28] Ensuring all .sh scripts are executable..."
for f in *.sh; do
  if [ -f "$f" ]; then
    chmod +x "$f"
    echo "   🔓 +x set for: $f"
  fi
done

echo "🟢 [✓] All dependencies and permissions are in place."
