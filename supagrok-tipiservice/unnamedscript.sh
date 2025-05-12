#!/usr/bin/env bash
# PRF‑COPYQ‑FLATPAK‑BOOTSTRAP‑2025‑05‑08‑FINAL‑REISSUE‑IDEMPOTENT
# UUID: 42fbcfa8-ae19-4ad1-9c21-1e6be52cc7ed
# Description: Idempotent PRF setup for CopyQ Flatpak with CLI tools and autostart

set -euo pipefail

echo "🔍 [PRF] Verifying dependencies..."

# Install flatpak if missing
if ! command -v flatpak &>/dev/null; then
  echo "📦 Installing Flatpak..."
  sudo dnf install -y flatpak
fi

# Add flathub if missing
if ! flatpak remotes | grep -q flathub; then
  echo "🔗 Adding Flathub remote..."
  flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
fi

# Install CopyQ via Flatpak (safe idempotent)
echo "📥 Installing/Refreshing CopyQ Flatpak..."
flatpak install -y --user flathub com.github.hluk.copyq

# Create autostart entry (overwrite-safe)
AUTOSTART=~/.config/autostart/copyq-flatpak.desktop
mkdir -p ~/.config/autostart
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

# Klipper history migration
HIST_FILE=$(find ~/.local/share/klipper -iname 'history*.lst' | head -n 1 || true)
if [[ -f "$HIST_FILE" ]]; then
  echo "📂 Migrating from: $HIST_FILE"
  strings "$HIST_FILE" | grep -v '^[[:space:]]*$' | tac | while read -r entry; do
    flatpak run com.github.hluk.copyq add "$entry" || true
  done
  echo "✅ Migration complete."
else
  echo "ℹ️ No Klipper clipboard history found."
fi

# CLI wrappers — overwrite-safe
echo "🛠 Creating CLI tools..."

sudo tee /usr/local/bin/copyq-list >/dev/null <<'EOL'
#!/usr/bin/env bash
set -euo pipefail
# CLI: Lists CopyQ entries (Flatpak version)

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
# CLI: Print first CopyQ clipboard entry

if ! flatpak ps | grep -q com.github.hluk.copyq; then
  flatpak run com.github.hluk.copyq --start-server >/dev/null 2>&1 &
  sleep 1
fi

flatpak run com.github.hluk.copyq eval "print(str(read(0)) + '\n')"
EOL

sudo chmod +x /usr/local/bin/copyq-list /usr/local/bin/copyq-read0

echo "✅ Installed: /usr/local/bin/copyq-list"
echo "✅ Installed: /usr/local/bin/copyq-read0"
echo "🎉 CopyQ Flatpak now fully bootstrapped and PRF-compliant."
