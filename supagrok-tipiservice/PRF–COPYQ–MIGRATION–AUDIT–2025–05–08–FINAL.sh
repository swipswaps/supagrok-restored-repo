#!/usr/bin/env bash
# PRF–COPYQ–MIGRATION–AUDIT–2025–05–08–FINAL
# UUID: b445b0f6-44e7-47fd-bf97-cda4bc7f7db2
# Description: Compares number of valid KDE Klipper entries with CopyQ Flatpak size

set -euo pipefail

KLIPPER_FILE=$(find "$HOME/.local/share/klipper" -iname 'history*.lst' | head -n 1 || true)

if [[ -z "$KLIPPER_FILE" || ! -f "$KLIPPER_FILE" ]]; then
  echo "❌ No Klipper history file found."
  exit 1
fi

echo "📂 Scanning Klipper history: $KLIPPER_FILE"

KLIPPER_COUNT=$(strings "$KLIPPER_FILE" | grep -v '^[[:space:]]*$' | sort | uniq | wc -l)
echo "🧾 Unique non-blank entries in Klipper: $KLIPPER_COUNT"

if ! flatpak run com.github.hluk.copyq --start-server >/dev/null 2>&1; then
  echo "🚀 Starting CopyQ Flatpak..."
  flatpak run com.github.hluk.copyq --start-server >/dev/null 2>&1 &
  sleep 1
fi

COPYQ_COUNT=$(flatpak run com.github.hluk.copyq eval 'print(size())' 2>/dev/null | grep -E '^[0-9]+$' || echo 0)
echo "📋 Entries currently in CopyQ: $COPYQ_COUNT"

if [[ "$COPYQ_COUNT" -lt "$KLIPPER_COUNT" ]]; then
  echo "⚠️ WARNING: Fewer items in CopyQ than source. Some entries may not have been migrated."
  exit 2
elif [[ "$COPYQ_COUNT" -eq "$KLIPPER_COUNT" ]]; then
  echo "✅ SUCCESS: CopyQ contains all migrated entries."
else
  echo "ℹ️ NOTE: CopyQ contains more items than Klipper. May include older or new runtime entries."
fi
