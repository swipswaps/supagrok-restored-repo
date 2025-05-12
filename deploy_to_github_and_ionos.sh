#!/usr/bin/env bash
# Script to push changes to GitHub and deploy to IONOS server

set -euo pipefail

# --- CONFIGURABLES ---
IONOS_USER="supagrok"
IONOS_HOST="67.217.243.191"
IONOS_REMOTE_DIR="~/supagrok-tipiservice"
GIT_BRANCH="main"

# Paths to modular scripts that will be transferred and executed on IONOS
SCRIPT_FILES=(
  "add_core_services.sh"
  "add_gateway_services.sh"
  "add_ui_services.sh"
  "add_performance_services.sh"
  "add_custom_services.sh"
  "deploy_all.sh"
  "MODULAR_SETUP_README.md"
  "DEPLOYMENT_README.md"
)

echo "🔄 [SUPAGROK] Adding and committing all changes..."
git add .
git commit -m "Automated SUPAGROK deploy with modular services $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit."

echo "⬆️ [SUPAGROK] Pushing to GitHub..."
git push origin "$GIT_BRANCH"

echo "🔐 [SUPAGROK] Connecting to IONOS and deploying..."
ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${IONOS_USER}@${IONOS_HOST}" bash <<EOF
  set -euo pipefail
  cd ${IONOS_REMOTE_DIR}
  
  # Ensure all files and directories have the correct permissions
  echo "🔒 [IONOS] Ensuring proper permissions on all files and directories..."
  sudo find . -type f -exec chmod 644 {} \;
  sudo find . -type d -exec chmod 755 {} \;
  
  echo "⚠️  Forcing discard of all local changes to match GitHub (PRF best practice)..."
  
  # Check if the repo is clean and has no untracked files
  if ! git diff-index --quiet HEAD -- || [ -n "\$(git ls-files --exclude-standard --others)" ]; then
    # Stash changes instead of hard reset to avoid permission errors
    git stash --include-untracked || true
    git clean -fd || true
  fi
  
  echo "🔄 [IONOS] Pulling latest code from GitHub..."
  git fetch origin
  git reset --hard origin/${GIT_BRANCH}
EOF

# Transfer our modular deployment scripts to IONOS
echo "📤 [SUPAGROK] Transferring modular deployment scripts to IONOS..."
for script in "${SCRIPT_FILES[@]}"; do
  if [ -f "$script" ]; then
    echo "Transferring $script..."
    scp "$script" "${IONOS_USER}@${IONOS_HOST}:${IONOS_REMOTE_DIR}/"
    ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${IONOS_USER}@${IONOS_HOST}" "sudo chmod +x ${IONOS_REMOTE_DIR}/${script} 2>/dev/null || true"
  else
    echo "⚠️ Warning: Script file $script not found locally. Skipping transfer."
  fi
done

# Create directories with proper permissions
echo "📂 [IONOS] Creating necessary directories on IONOS..."
ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${IONOS_USER}@${IONOS_HOST}" bash <<EOF
  set -euo pipefail
  
  # Create directory function with proper permissions
  create_dir() {
    sudo mkdir -p "\$1" 2>/dev/null || true
    sudo chmod 755 "\$1" 2>/dev/null || true
  }
  
  # Create all required directories
  create_dir ${IONOS_REMOTE_DIR}/volumes/db/data
  create_dir ${IONOS_REMOTE_DIR}/volumes/logs
  create_dir ${IONOS_REMOTE_DIR}/volumes/storage
  create_dir ${IONOS_REMOTE_DIR}/volumes/functions
  create_dir ${IONOS_REMOTE_DIR}/volumes/kong
  create_dir ${IONOS_REMOTE_DIR}/volumes/pgbouncer
  create_dir ${IONOS_REMOTE_DIR}/volumes/timescaledb/data
  create_dir ${IONOS_REMOTE_DIR}/volumes/d3_plotter
  create_dir ${IONOS_REMOTE_DIR}/volumes/tipiservice
  
  echo "✅ Directories created with proper permissions"
EOF

# Transfer configuration files with appropriate permissions
if [ -f "volumes/logs/vector.yml" ]; then
  echo "📤 [SUPAGROK] Transferring vector.yml configuration..."
  # First ensure target directory exists and has correct permissions
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${IONOS_USER}@${IONOS_HOST}" "sudo mkdir -p ${IONOS_REMOTE_DIR}/volumes/logs && sudo chmod 755 ${IONOS_REMOTE_DIR}/volumes/logs"
  scp "volumes/logs/vector.yml" "${IONOS_USER}@${IONOS_HOST}:${IONOS_REMOTE_DIR}/volumes/logs/"
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${IONOS_USER}@${IONOS_HOST}" "sudo chmod 644 ${IONOS_REMOTE_DIR}/volumes/logs/vector.yml"
fi

if [ -f "volumes/db/postgresql.conf" ]; then
  echo "📤 [SUPAGROK] Transferring postgresql.conf configuration..."
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${IONOS_USER}@${IONOS_HOST}" "sudo mkdir -p ${IONOS_REMOTE_DIR}/volumes/db && sudo chmod 755 ${IONOS_REMOTE_DIR}/volumes/db"
  scp "volumes/db/postgresql.conf" "${IONOS_USER}@${IONOS_HOST}:${IONOS_REMOTE_DIR}/volumes/db/"
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${IONOS_USER}@${IONOS_HOST}" "sudo chmod 644 ${IONOS_REMOTE_DIR}/volumes/db/postgresql.conf"
fi

# Transfer the .env file if it exists
if [ -f ".env" ] && [[ ! ".env" == *"template"* ]]; then
  echo "📤 [SUPAGROK] Transferring .env configuration (contains sensitive data)..."
  scp ".env" "${IONOS_USER}@${IONOS_HOST}:${IONOS_REMOTE_DIR}/"
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${IONOS_USER}@${IONOS_HOST}" "sudo chmod 600 ${IONOS_REMOTE_DIR}/.env"
else
  echo "⚠️ Warning: .env file not found or is a template. You may need to manually configure environment variables on IONOS."
fi

# Deploy the services
echo "🚀 [IONOS] Deploying Supabase services on IONOS..."
ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${IONOS_USER}@${IONOS_HOST}" bash <<EOF
  set -euo pipefail
  cd ${IONOS_REMOTE_DIR}
  
  # Check if Docker and Docker Compose are installed
  if ! command -v docker &>/dev/null; then
    echo "❌ Docker not installed. Please install Docker manually or contact administrator."
    exit 1
  fi
  
  if ! command -v docker-compose &>/dev/null; then
    echo "❌ Docker Compose not installed. Please install Docker Compose manually or contact administrator."
    exit 1
  fi
  
  # Ensure all script files are executable
  sudo find . -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
  
  # Run the modular deployment script
  echo "🚀 Starting Supabase deployment with modular approach..."
  cd ${IONOS_REMOTE_DIR}
  
  # Run deploy_all script if it exists and is executable
  if [ -x "./deploy_all.sh" ]; then
    ./deploy_all.sh
  else
    echo "⚠️ deploy_all.sh not found or not executable. Trying individual scripts..."
    
    # Try to run the core services script
    if [ -x "./add_core_services.sh" ]; then
      ./add_core_services.sh
    else
      echo "❌ Failed to find executable deployment scripts. Please check the transferred files."
      exit 1
    fi
  fi
EOF

echo "🎉 [SUPAGROK] Full deployment to GitHub and IONOS complete!"
echo "🌐 Access your Supabase studio at: http://${IONOS_HOST}:8000"
echo "🌐 Access your TIPI service at: http://${IONOS_HOST}:7000"