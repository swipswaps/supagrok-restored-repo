#!/usr/bin/env bash
# PRF‑COPYQ‑LIST‑WRAPPER‑2025‑05‑08‑VERIFIED
# UUID: 9f901d6d-e25f-45a5-b35b-1e2b32c187e5
# Description: Hardened CopyQ Flatpak list tool with session bootstrap wait loop
# Description: (PRF‑COPYQ‑LIST‑WRAPPER‑2025‑05‑08‑VERIFIED.sh) Hardened CopyQ Flatpak list tool with session bootstrap wait loop
set -euo pipefail

export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

# Start server if needed and wait up to 10s for socket
if ! flatpak ps | grep -q com.github.hluk.copyq; then
  echo "🚀 Starting CopyQ Flatpak server..."
  flatpak run com.github.hluk.copyq --start-server >/dev/null 2>&1 &
  
  for i in {1..10}; do
    sleep 1
    if flatpak run com.github.hluk.copyq eval 'exit(0)' >/dev/null 2>&1; then
      break
    fi
  done
fi

# Final check
if ! flatpak run com.github.hluk.copyq eval 'exit(0)' >/dev/null 2>&1; then
  echo "❌ Failed to connect to CopyQ Flatpak server after retry."
  exit 1
fi

flatpak run com.github.hluk.copyq eval -- "
var out = '';
for (var i = 0; i < size(); ++i) {
  var content = str(read(i)).replace(/\n/g, '⏎');
  out += i + ': ' + content + '\n';
}
print(out);"
