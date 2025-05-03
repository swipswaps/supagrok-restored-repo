#!/usr/bin/env bash
# PRF-SUPAGROK-GITHUB-SYNC-2025-05-03-G — Separate Create and Verbose Push for GitHub Repo
# Directive: PRF-MODIFY-SCRIPT-2025-05-03-G
# UUID: 23456789-abcd-ef01-2345-6789abcdef01 # Example UUID, replace if needed
# Timestamp: 2025-05-03T06:00:00Z # Example timestamp

# --- Argument Validation ---
# Ensure the target repository argument is provided
: ${1?"Usage: $0 <owner/repo>"}
TARGET_REPO="$1"
# --- Configuration ---
# Set desired visibility for new repositories ('public', 'private', 'internal')
NEW_REPO_VISIBILITY="public"
# Construct the expected HTTPS URL (adjust if using SSH)
REPO_URL="https://github.com/${TARGET_REPO}.git"

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
# Only commit if there are staged changes to avoid error on empty commit
if ! git diff --staged --quiet; then
    if git commit -m "Automated commit from SupaGrok Script Runner $(date '+%Y-%m-%d %H:%M:%S %Z')"; then
        echo "✅ Changes committed."
    else
        echo "⚠️ git commit command failed unexpectedly." >&2
        # Optionally exit here depending on desired strictness
        exit 1 # Exit if commit fails for safety
    fi
else
    echo "ℹ️ No changes staged to commit."
fi


echo "ℹ️ Determining current branch..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
if [ -z "$CURRENT_BRANCH" ]; then
    echo "❌ Could not determine current branch, defaulting to 'main'." >&2
    CURRENT_BRANCH="main"
fi
echo "✅ Current branch is '${CURRENT_BRANCH}'."

# --- Conditional GitHub Create/Push or Sync ---
echo "ℹ️ Checking if remote repository '${TARGET_REPO}' exists..."
if gh repo view "${TARGET_REPO}" &> /dev/null; then
    # --- Repository Exists - Perform Sync ---
    echo "✅ Remote repository found. Attempting to sync..."
    # Ensure origin URL is correct before syncing, in case it was changed manually
    echo "ℹ️ Verifying 'origin' remote URL points to ${REPO_URL}..."
    if git remote | grep -q '^origin$'; then
        CURRENT_ORIGIN_URL=$(git remote get-url origin)
        if [[ "${CURRENT_ORIGIN_URL}" != "${REPO_URL}" ]]; then
            echo "⚠️ 'origin' remote URL is incorrect (${CURRENT_ORIGIN_URL}). Updating to ${REPO_URL}..."
            if ! git remote set-url origin "${REPO_URL}"; then
                 echo "❌ Failed to update 'origin' remote URL before sync." >&2
                 exit 1
            fi
            echo "✅ Updated 'origin' remote URL."
        else
            echo "✅ 'origin' remote URL is correct."
        fi
    else
        echo "⚠️ 'origin' remote not found. Adding it before sync..."
         if ! git remote add origin "${REPO_URL}"; then
            echo "❌ Failed to add 'origin' remote before sync." >&2
            exit 1
        fi
        echo "✅ Added 'origin' remote."
    fi

    # Now perform the sync
    if gh repo sync "${TARGET_REPO}" --source "${CURRENT_BRANCH}" --branch "${CURRENT_BRANCH}"; then
        echo "✅ Repository synced successfully to branch '${CURRENT_BRANCH}' on remote '${TARGET_REPO}'."
    else
        GH_EXIT_CODE=$?
        echo "❌ Failed to sync existing repository '${TARGET_REPO}' with GitHub using 'gh repo sync'. Exit code: ${GH_EXIT_CODE}" >&2
        if [[ ${GH_EXIT_CODE} -eq 1 ]]; then
            echo "ℹ️ Common causes for sync failure include:" >&2
            echo "   - Local branch '${CURRENT_BRANCH}' has diverged significantly from the remote (fetch/merge needed?)." >&2
            echo "   - Network issues connecting to GitHub." >&2
        fi
        exit ${GH_EXIT_CODE}
    fi
else
    # --- Repository Does Not Exist - Create, Set Remote, Push Verbose ---
    echo "ℹ️ Remote repository '${TARGET_REPO}' not found or inaccessible. Attempting to create..."

    # 1. Create the repository structure on GitHub (non-interactively, no push yet)
    # Use --source . to include local files in the creation context, even though push is separate
    if gh repo create "${TARGET_REPO}" --source . "--${NEW_REPO_VISIBILITY}" < /dev/null; then
        echo "✅ Repository structure '${TARGET_REPO}' created successfully on GitHub."
    else
        GH_EXIT_CODE=$?
        echo "❌ Failed to create repository structure '${TARGET_REPO}' with GitHub using 'gh repo create'. Exit code: ${GH_EXIT_CODE}" >&2
         if [[ ${GH_EXIT_CODE} -eq 1 ]]; then
            echo "ℹ️ Common causes for create failure include:" >&2
            echo "   - Repository name '${TARGET_REPO}' already exists but is inaccessible/private." >&2
            echo "   - Insufficient permissions to create repositories." >&2
            echo "   - Network issues." >&2
        fi
        exit ${GH_EXIT_CODE}
    fi

    # 2. Set the local 'origin' remote URL
    echo "ℹ️ Setting up 'origin' remote to point to ${REPO_URL}..."
    if git remote | grep -q '^origin$'; then
        echo "ℹ️ Updating existing 'origin' remote URL..."
        if git remote set-url origin "${REPO_URL}"; then
             echo "✅ Updated 'origin' remote URL."
        else
             echo "❌ Failed to update 'origin' remote URL." >&2
             exit 1
        fi
    else
        echo "ℹ️ Adding 'origin' remote..."
        if git remote add origin "${REPO_URL}"; then
            echo "✅ Added 'origin' remote."
        else
            echo "❌ Failed to add 'origin' remote." >&2
            exit 1
        fi
    fi

    # 3. Push the current branch with progress and verbosity
    echo "ℹ️ Pushing branch '${CURRENT_BRANCH}' to new repository 'origin' with progress..."
    # Use -u to set upstream for the current branch
    if git push --verbose --progress -u origin "${CURRENT_BRANCH}"; then
        echo "✅ Branch '${CURRENT_BRANCH}' pushed successfully to new repository."
    else
        GIT_EXIT_CODE=$?
        echo "❌ Failed to push branch '${CURRENT_BRANCH}' to 'origin'. Exit code: ${GIT_EXIT_CODE}" >&2
        echo "ℹ️ Common causes for push failure include:" >&2
        echo "   - Authentication issues (check credential helper or SSH keys)." >&2
        echo "   - Network connectivity problems." >&2
        echo "   - Large commit size timing out." >&2
        exit ${GIT_EXIT_CODE}
    fi
fi

echo "🎉 GitHub operation completed successfully for ${TARGET_REPO}."

exit 0
