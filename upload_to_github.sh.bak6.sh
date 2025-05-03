#!/usr/bin/env bash
# PRF-SUPAGROK-GITHUB-SYNC-2025-05-03-C — Sync local changes to specified GitHub repo via gh CLI (auto-init)
# Directive: PRF-MODIFY-SCRIPT-2025-05-03-C
# UUID: e5f6a7b8-c9d0-1234-5678-90abcdef0123 # Example UUID, replace if needed
# Timestamp: 2025-05-03T02:00:00Z # Example timestamp

# --- Argument Validation ---
# Ensure the target repository argument is provided
: ${1?"Usage: $0 <owner/repo>"}
TARGET_REPO="$1"

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

# --- Check if it's a Git repository and initialize if not ---
echo "ℹ️ Verifying Git repository status..."
if ! git rev-parse --is-inside-work-tree &> /dev/null; then
    echo "ℹ️ Directory is not a Git repository. Initializing..."
    if git init -b main; then # Initialize with 'main' as the default branch
       echo "✅ Git repository initialized successfully."
    else
       echo "❌ Failed to initialize Git repository." >&2
       exit 1
    fi
else
    echo "✅ Directory is already a Git repository."
fi

# --- Git Add/Commit ---
echo "ℹ️ Staging all changes..."
git add .

echo "ℹ️ Committing changes..."
# Use || true to prevent script exit if there are no changes to commit
# Also check if this is the very first commit after init, which might need --allow-empty depending on workflow
# For simplicity, we assume 'git add .' stages something or the commit fails gracefully.
if git commit -m "Automated commit from SupaGrok Script Runner $(date '+%Y-%m-%d %H:%M:%S %Z')"; then
    echo "✅ Changes committed."
else
    # Check if the failure was due to "nothing to commit" vs other errors
    if git diff --quiet && git diff --staged --quiet; then
        echo "ℹ️ No changes to commit."
    else
        echo "⚠️ git commit command failed for reasons other than 'nothing to commit'." >&2
        # Optionally exit here, or let gh repo sync handle potential issues
    fi
fi


echo "ℹ️ Determining current branch..."
# If git init just ran, HEAD might be unborn. Use a default or check.
# 'git symbolic-ref --short HEAD' fails on unborn HEAD, rev-parse might too depending on version.
# Let's try rev-parse first, fall back if needed.
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main") # Default to main if unborn
if [ -z "$CURRENT_BRANCH" ]; then
    # This case should ideally not happen with the fallback, but as a safeguard:
    echo "❌ Could not determine current branch, defaulting to 'main'." >&2
    CURRENT_BRANCH="main"
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
        echo "   - Local branch '${CURRENT_BRANCH}' has diverged significantly from the remote, or remote branch doesn't exist yet (first push?)." >&2
        echo "   - Network issues connecting to GitHub." >&2
        echo "   - If this was the first commit after 'git init', the remote repository might be empty. 'gh repo sync' might need the remote branch to exist first." >&2
    fi
    exit ${GH_EXIT_CODE} # Exit with the same code gh failed with
fi

echo "🎉 GitHub sync process completed successfully for ${TARGET_REPO}."

exit 0
