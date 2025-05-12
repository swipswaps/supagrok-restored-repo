#!/usr/bin/env bash
# PRF-COMPLIANT GITHUB PUSH: Moves large files, cleans history, updates .gitignore, and pushes safely.

set -euo pipefail

# --- CONFIGURABLES ---
LARGE_FILES=(
  ".git_bak/objects/4b/82e64c5066c5d0a32099924f66ed93c93b4c21"
  "node_modules/electron/dist/electron"
)
BACKUP_DIR="$HOME/Documents/large_files_backup"
GITIGNORE=".gitignore"
TARGET_REPO="swipswaps/supagrok-restored-repo"

# --- 1. Move Large Files Out of Repo ---
mkdir -p "$BACKUP_DIR"
for f in "${LARGE_FILES[@]}"; do
  if [ -f "$f" ]; then
    echo "Moving $f to $BACKUP_DIR/"
    mv "$f" "$BACKUP_DIR/"
  fi
done

# --- 2. Update .gitignore ---
for pattern in ".git_bak/" "node_modules/"; do
  grep -qxF "$pattern" "$GITIGNORE" || echo "$pattern" >> "$GITIGNORE"
done

# --- 3. Remove from Git Index ---
for f in "${LARGE_FILES[@]}"; do
  git rm --cached -f "$f" 2>/dev/null || true
done
git add "$GITIGNORE"
git commit -m "PRF: Remove large files, update .gitignore for GitHub compliance" || true

# --- 4. Clean Git History (requires git-filter-repo) ---
if ! command -v git-filter-repo &>/dev/null; then
  echo "Installing git-filter-repo..."
  sudo dnf install -y git-filter-repo
fi
for f in "${LARGE_FILES[@]}"; do
  git filter-repo --path "$f" --invert-paths || true
done

# --- 5. Push using existing upload_to_github.sh ---
bash ./upload_to_github.sh "$TARGET_REPO"