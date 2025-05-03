#!/usr/bin/env bash
# PRF-SUPAGROK-GITHUB-SYNC-2025-05-03-F — Conditionally Create (Non-Interactive) or Sync GitHub repo
# Directive: PRF-MODIFY-SCRIPT-2025-05-03-F
# UUID: 12345678-9abc-def0-1234-56789abcdef0 # Example UUID, replace if needed
# Timestamp: 2025-05-03T05:00:00Z # Example timestamp

# --- Argument Validation ---
# Ensure the target repository argument is provided
: ${1?"Usage: $0 <owner/repo>"}
TARGET_REPO="$1"
# --- Configuration ---
# Set desired visibility for new repositories ('public', 'private', 'internal')
NEW_REPO_VISIBILITY="public"

# Exit on error, undefined variable, or pipe failure
set -euo pipefail

# Define the directory where the script is located and where the git repo is
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
REPO_DIR="$SCRIPT_DIR"

echo "▶️ Starting GitHub operation for repository '${TARGET_REPO}' via gh CLI..."

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
    gh auth status >&2
    exit 1
fi
echo "✅ GitHub authentication successful."

# --- Repository Operations ---
echo "ℹ️ Attempting to change to repository directory: ${REPO_DIR}"
if ! cd "$REPO_DIR"; then
    echo "❌ Failed to change directory to ${REPO_DIR}" >&2
    exit 1
fi
echo "✅ Successfully changed to directory: $(pwd)"

# --- Check if it's a Git repository and initialize if not ---
echo "ℹ️ Verifying Git repository status..."
if ! git rev-parse --is-inside-work-tree &> /dev/null; then
    echo "ℹ️ Directory is not a Git repository. Initializing..."
    if git init -b main; then
       echo "✅ Git repository initialized successfully."
    else
       echo "❌ Failed to initialize Git repository." >&2
       exit 1
    fi
else
    echo "✅ Directory is already a Git repository."
fi

# --- Git Add/Commit ---
echo "ℹ️ Staging all changes (git add .)..."
git add .
echo "✅ Staging complete."

echo "ℹ️ Committing changes..."
if git commit -m "Automated commit from SupaGrok Script Runner $(date '+%Y-%m-%d %H:%M:%S %Z')"; then
    echo "✅ Changes committed."
else
    if git diff --quiet && git diff --staged --quiet; then
        echo "ℹ️ No changes to commit."
    else
        echo "⚠️ git commit command failed for reasons other than 'nothing to commit'." >&2
    fi
fi

echo "ℹ️ Determining current branch..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
if [ -z "$CURRENT_BRANCH" ]; then
    echo "❌ Could not determine current branch, defaulting to 'main'." >&2
    CURRENT_BRANCH="main"
fi
echo "✅ Current branch is '${CURRENT_BRANCH}'."

# --- Conditional GitHub Create or Sync ---
echo "ℹ️ Checking if remote repository '${TARGET_REPO}' exists..."
if gh repo view "${TARGET_REPO}" &> /dev/null; then
    # Repository Exists - Perform Sync
    echo "✅ Remote repository found. Attempting to sync..."
    if gh repo sync "${TARGET_REPO}" --source "${CURRENT_BRANCH}" --branch "${CURRENT_BRANCH}"; then
        echo "✅ Repository synced successfully to branch '${CURRENT_BRANCH}' on remote '${TARGET_REPO}'."
    else
        GH_EXIT_CODE=$?
        echo "❌ Failed to sync existing repository '${TARGET_REPO}' with GitHub using 'gh repo sync'. Exit code: ${GH_EXIT_CODE}" >&2
        if [[ ${GH_EXIT_CODE} -eq 1 ]]; then
            echo "ℹ️ Common causes for sync failure include:" >&2
            echo "   - Local branch '${CURRENT_BRANCH}' has diverged significantly from the remote." >&2
            echo "   - Network issues connecting to GitHub." >&2
        fi
        exit ${GH_EXIT_CODE}
    fi
else
    # Repository Does Not Exist (or inaccessible) - Perform Create Non-Interactively
    echo "ℹ️ Remote repository not found or inaccessible. Attempting to create and push non-interactively..."
    # Use --push to push the current branch after creation
    # Add --public, --private, or --internal as needed
    # Redirect stdin from /dev/null to prevent interactive prompts
    if gh repo create "${TARGET_REPO}" --source . --push "--${NEW_REPO_VISIBILITY}" < /dev/null; then
        echo "✅ Repository '${TARGET_REPO}' created successfully and initial code pushed."
    else
        GH_EXIT_CODE=$?
        echo "❌ Failed to create repository '${TARGET_REPO}' with GitHub using 'gh repo create'. Exit code: ${GH_EXIT_CODE}" >&2
         if [[ ${GH_EXIT_CODE} -eq 1 ]]; then
            echo "ℹ️ Common causes for create failure include:" >&2
            echo "   - Repository name '${TARGET_REPO}' already exists but is inaccessible." >&2
            echo "   - Insufficient permissions to create repositories in the specified owner/organization." >&2
            echo "   - Network issues connecting to GitHub." >&2
            echo "   - Missing required information that could not be prompted for (check gh create defaults)." >&2
        fi
        exit ${GH_EXIT_CODE}
    fi
fi

echo "🎉 GitHub operation completed successfully for ${TARGET_REPO}."

exit 0
