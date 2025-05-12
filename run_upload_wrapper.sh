#!/bin/bash

# Wrapper script to commit changes to the upload script itself
# before running the upload script for the target directory.

set -euo pipefail

# --- Configuration ---
# Adjust paths as necessary
SCRIPT_PARENT_DIR="/home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca/app/supagrok_restored_repo"
UPLOAD_SCRIPT_RELPATH="app3/upload_to_github.sh" # Relative path from SCRIPT_PARENT_DIR
TARGET_REPO_ARG="$1" # Pass the owner/repo argument through

# --- Argument Check ---
if [ -z "$TARGET_REPO_ARG" ]; then
    echo "Usage: $0 <owner/repo>"
    exit 1
fi

# --- Commit Script Changes ---
echo "ℹ️ Checking for changes to the upload script..."
cd "$SCRIPT_PARENT_DIR" || exit 1

if ! git diff --quiet -- "$UPLOAD_SCRIPT_RELPATH"; then
    echo "ℹ️ Found changes in '$UPLOAD_SCRIPT_RELPATH'. Adding and committing..."
    git add "$UPLOAD_SCRIPT_RELPATH"
    git commit -m "Update upload script ($UPLOAD_SCRIPT_RELPATH)" || echo "⚠️ Commit failed (maybe no changes after all?)"
else
    echo "ℹ️ No changes detected in '$UPLOAD_SCRIPT_RELPATH'."
fi

# --- Run the Upload Script ---
echo "ℹ️ Running the main upload script for target directory..."
"$SCRIPT_PARENT_DIR/$UPLOAD_SCRIPT_RELPATH" "$TARGET_REPO_ARG"