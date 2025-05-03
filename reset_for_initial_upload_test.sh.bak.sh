#!/usr/bin/env bash
# PRF-SUPAGROK-TEST-RESET-2025-05-03-A — Automates setup for initial GitHub upload test
# Directive: PRF-CREATE-SCRIPT-2025-05-03-A
# UUID: 3456789a-bcde-f012-3456-789abcdef012 # Example UUID, replace if needed
# Timestamp: 2025-05-03T07:00:00Z # Example timestamp

# --- Argument Validation ---
: ${1?"Usage: $0 <owner/repo>"}
TARGET_REPO="$1"

# Exit on most errors, but allow gh repo delete to fail if repo doesn't exist
set -uo pipefail
# Temporarily disable exit on error for gh repo delete
set +e

# Define the directory where this script resides
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

echo "▶️ Starting reset procedure for testing initial upload to '${TARGET_REPO}'..."
echo "   Target directory: ${SCRIPT_DIR}"

# --- Dependency Check ---
echo "ℹ️ Checking for required tool (gh)..."
if ! command -v gh &> /dev/null; then
  echo "❌ GitHub CLI (gh) not found. Install from https://cli.github.com" >&2
  exit 1
fi
echo "✅ Required tool (gh) found."

# --- Authentication Check ---
echo "ℹ️ Checking GitHub authentication..."
if ! gh auth status > /dev/null; then
    echo "❌ GitHub authentication failed. Please run 'gh auth login'." >&2
    gh auth status >&2
    exit 1
fi
echo "✅ GitHub authentication successful."


# --- Delete Remote Repository (Non-Interactive) ---
echo "ℹ️ Attempting to delete remote repository '${TARGET_REPO}' (if it exists)..."
gh repo delete "${TARGET_REPO}" --yes
DELETE_EXIT_CODE=$?
# Re-enable exit on error
set -e
# Check exit code specifically for "not found" vs other errors
if [[ ${DELETE_EXIT_CODE} -eq 0 ]]; then
    echo "✅ Remote repository '${TARGET_REPO}' deleted successfully."
elif gh repo view "${TARGET_REPO}" &> /dev/null; then
    # If delete failed but view succeeds, it was likely a permissions issue or other error
    echo "❌ Failed to delete remote repository '${TARGET_REPO}'. Exit code: ${DELETE_EXIT_CODE}. Please check permissions or delete manually." >&2
    exit ${DELETE_EXIT_CODE}
else
    # If delete failed and view fails, the repo likely didn't exist, which is fine.
    echo "ℹ️ Remote repository '${TARGET_REPO}' not found or already deleted. Proceeding..."
fi


# --- Delete Local .git Directory ---
echo "ℹ️ Changing to script directory: ${SCRIPT_DIR}"
if ! cd "$SCRIPT_DIR"; then
    echo "❌ Failed to change directory to ${SCRIPT_DIR}" >&2
    exit 1
fi

echo "ℹ️ Deleting local '.git' directory..."
if [ -d ".git" ]; then
    if rm -rf .git; then
        echo "✅ Local '.git' directory deleted successfully."
    else
        echo "❌ Failed to delete local '.git' directory." >&2
        exit 1
    fi
else
    echo "ℹ️ Local '.git' directory not found. Nothing to delete."
fi

echo "🎉 Reset complete. Ready for initial upload test."

exit 0
