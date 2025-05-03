#!/usr/bin/env bash
# PRF-SUPAGROK-GITHUB-SYNC-2025-05-02-B — Sync local changes to GitHub via gh CLI
# Directive: PRF-MODIFY-SCRIPT-2025-05-02-B
# UUID: a1b2c3d4-e5f6-7890-1234-567890abcdef # Example UUID, replace if needed
# Timestamp: 2025-05-02T22:30:00Z # Example timestamp

# Exit on error, undefined variable, or pipe failure
set -euo pipefail

# Define the directory where the script is located and where the git repo is
# Assumes the script resides in the root of the repository it needs to sync.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
REPO_DIR="$SCRIPT_DIR"

echo "▶️ Starting GitHub sync via gh CLI..."

# --- Dependency Checks ---
echo "ℹ️ Checking for required tools (git, gh)..."
if ! command -v gh &> /dev/null; then
  echo "❌ GitHub CLI (gh) not found. Install from https://cli.github.com" >&2
  exit 1
fi
if ! command -v git &> /dev/null; then
  echo "❌ Git not found. Please install Git." >&2
  exit 1
fi
echo "✅ Required tools found."

# --- Authentication Check ---
echo "ℹ️ Checking GitHub authentication..."
if ! gh auth status > /dev/null; then
    echo "❌ GitHub authentication failed. Please run 'gh auth login'." >&2
    # Attempt to display the actual error from gh auth status
    gh auth status >&2
    exit 1
fi
echo "✅ GitHub authentication successful."

# --- Repository Operations ---
echo "ℹ️ Changing to repository directory: ${REPO_DIR}"
if ! cd "$REPO_DIR"; then
    echo "❌ Failed to change directory to ${REPO_DIR}" >&2
    exit 1
fi

echo "ℹ️ Staging all changes..."
git add .

echo "ℹ️ Committing changes..."
# Use || true to prevent script exit if there are no changes to commit
if git commit -m "Automated commit from SupaGrok Script Runner $(date '+%Y-%m-%d %H:%M:%S %Z')"; then
    echo "✅ Changes committed."
else
    echo "ℹ️ No changes to commit."
fi

echo "ℹ️ Determining current branch..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ -z "$CURRENT_BRANCH" ]; then
    echo "❌ Could not determine current branch." >&2
    exit 1
fi
echo "✅ Current branch is '${CURRENT_BRANCH}'."

echo "ℹ️ Syncing repository with GitHub remote..."
# Sync the current local branch with the remote branch of the same name
# Assumes the remote is configured correctly (e.g., named 'origin')
if gh repo sync --source "${CURRENT_BRANCH}" --branch "${CURRENT_BRANCH}"; then
    echo "✅ Repository synced successfully to branch '${CURRENT_BRANCH}' on remote."
else
    echo "❌ Failed to sync repository with GitHub." >&2
    # Optionally, add more specific error handling or suggestions here
    exit 1
fi

echo "🎉 GitHub sync process completed successfully."

exit 0
