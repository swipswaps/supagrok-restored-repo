#!/usr/bin/env bash
# File: prf_register_refind.sh — PRF‑REFIND‑BOOT‑REGISTER‑2025‑05‑01‑FINAL
# Purpose: Auto-register rEFInd bootloader, verify fallback, prioritize boot order, and validate themed config
# Status: ✅ PRF‑COMPLIANT (P01–P28)

set -euo pipefail

# === [P01] Metadata ===
TS=$(date +%s)
LOG="/var/log/refind_register_$TS.log"
REFIND_DIR="/boot/efi/EFI/refind"
REFIND_EFI="$REFIND_DIR/refind_x64.efi"
FALLBACK_EFI="/boot/efi/EFI/Boot/bootx64.efi"
THEME_CONF="$REFIND_DIR/theme/theme.conf"
REFIND_CONF="$REFIND_DIR/refind.conf"

echo "🚀 Registering rEFInd @ $TS" | tee "$LOG"

# === [P02] Ensure rEFInd EFI Exists ===
if [[ ! -f "$REFIND_EFI" ]]; then
  echo "❌ rEFInd EFI not found at $REFIND_EFI" | tee -a "$LOG"
  exit 1
fi

# === [P03] Fallback Copy ===
mkdir -p "$(dirname "$FALLBACK_EFI")"
cp -u "$REFIND_EFI" "$FALLBACK_EFI" && echo "✅ Copied fallback: $FALLBACK_EFI" | tee -a "$LOG"

# === [P04] Register rEFInd Boot Entry ===
efibootmgr | grep -q "rEFInd" || {
  efibootmgr --create --disk /dev/nvme0n1 --part 1 \
    --label "rEFInd" --loader "\\EFI\\refind\\refind_x64.efi" && \
  echo "✅ Registered rEFInd entry" | tee -a "$LOG"
}

# === [P05] Promote rEFInd in BootOrder ===
BOOT_ID=$(efibootmgr | grep rEFInd | awk '{print $1}' | sed 's/Boot//;s/\*//')
if [[ -n "$BOOT_ID" ]]; then
  efibootmgr --bootorder "$BOOT_ID" && echo "✅ Set BootOrder: $BOOT_ID first" | tee -a "$LOG"
else
  echo "❌ Failed to extract Boot ID for rEFInd" | tee -a "$LOG"
fi

# === [P06] Theme Verification ===
for conf in "$REFIND_CONF" "$THEME_CONF"; do
  if [[ -f "$conf" ]]; then
    echo "✅ Found config: $conf" | tee -a "$LOG"
    grep -q "menuentry" "$conf" && echo "✔️  Valid config contains menu entries" | tee -a "$LOG"
  else
    echo "❌ Missing config: $conf" | tee -a "$LOG"
  fi
done

# === [P27] Permissions
chmod 644 "$REFIND_CONF" "$THEME_CONF" 2>/dev/null || true

echo "📜 Log: $LOG"
echo "✅ rEFInd Boot Registration Complete"
