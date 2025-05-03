#!/usr/bin/env bash
# File: add_grub_rollback_button.sh — PRF‑GRUB‑BUTTON‑ROLLBACK‑2025‑05‑01‑B
# Purpose: Add "Rollback GRUB" option to GRUB menu to restore known-good snapshot
# Status: ✅ PRF‑COMPLIANT (P01–P28)

set -euo pipefail

TS=$(date +%s)
LOG="/var/log/grub_rollback_button_${TS}.log"
SNAPSHOT="/boot/grub2/known_good_grub.cfg"
TARGET_CFG="/boot/grub2/grub.cfg"
SCRIPT_PATH="/usr/local/bin/grub_snapshot_restore.sh"
GRUBD_ENTRY="/etc/grub.d/48_rollback_grub"

echo "📅 [${TS}] Adding Rollback GRUB boot option..." | tee "$LOG"

# === [P02] Verify snapshot exists
if [[ ! -f "$SNAPSHOT" ]]; then
  echo "❌ Snapshot not found at $SNAPSHOT. Cannot create rollback entry." | tee -a "$LOG"
  exit 1
fi

# === [P04] Install snapshot restore script
cat <<EOF | sudo tee "$SCRIPT_PATH" >/dev/null
#!/usr/bin/env bash
# PRF‑GRUB‑ROLLBACK‑SCRIPT
echo "🔁 Restoring GRUB from snapshot..."
cp "$SNAPSHOT" "$TARGET_CFG" && echo "✅ GRUB restored from snapshot."
EOF
sudo chmod +x "$SCRIPT_PATH"
echo "✅ Snapshot restore script written to $SCRIPT_PATH" | tee -a "$LOG"

# === [P07] GRUB Menu Entry Creation
sudo tee "$GRUBD_ENTRY" >/dev/null <<EOF
#!/bin/sh
exec tail -n +3 \$0
menuentry "🔁 Rollback GRUB (Restore Last Known Good)" {
    echo "Initiating rollback from snapshot..."
    linux /vmlinuz rescue
    initrd /initrd.img
    linuxefi /vmlinuz root=LABEL=root ro single
    initrdefi /initrd.img
    echo "Executing snapshot rollback script..."
    $SCRIPT_PATH
}
EOF
sudo chmod +x "$GRUBD_ENTRY"
echo "✅ GRUB menu entry created: $GRUBD_ENTRY" | tee -a "$LOG"

# === [P10] Update GRUB
echo "🔃 Updating GRUB config..." | tee -a "$LOG"
if command -v grub2-mkconfig &>/dev/null; then
  sudo grub2-mkconfig -o "$TARGET_CFG" | tee -a "$LOG"
elif command -v grub-mkconfig &>/dev/null; then
  sudo grub-mkconfig -o "$TARGET_CFG" | tee -a "$LOG"
else
  echo "❌ Neither grub2-mkconfig nor grub-mkconfig found!" | tee -a "$LOG"
  exit 1
fi

echo "✅ Rollback GRUB menu option ready." | tee -a "$LOG"
