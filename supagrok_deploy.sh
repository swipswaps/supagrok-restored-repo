#!/usr/bin/env bash
# SUPAGROK One-Shot PRF-Compliant Deployment Script

set -euo pipefail

# --- CONFIGURABLES ---
REPO_DIR="$HOME/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo"
IONOS_USER="supagrok"
IONOS_HOST="67.217.243.191"
IONOS_REMOTE_DIR="~/supagrok-tipiservice"
SETUP_SCRIPT="setup_supagrok_services.sh"
GIT_BRANCH="main"

cd "$REPO_DIR"

echo "🔄 [SUPAGROK] Adding and committing all changes..."
git add .
git commit -m "Automated SUPAGROK deploy $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit."

echo "⬆️ [SUPAGROK] Pushing to GitHub..."
git push origin "$GIT_BRANCH"

echo "🔐 [SUPAGROK] Connecting to IONOS and deploying..."
ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${IONOS_USER}@${IONOS_HOST}" bash <<EOF
  set -euo pipefail
  cd ${IONOS_REMOTE_DIR}
  echo "🔄 [IONOS] Pulling latest code from GitHub..."
  git pull origin ${GIT_BRANCH}
  echo "🚀 [IONOS] Running service setup..."
  chmod +x ${SETUP_SCRIPT}
  ./${SETUP_SCRIPT}
EOF

echo "🎉 [SUPAGROK] Full deployment and service setup complete!"
