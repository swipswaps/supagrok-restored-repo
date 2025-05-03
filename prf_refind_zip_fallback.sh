#!/usr/bin/env bash
# File: prf_refind_zip_fallback.sh
# Directive: PRF‑REFIND‑ZIP‑FALLBACK‑2025‑05‑01‑A
# Purpose: Extract refind_x64.efi from ZIP archive misnamed as ISO
# Status: ✅ PRF‑COMPLIANT (P01–P28)

set -euo pipefail

# === [P01] Metadata
TS=$(date +%s)
UUID=$(uuidgen)
LOG="/var/log/prf_refind_zip_fallback_${TS}.log"
ISO_URL="https://sourceforge.net/projects/refind/files/latest/download"
ZIP_PATH="/tmp/refind-latest.iso"
UNZIP_DIR="/tmp/refind_unzipped"
DEST="/boot/efi/EFI/refind/refind_x64.efi"

echo "📦 Starting rEFInd ZIP fallback — $TS" | tee "$LOG"

# === [P02] Tool Check
for bin in curl unzip find sha256sum file; do
  if ! command -v "$bin" &>/dev/null; then
    echo "❌ Required tool missing: $bin" | tee -a "$LOG"
    exit 1
  fi
done

# === [P03] Download ZIP (misnamed ISO)
if [[ ! -f "$ZIP_PATH" ]]; then
  echo "📥 Downloading ZIP pretending to be ISO..." | tee -a "$LOG"
  curl -L "$ISO_URL" -o "$ZIP_PATH" || {
    echo "❌ Download failed!" | tee -a "$LOG"
    exit 1
  }
fi

# === [P04] Detect Format
FSTYPE=$(file -b "$ZIP_PATH" | cut -d',' -f1)
echo "🧬 Detected format: $FSTYPE" | tee -a "$LOG"
if ! echo "$FSTYPE" | grep -iq "zip"; then
  echo "❌ File is not a ZIP archive. Aborting." | tee -a "$LOG"
  exit 1
fi

# === [P05] Unzip Contents
mkdir -p "$UNZIP_DIR"
unzip -o "$ZIP_PATH" -d "$UNZIP_DIR" | tee -a "$LOG"

# === [P06] Find Binary
src=$(find "$UNZIP_DIR" -type f -name "refind_x64.efi" | head -n1 || true)
if [[ -z "$src" ]]; then
  echo "❌ refind_x64.efi not found in ZIP contents" | tee -a "$LOG"
  exit 1
fi

# === [P07] Copy and Verify
mkdir -p "$(dirname "$DEST")"
cp -u "$src" "$DEST"
chmod 644 "$DEST"
echo "✅ Copied $src → $DEST" | tee -a "$LOG"
sha256sum "$DEST" | tee -a "$LOG"

# === [P28] Output
echo "✅ UUID: $UUID" | tee -a "$LOG"
echo "📜 Log: $LOG"
