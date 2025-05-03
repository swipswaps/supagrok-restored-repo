#!/usr/bin/env bash
# PRF-SUPAGROK-GITHUB-SYNC-2025-05-03-A — Sync local changes to specific GitHub repo via gh CLI
# Directive: PRF-MODIFY-SCRIPT-2025-05-03-A
# UUID: c3d4e5f6-a7b8-9012-3456-7890abcdef01 # Example UUID, replace if needed
# Timestamp: 2025-05-03T00:30:00Z # Example timestamp

# --- Configuration ---
# !!! IMPORTANT: Replace this with your actual GitHub username/organization and repository name !!!
TARGET_REPO="owner/supagrok_restored_repo"
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Exit on error, undefined variable, or pipe failure
set -euo pipefail

# Define the directory where the script is located and where the git repo is
# Assumes the script resides in the root of the repository it needs to sync.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
REPO_DIR="$SCRIPT_DIR"

echo "▶️ Starting GitHub sync for repository '${TARGET_REPO}' via gh CLI..."

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

# --- Check if it's a Git repository ---
echo "ℹ️ Verifying this is a Git repository..."
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "❌ Error: Directory ${REPO_DIR} is not a Git repository." >&2
    echo "ℹ️ Please initialize it using 'git init'." >&2
    exit 1
fi
echo "✅ Directory is a Git repository."

# --- Git Add/Commit ---
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

# --- GitHub Sync ---
echo "ℹ️ Attempting to sync repository with GitHub remote '${TARGET_REPO}' using 'gh repo sync'..."
# Sync the current local branch with the remote branch of the same name on the specified repo
if gh repo sync "${TARGET_REPO}" --source "${CURRENT_BRANCH}" --branch "${CURRENT_BRANCH}"; then
    echo "✅ Repository synced successfully to branch '${CURRENT_BRANCH}' on remote '${TARGET_REPO}'."
else
    # Capture the exit code from gh
    GH_EXIT_CODE=$?
    echo "❌ Failed to sync repository '${TARGET_REPO}' with GitHub using 'gh repo sync'. Exit code: ${GH_EXIT_CODE}" >&2
    # Provide more specific advice for common errors if possible
    if [[ ${GH_EXIT_CODE} -eq 1 ]]; then
        echo "ℹ️ Common causes include:" >&2
        echo "   - Repository '${TARGET_REPO}' not found on GitHub or insufficient permissions." >&2
        echo "   - Local branch '${CURRENT_BRANCH}' has diverged significantly from the remote." >&2
        echo "   - Network issues connecting to GitHub." >&2
    fi
    exit ${GH_EXIT_CODE} # Exit with the same code gh failed with
fi

echo "🎉 GitHub sync process completed successfully for ${TARGET_REPO}."

exit 0
