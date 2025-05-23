#!/usr/bin/env bash
# PRF-SUPAGROK-TEST-RESET-2025-05-03-C — Handle Missing Scope Error
# Directive: PRF-MODIFY-SCRIPT-2025-05-03-C
# UUID: 6789abcd-ef01-2345-6789-abcdef012345 # Example UUID, replace if needed
# Timestamp: 2025-05-03T10:00:00Z # Example timestamp

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
DELETE_STDERR=$(gh repo delete "${TARGET_REPO}" --yes 2>&1)
DELETE_EXIT_CODE=$?
# Re-enable exit on error
set -e

# Check exit code and stderr content
if [[ ${DELETE_EXIT_CODE} -eq 0 ]]; then
    echo "✅ Remote repository '${TARGET_REPO}' deleted successfully."
elif echo "$DELETE_STDERR" | grep -q -e "delete_repo scope" -e "HTTP 403"; then
    # Specific error for missing scope
    echo "❌ Failed to delete remote repository '${TARGET_REPO}'. Exit code: ${DELETE_EXIT_CODE}." >&2
    echo "   Reason: The currently authenticated 'gh' token lacks the required 'delete_repo' scope." >&2
    echo "   Stderr: $DELETE_STDERR" >&2
    exit 1 # Use a consistent exit code for this failure
elif ! gh repo view "${TARGET_REPO}" &> /dev/null; then
    # If delete failed but repo doesn't exist anyway, consider it a success for reset purposes
    echo "ℹ️ Remote repository '${TARGET_REPO}' not found or delete completed despite non-zero exit (${DELETE_EXIT_CODE}). Proceeding..."
else
    # If delete failed for some other reason and the repo still exists
    echo "❌ Failed to delete remote repository '${TARGET_REPO}' for an unknown reason. Exit code: ${DELETE_EXIT_CODE}." >&2
    echo "   Stderr: $DELETE_STDERR" >&2
    exit ${DELETE_EXIT_CODE}
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
