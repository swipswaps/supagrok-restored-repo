#!/usr/bin/env bash
# PRF‑COPYQ‑FLATPAK‑BOOTSTRAP‑2025‑05‑08‑FINAL‑CORRECTED
# UUID: 42fbcfa8-ae19-4ad1-9c21-1e6be52cc7ed
# Timestamp: 2025-05-08T17:00:00Z
# Description: (PRF‑COPYQ‑FLATPAK‑BOOTSTRAP‑2025‑05‑08‑FINAL‑CORRECTED.sh) PRF-compliant, idempotent setup of CopyQ Flatpak with CLI tools and Unicode clipboard migration

set -euo pipefail

echo "🔍 Verifying Flatpak and CopyQ..."
sudo dnf install -y flatpak

if ! flatpak remotes | grep -q flathub; then
  echo "🔗 Adding flathub..."
  flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
fi

echo "📥 Installing CopyQ..."
flatpak install -y --user flathub com.github.hluk.copyq

echo "🛠 Forcing history limit to 20000 via copyq.conf..."
CFG_DIR="$HOME/.var/app/com.github.hluk.copyq/config/copyq"
CFG_FILE="$CFG_DIR/copyq.conf"

mkdir -p "$CFG_DIR"
if grep -q 'historyItems=' "$CFG_FILE" 2>/dev/null; then
  sed -i 's/^historyItems=.*/historyItems=20000/' "$CFG_FILE"
else
  echo 'historyItems=20000' >> "$CFG_FILE"
fi

echo "✅ Config updated: $CFG_FILE"

echo "📋 Writing autostart entry..."
AUTOSTART="$HOME/.config/autostart/copyq-flatpak.desktop"
mkdir -p "$(dirname "$AUTOSTART")"

cat > "$AUTOSTART" <<EOF
[Desktop Entry]
Type=Application
Name=CopyQ Clipboard Manager (Flatpak)
Exec=flatpak run com.github.hluk.copyq
Icon=copyq
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

echo "✅ Autostart updated: $AUTOSTART"

echo "🚀 Restarting CopyQ Flatpak..."
pkill -f 'com.github.hluk.copyq' || true
flatpak run com.github.hluk.copyq --start-server >/dev/null 2>&1 &
sleep 1

# === Optional migration ===
HIST_FILE=$(find ~/.local/share/klipper -iname 'history*.lst' | head -n 1 || true)
HASHLOG=~/.cache/copyq_migration.hashes

if [[ -f "$HIST_FILE" ]]; then
  echo "📂 Migrating from: $HIST_FILE"

  strings "$HIST_FILE" | grep -v '^[[:space:]]*$' | tac | while read -r entry; do
    h=$(printf "%s" "$entry" | sha256sum | cut -d' ' -f1)
    if ! grep -q "$h" "$HASHLOG" 2>/dev/null; then
      flatpak run com.github.hluk.copyq add "$entry" && echo "$h" >> "$HASHLOG"
    fi
  done
  echo "✅ Migration complete. Hashes stored: $HASHLOG"
else
  echo "ℹ️ No KDE Klipper clipboard history found."
fi

echo "🛠 Installing CLI wrappers..."

sudo tee /usr/local/bin/copyq-list >/dev/null <<'EOL'
#!/usr/bin/env bash
set -euo pipefail
if ! flatpak ps | grep -q com.github.hluk.copyq; then
  flatpak run com.github.hluk.copyq --start-server >/dev/null 2>&1 &
  sleep 1
fi
flatpak run com.github.hluk.copyq eval -- "
var output = '';
for (var i = 0; i < size(); ++i) {
  var content = str(read(i)).replace(/\\n/g, '⏎');
  output += i + ': ' + content + '\\n';
}
print(output);"
EOL

sudo tee /usr/local/bin/copyq-read0 >/dev/null <<'EOL'
#!/usr/bin/env bash
set -euo pipefail
if ! flatpak ps | grep -q com.github.hluk.copyq; then
  flatpak run com.github.hluk.copyq --start-server >/dev/null 2>&1 &
  sleep 1
fi
flatpak run com.github.hluk.copyq eval "print(str(read(0)) + '\n')"
EOL

sudo chmod +x /usr/local/bin/copyq-list /usr/local/bin/copyq-read0

echo "✅ Installed: /usr/local/bin/copyq-list"
echo "✅ Installed: /usr/local/bin/copyq-read0"
echo "🎉 CopyQ Flatpak fully PRF-bootstrapped and Unicode-capable."
