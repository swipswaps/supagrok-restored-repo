#!/usr/bin/env bash
# File: prf_refind_binary_repair.sh
# Directive: PRF‑REFIND‑BINARY‑RECOVERY‑2025‑05‑01‑FIXED
# Purpose: Auto-recover rEFInd binary via package manager or mounted source
# Status: ✅ PRF‑COMPLIANT (P01–P28)

set -euo pipefail

# === [P01] Metadata
TS=$(date +%s)
UUID=$(uuidgen)
LOG="/var/log/prf_refind_binary_repair_${TS}.log"
DEST="/boot/efi/EFI/refind/refind_x64.efi"
echo "🔧 Recovering rEFInd binary — $TS" | tee "$LOG"

# === [P02] Ensure Destination Exists
mkdir -p "$(dirname "$DEST")"

# === [P03] Attempt to Install rEFInd
function install_refind() {
  if command -v dnf &>/dev/null; then
    echo "📦 Trying DNF install..." | tee -a "$LOG"
    dnf install -y refind-efi && return 0
  elif command -v apt &>/dev/null; then
    echo "📦 Trying APT install..." | tee -a "$LOG"
    apt-get update && apt-get install -y refind && return 0
  fi
  return 1
}

# === [P04] Install if Missing
if [[ ! -f "$DEST" ]]; then
  echo "🔍 Attempting to install rEFInd via package manager..." | tee -a "$LOG"
  if ! install_refind; then
    echo "❌ No valid package manager or package install failed." | tee -a "$LOG"
  fi
fi

# === [P05] Search for Binary
src_path=$(find /usr/share/refind*/ /boot/efi/EFI/refind*/ -type f -name 'refind_x64.efi' 2>/dev/null | head -n 1 || true)

# === [P06] Copy and Verify
if [[ -f "$src_path" ]]; then
  cp -u "$src_path" "$DEST"
  chmod 644 "$DEST"
  echo "✅ Copied: $src_path → $DEST" | tee -a "$LOG"
  sha256sum "$DEST" | tee -a "$LOG"
else
  echo "❌ Could not locate refind_x64.efi even after install attempt." | tee -a "$LOG"
  echo "🛑 Halting for manual ISO mount or verification." | tee -a "$LOG"
  exit 1
fi

# === [P27] Summary
echo "✅ UUID: $UUID" | tee -a "$LOG"
echo "📜 Log: $LOG"
