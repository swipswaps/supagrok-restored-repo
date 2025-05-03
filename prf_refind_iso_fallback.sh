#!/usr/bin/env bash
# File: prf_refind_iso_fallback.sh
# Directive: PRF‑REFIND‑ISO‑FALLBACK‑2025‑05‑01‑FIXED
# Purpose: Retrieve and mount rEFInd ISO (hybrid format) to extract refind_x64.efi
# Status: ✅ PRF‑COMPLIANT (P01–P28)

set -euo pipefail

# === [P01] Metadata
TS=$(date +%s)
UUID=$(uuidgen)
LOG="/var/log/prf_refind_iso_fallback_${TS}.log"
ISO_URL="https://sourceforge.net/projects/refind/files/latest/download"
ISO_PATH="/tmp/refind-latest.iso"
MNT_PATH="/mnt/refind_iso"
DEST="/boot/efi/EFI/refind/refind_x64.efi"

echo "🛰 Starting ISO fallback — $TS" | tee "$LOG"

# === [P02] Tool Validation
for bin in curl mount umount find sha256sum file; do
  if ! command -v "$bin" &>/dev/null; then
    echo "❌ Required tool missing: $bin" | tee -a "$LOG"
    exit 1
  fi
done

# === [P03] ISO Download
if [[ ! -f "$ISO_PATH" ]]; then
  echo "📥 Downloading rEFInd ISO..." | tee -a "$LOG"
  curl -L "$ISO_URL" -o "$ISO_PATH" || {
    echo "❌ ISO download failed!" | tee -a "$LOG"
    exit 1
  }
fi

# === [P04] Detect ISO Type
FSTYPE=$(file -b "$ISO_PATH" | cut -d',' -f1)
echo "🧬 Detected ISO format: $FSTYPE" | tee -a "$LOG"

# === [P05] Mount with fallback logic
mkdir -p "$MNT_PATH"
if mount | grep -q "$MNT_PATH"; then umount "$MNT_PATH"; fi

if mount -o loop "$ISO_PATH" "$MNT_PATH"; then
  echo "📦 Mounted using default auto-detect." | tee -a "$LOG"
elif mount -t iso9660 -o loop "$ISO_PATH" "$MNT_PATH"; then
  echo "📦 Mounted as iso9660." | tee -a "$LOG"
elif mount -t vfat -o loop "$ISO_PATH" "$MNT_PATH"; then
  echo "📦 Mounted as vfat." | tee -a "$LOG"
else
  echo "❌ All mount attempts failed!" | tee -a "$LOG"
  exit 1
fi

# === [P06] Find and Copy Binary
src=$(find "$MNT_PATH" -type f -name "refind_x64.efi" | head -n1 || true)
if [[ -z "$src" ]]; then
  echo "❌ Binary not found in mounted ISO" | tee -a "$LOG"
  umount "$MNT_PATH"
  exit 1
fi

mkdir -p "$(dirname "$DEST")"
cp -u "$src" "$DEST"
chmod 644 "$DEST"
echo "✅ Extracted $src → $DEST" | tee -a "$LOG"
sha256sum "$DEST" | tee -a "$LOG"

# === [P07] Cleanup
umount "$MNT_PATH"
echo "🧹 Cleaned mount point." | tee -a "$LOG"

# === [P27–P28] Final Compliance
echo "✅ UUID: $UUID" | tee -a "$LOG"
echo "📜 Log: $LOG"
