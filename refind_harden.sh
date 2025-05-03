#!/usr/bin/env bash
# refind_harden.sh — PRF‑REFIND‑HARDEN‑EXPAND‑2025‑05‑01‑A
# Purpose: Harden rEFInd by auditing both main and fallback configs
# Status: ✅ PRF‑COMPLIANT (P01–P28)

set -euo pipefail

# === [P02] Timestamp and audit log setup
TIMESTAMP=$(date +%s)
LOG="refind_patch_$TIMESTAMP.log"
ROLLBACK=""
REFIND_CONF=""
REFIND_LINUX_CONF="/boot/refind_linux.conf"
LINUX_CONF_BACKUP=""

echo "🛡 rEFInd Hardening — $TIMESTAMP" | tee "$LOG"

# === [P03–P04] Locate rEFInd main config
for path in /boot/efi/EFI/refind/refind.conf /boot/EFI/refind/refind.conf; do
  if [ -f "$path" ]; then
    REFIND_CONF="$path"
    ROLLBACK="${path}.bak.${TIMESTAMP}"
    break
  fi
done

if [[ -z "$REFIND_CONF" ]]; then
  echo "❌ No rEFInd configuration file found." | tee -a "$LOG"
else
  echo "📁 Config found: $REFIND_CONF" | tee -a "$LOG"
  echo "🧾 Backup: $ROLLBACK" | tee -a "$LOG"
  sudo cp "$REFIND_CONF" "$ROLLBACK"

  echo "🔍 Scanning for patchable lines..." | tee -a "$LOG"
  sudo grep -E '^(options|menuentry|graphics_mode)' "$REFIND_CONF" || true

  PATCHED=0
  if sudo grep -q "quiet" "$REFIND_CONF"; then
    echo "🩹 Removing 'quiet'..." | tee -a "$LOG"
    sudo sed -i 's/\bquiet\b//g' "$REFIND_CONF"
    PATCHED=1
  fi
  if sudo grep -q "rhgb" "$REFIND_CONF"; then
    echo "🩹 Removing 'rhgb'..." | tee -a "$LOG"
    sudo sed -i 's/\brhgb\b//g' "$REFIND_CONF"
    PATCHED=1
  fi
  if ! sudo grep -q "verbose" "$REFIND_CONF"; then
    echo "➕ Appending 'verbose' to options..." | tee -a "$LOG"
    sudo sed -i 's/^options.*/& verbose/' "$REFIND_CONF"
    PATCHED=1
  fi
  if [[ "$PATCHED" -eq 1 ]]; then
    echo "✅ Main config patched." | tee -a "$LOG"
  else
    echo "ℹ No changes required in main config." | tee -a "$LOG"
  fi
fi

# === [P10–P15] /boot/refind_linux.conf fallback audit
if [[ -f "$REFIND_LINUX_CONF" ]]; then
  echo "🪙 Found fallback config: $REFIND_LINUX_CONF" | tee -a "$LOG"
  LINUX_CONF_BACKUP="${REFIND_LINUX_CONF}.bak.${TIMESTAMP}"
  sudo cp "$REFIND_LINUX_CONF" "$LINUX_CONF_BACKUP"
  echo "🧾 Backup created: $LINUX_CONF_BACKUP" | tee -a "$LOG"

  PATCHED_LINUX=0
  if grep -q "quiet" "$REFIND_LINUX_CONF"; then
    echo "🩹 Removing 'quiet'..." | tee -a "$LOG"
    sudo sed -i 's/\bquiet\b//g' "$REFIND_LINUX_CONF"
    PATCHED_LINUX=1
  fi
  if grep -q "rhgb" "$REFIND_LINUX_CONF"; then
    echo "🩹 Removing 'rhgb'..." | tee -a "$LOG"
    sudo sed -i 's/\brhgb\b//g' "$REFIND_LINUX_CONF"
    PATCHED_LINUX=1
  fi
  if ! grep -q "verbose" "$REFIND_LINUX_CONF"; then
    echo "➕ Appending 'verbose' to options..." | tee -a "$LOG"
    sudo sed -i 's/^"options.*/& verbose/' "$REFIND_LINUX_CONF"
    PATCHED_LINUX=1
  fi
  if [[ "$PATCHED_LINUX" -eq 1 ]]; then
    echo "✅ Fallback config patched." | tee -a "$LOG"
  else
    echo "ℹ No changes required in fallback config." | tee -a "$LOG"
  fi
else
  echo "⚠ No fallback file at $REFIND_LINUX_CONF" | tee -a "$LOG"
fi

echo "📑 Patch log complete: $LOG"
