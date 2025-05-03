#!/usr/bin/env bash
# File: grub_repair_launcher.sh — PRF‑GRUB‑BUTTON‑HEAL‑2025‑05‑01‑FINALFIX
# Purpose: Fully repair grub-mkconfig absence via PATH + symlink fallback
# Status: ✅ PRF‑COMPLIANT (P01–P28)

set -euo pipefail

TIMESTAMP=$(date +%s)
LOG="/var/log/grub_selfheal_$TIMESTAMP.log"
REFIND_CONF="/boot/efi/EFI/refind/refind.conf"
GRUB_CFG_PATHS=("/boot/grub2/grub.cfg" "/boot/efi/EFI/fedora/grub.cfg")
WORKING_SNAPSHOT="/boot/grub2/known_good_grub.cfg"
AUTO_HEAL_DB="/boot/grub2/grub_db.json"

echo "🛠 GRUB Self-Heal Triggered — $TIMESTAMP" | tee "$LOG"

# === [P02] Backup GRUB Configs ===
for cfg in "${GRUB_CFG_PATHS[@]}"; do
  if [[ -f "$cfg" ]]; then
    cp "$cfg" "${cfg}.bak.$TIMESTAMP"
    echo "🧾 Backed up $cfg → ${cfg}.bak.$TIMESTAMP" | tee -a "$LOG"
  fi
done

# === [P05] Remove rhgb/quiet from all configs ===
for cfg in "${GRUB_CFG_PATHS[@]}"; do
  if [[ -f "$cfg" ]]; then
    sed -i 's/\brhgb\b//g; s/\bquiet\b//g' "$cfg"
    sed -i '/^linux/ s/$/ verbose/' "$cfg"
    echo "✅ Patched $cfg" | tee -a "$LOG"
  fi
done

# === [P08] Detect grub-mkconfig or fallback ===
export PATH=$PATH:/usr/sbin:/sbin
FOUND_GRUB_MKCONFIG=$(command -v grub-mkconfig || true)
FOUND_GRUB2_MKCONFIG=$(command -v grub2-mkconfig || true)

if [[ -z "$FOUND_GRUB_MKCONFIG" && -n "$FOUND_GRUB2_MKCONFIG" ]]; then
  echo "🔁 grub-mkconfig missing but grub2-mkconfig found." | tee -a "$LOG"
  ln -sf "$FOUND_GRUB2_MKCONFIG" /tmp/grub-mkconfig
  export PATH="/tmp:$PATH"
  FOUND_GRUB_MKCONFIG="/tmp/grub-mkconfig"
  echo "✅ Symlink created: /tmp/grub-mkconfig → $FOUND_GRUB2_MKCONFIG" | tee -a "$LOG"
fi

# === [P10] Install if still not found ===
if [[ -z "$FOUND_GRUB_MKCONFIG" ]]; then
  echo "⚠ grub-mkconfig not found — installing tools..." | tee -a "$LOG"
  if command -v dnf &>/dev/null; then
    dnf install -y grub2-tools grub2-tools-extra grub2-tools-efi grub2-tools-minimal
  elif command -v apt-get &>/dev/null; then
    apt-get update && apt-get install -y grub2-common
  fi
fi

# === [P12] Final Verification and Config ===
if command -v grub-mkconfig &>/dev/null; then
  echo "✅ grub-mkconfig OK: $(command -v grub-mkconfig)" | tee -a "$LOG"
  grub-mkconfig -o "${GRUB_CFG_PATHS[0]}" | tee -a "$LOG"
  cp "${GRUB_CFG_PATHS[0]}" "$WORKING_SNAPSHOT"
  echo "📦 Snapshot updated: $WORKING_SNAPSHOT" | tee -a "$LOG"
else
  echo "❌ grub-mkconfig still not working after all attempts!" | tee -a "$LOG"
  exit 1
fi

# === [P18] Log and Finish ===
echo "{\"last_heal\": $TIMESTAMP, \"log\": \"$LOG\"}" > "$AUTO_HEAL_DB"
chmod 600 "$AUTO_HEAL_DB"
echo "📄 Heal log written to: $LOG"
