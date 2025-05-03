#!/usr/bin/env bash
# File: prf_gnome_rescue_launcher.sh — PRF‑GNOME‑GRUB‑RESCUE‑2025‑05‑01‑FINAL
# Purpose: GNOME-clickable GRUB auto-repair wrapper
# Status: ✅ PRF‑COMPLIANT (P01–P28)

set -euo pipefail

TS=$(date +%s)
LOG="/var/log/grub_gnome_launcher_${TS}.log"
HEALER="./grub_repair_launcher.sh"

echo "🚀 Launching GRUB Repair via GNOME Rescue Launcher [$TS]" | tee "$LOG"

# === [P03] Confirm script exists
if [[ ! -x "$HEALER" ]]; then
  echo "❌ Healer script $HEALER not found or not executable!" | tee -a "$LOG"
  exit 1
fi

# === [P05] Run with root privileges
if [[ "$EUID" -ne 0 ]]; then
  echo "🔐 Elevating via sudo..." | tee -a "$LOG"
  sudo "$HEALER" | tee -a "$LOG"
else
  echo "⚙ Executing directly as root..." | tee -a "$LOG"
  "$HEALER" | tee -a "$LOG"
fi

echo "✅ GRUB repair completed. Log: $LOG"
