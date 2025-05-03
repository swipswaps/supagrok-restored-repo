#!/usr/bin/env bash
set -euo pipefail
JSON_FILE="supagrok_repo_snapshot_2025_04_29_CORRECTED_COMPLETE.json"
TARGET_DIR="./supagrok_restored_repo"
mkdir -p "$TARGET_DIR"
jq -c '.files[]' "$JSON_FILE" | while read -r entry; do
  path=$(echo "$entry" | jq -r '.path')
  perms=$(echo "$entry" | jq -r '.permissions')
  content=$(echo "$entry" | jq -r '.content')
  full_path="$TARGET_DIR/$path"
  mkdir -p "$(dirname \"$full_path\")"
  echo "$content" > "$full_path"
  chmod "$perms" "$full_path"
  echo "✅ Restored: $full_path (perm $perms)"
done
echo "\n✅ All files unpacked to $TARGET_DIR"
