#!/bin/bash
# PRF-SUPAGROK-SERVER-FIX-V1.0
# This script is run on the remote server to fix Supagrok service issues.

set -e # Exit immediately if a command exits with a non-zero status.

APP_DIR="/home/supagrok/supagrok-tipiservice" # Standardized path on the server
PORT="8000"
CONTAINER_NAME="supagrok_snapshot_service_container"
SERVICE_NAME="supagrok-snapshot-service" # As in docker-compose.yml

log_remote() {
    echo "🌀 [REMOTE] $1"
}

log_remote "Starting Supagrok Server Fix Script..."

# 0. Set DEBIAN_FRONTEND to noninteractive to prevent prompts during apt operations
export DEBIAN_FRONTEND=noninteractive

# 1. Ensure Docker service is running
log_remote "Ensuring Docker service is running..."
if ! sudo systemctl is-active --quiet docker; then
    log_remote "Docker service is not active. Attempting to start..."
    sudo systemctl start docker
    sleep 5 # Give it a moment to start
    if ! sudo systemctl is-active --quiet docker; then
        log_remote "❌ [REMOTE] Failed to start Docker service. Please check Docker installation."
        exit 1
    fi
    log_remote "✅ [REMOTE] Docker service started."
else
    log_remote "✅ [REMOTE] Docker service is active."
fi

# 2. Ensure UFW is configured (if active)
log_remote "Checking UFW status..."
if sudo ufw status | grep -q "Status: active"; then
    log_remote "UFW is active. Ensuring port $PORT is allowed..."
    if sudo ufw status | grep -q "$PORT/tcp.*ALLOW"; then
        log_remote "✅ [REMOTE] Port $PORT/tcp is already allowed in UFW."
    else
        log_remote "Port $PORT/tcp is not allowed. Adding rule..."
        sudo ufw allow $PORT/tcp
        # sudo ufw reload # Reload might disconnect SSH if not careful, often rules apply immediately or on next restart
        log_remote "✅ [REMOTE] UFW rule for port $PORT/tcp added. You might need to reload UFW manually if changes don't take effect."
    fi
else
    log_remote "UFW is inactive or not installed. Skipping UFW configuration."
fi

# 3. Navigate to the application directory
log_remote "Changing to application directory: $APP_DIR"
if [ ! -d "$APP_DIR" ]; then
    log_remote "❌ [REMOTE] Application directory $APP_DIR does not exist. Please ensure the service files are present."
    # Attempt to create it if it's missing, assuming files will be placed there by another process (e.g., scp)
    # This part is tricky as the fix script itself is transferred, but other app files might not be.
    # For now, we'll assume the supagrok_master_launcher.py or manual setup has created this.
    # If not, the docker-compose will fail anyway.
    log_remote "Please ensure the application code (Dockerfile, supagrok_snapshot_worker.py, requirements.txt) is in $APP_DIR."
    # exit 1 # Commenting out exit to allow compose to potentially create it if it's just the base dir
fi
mkdir -p "$APP_DIR" # Ensure it exists
cd "$APP_DIR"

# 4. Ensure docker-compose.yml is present and configured for host networking
log_remote "Ensuring docker-compose.yml is configured for host networking..."
COMPOSE_FILE="docker-compose.yml"

# Create a backup if it exists
if [ -f "$COMPOSE_FILE" ]; then
    cp "$COMPOSE_FILE" "${COMPOSE_FILE}.bak.$(date +%s)"
    log_remote "Backed up existing $COMPOSE_FILE to ${COMPOSE_FILE}.bak.*"
fi

log_remote "Creating/Overwriting $COMPOSE_FILE with host networking configuration."
cat << EOF > "$COMPOSE_FILE"
version: '3.9'
services:
  ${SERVICE_NAME}:
    image: supagrok/snapshot-tipiservice:local
    container_name: ${CONTAINER_NAME}
    network_mode: "host" # Key change for direct port access
    volumes:
      - ./data/source:/app/data/source
      - ./data/output:/app/data/output
    environment:
      GPG_KEY_ID: "tipi-backup@supagrok.io" # Default, can be overridden by .env file
      PYTHONUNBUFFERED: '1'
      # GPG_PASSPHRASE should be set via .env file or passed directly to the container if secure
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:${PORT}/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    build:
      context: .
      dockerfile: Dockerfile
EOF
log_remote "✅ [REMOTE] $COMPOSE_FILE configured for host networking."
log_remote "⚠️ [REMOTE] IMPORTANT: Ensure GPG_PASSPHRASE is set for the service, typically via a .env file in $APP_DIR or as an environment variable for the user running Docker."

# Ensure data directories exist (Docker might create them, but good to be sure)
mkdir -p ./data/source
mkdir -p ./data/output
# Attempt to set permissions if running as root, for the supagrok user
if [ "$(id -u)" = "0" ] && id "supagrok" &>/dev/null; then
    log_remote "Running as root, ensuring supagrok user owns ./data"
    chown -R supagrok:supagrok ./data || log_remote "⚠️ [REMOTE] Could not chown ./data directory."
fi


# 5. Stop and remove the specific container if it exists
log_remote "Checking for existing container '$CONTAINER_NAME'..."
if sudo docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}$"; then
    log_remote "Container '$CONTAINER_NAME' found. Stopping and removing..."
    sudo docker stop "$CONTAINER_NAME" || log_remote "⚠️ [REMOTE] Could not stop container (maybe already stopped)."
    sudo docker rm -f "$CONTAINER_NAME" || log_remote "⚠️ [REMOTE] Could not remove container (maybe already removed)."
    log_remote "✅ [REMOTE] Existing container '$CONTAINER_NAME' removed."
else
    log_remote "No existing container named '$CONTAINER_NAME' found."
fi

# 6. Restart the service using docker-compose
log_remote "Starting/Restarting Supagrok service with docker-compose..."
# Using -p to define a project name helps isolate this deployment's resources
if sudo docker-compose -p supagrok -f "$COMPOSE_FILE" up -d --build --force-recreate --remove-orphans; then
    log_remote "✅ [REMOTE] Docker Compose 'up' command successful."
else
    log_remote "❌ [REMOTE] Docker Compose 'up' command failed. Displaying logs:"
    sudo docker-compose -p supagrok -f "$COMPOSE_FILE" logs --tail=50 "$SERVICE_NAME" || log_remote "⚠️ [REMOTE] Could not get compose logs."
    exit 1
fi

# 7. Verify service is running locally
log_remote "Verifying service locally (waiting up to 30 seconds)..."
for i in {1..6}; do
    if curl --fail --silent http://localhost:$PORT/health; then
        log_remote "✅ [REMOTE] Service is healthy locally."
        echo "✅ [REMOTE] Supagrok Server Fix completed successfully."
        exit 0
    fi
    log_remote "Waiting for service to become healthy... (attempt $i/6)"
    sleep 5
done

log_remote "❌ [REMOTE] Service did not become healthy locally after 30 seconds."
log_remote "Dumping last 50 lines of container logs:"
sudo docker logs "$CONTAINER_NAME" --tail 50 || log_remote "⚠️ [REMOTE] Could not get logs for $CONTAINER_NAME."
exit 1
