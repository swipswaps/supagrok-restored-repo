#!/usr/bin/env bash
# PRF-SUPAGROK-GITHUB-SYNC-2025-05-02-C — Sync local changes to GitHub via gh CLI with remote check
# Directive: PRF-MODIFY-SCRIPT-2025-05-02-C
# UUID: b2c3d4e5-f6a7-8901-2345-67890abcdef0 # Example UUID, replace if needed
# Timestamp: 2025-05-02T23:50:00Z # Example timestamp

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

# --- Git Remote Check ---
echo "ℹ️ Verifying 'origin' remote points to GitHub..."
REMOTE_URL=""
if REMOTE_URL=$(git remote get-url origin 2>/dev/null); then
    # Check if the URL contains github.com
    if [[ "$REMOTE_URL" != *"github.com"* ]]; then
        echo "❌ Error: Git remote 'origin' URL (${REMOTE_URL}) does not point to github.com." >&2
        echo "ℹ️ Please update the remote URL using 'git remote set-url origin <correct_github_url>'." >&2
        exit 1
    fi
    echo "✅ Git remote 'origin' found and points to GitHub: ${REMOTE_URL}"
else
    echo "❌ Error: Git remote 'origin' not found." >&2
    echo "ℹ️ Please add the remote using 'git remote add origin <your_github_repo_url>'." >&2
    echo "   Example: git remote add origin git@github.com:OWNER/REPO.git" >&2
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

echo "ℹ️ Attempting to sync repository with GitHub remote using 'gh repo sync'..."
# Sync the current local branch with the remote branch of the same name
# gh should now be able to auto-detect the repo based on the verified 'origin' remote
if gh repo sync --source "${CURRENT_BRANCH}" --branch "${CURRENT_BRANCH}"; then
    echo "✅ Repository synced successfully to branch '${CURRENT_BRANCH}' on remote."
else
    # Capture the exit code from gh
    GH_EXIT_CODE=$?
    echo "❌ Failed to sync repository with GitHub using 'gh repo sync'. Exit code: ${GH_EXIT_CODE}" >&2
    # Optionally, add more specific error handling or suggestions here based on common gh exit codes
    exit ${GH_EXIT_CODE} # Exit with the same code gh failed with
fi

echo "🎉 GitHub sync process completed successfully."

exit 0
