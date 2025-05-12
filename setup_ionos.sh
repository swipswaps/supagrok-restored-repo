#!/bin/bash
# PRF-SUPAGROK-IONOS-SETUP-V1.0
# Purpose: Zero-complexity IONOS server setup with automatic file transfer

# Server details
SERVER_IP="67.217.243.191"
SERVER_USER="root"

echo "🔷 [STEP] Starting Supagrok IONOS server setup..."
echo "🔵 [INFO] This script will automatically set up your IONOS server at $SERVER_IP"

# Create temporary directory for files
TEMP_DIR=$(mktemp -d)
echo "🔵 [INFO] Created temporary directory: $TEMP_DIR"

# Create server setup script
cat > "$TEMP_DIR/server_setup.sh" << 'EOF'
#!/bin/bash
# PRF-SUPAGROK-SERVER-SETUP-V1.0

# Logging function
log() {
  local level=$1
  local msg=$2
  local icon="ℹ️"
  
  case $level in
    "INFO") icon="🔵";;
    "WARN") icon="⚠️";;
    "ERROR") icon="❌";;
    "SUCCESS") icon="✅";;
    "STEP") icon="🔷";;
  esac
  
  echo -e "$icon [$level] $msg"
}

# Variables
NEW_USER="supagrok"
SSH_PORT=22
SERVER_HOSTNAME="supagrok-server"

# Main setup process
log "STEP" "Starting server setup process..."

# Update system
log "INFO" "Updating system packages..."
apt update && apt upgrade -y

# Set hostname
log "INFO" "Setting hostname to $SERVER_HOSTNAME..."
hostnamectl set-hostname $SERVER_HOSTNAME

# Create user with sudo privileges
log "STEP" "Creating user $NEW_USER with sudo privileges..."
if id "$NEW_USER" &>/dev/null; then
  log "INFO" "User $NEW_USER already exists."
else
  useradd -m -s /bin/bash $NEW_USER
  echo "$NEW_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$NEW_USER
  chmod 0440 /etc/sudoers.d/$NEW_USER
  log "SUCCESS" "User $NEW_USER created with sudo privileges."
  
  # Set password for new user
  log "INFO" "Setting password for $NEW_USER..."
  echo -e "supagrok2025\nsupagrok2025" | passwd $NEW_USER
  log "SUCCESS" "Password set for $NEW_USER."
fi

# Configure SSH
log "STEP" "Configuring SSH..."
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
sed -i "s/#Port 22/Port $SSH_PORT/" /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Restart SSH service
log "INFO" "Restarting SSH service..."
systemctl restart sshd
log "SUCCESS" "SSH configured and restarted."

# Install essential packages
log "STEP" "Installing essential packages..."
apt install -y curl wget git python3 python3-pip ufw

# Configure firewall
log "STEP" "Configuring firewall..."
ufw allow $SSH_PORT/tcp
ufw allow 8000/tcp  # For Supagrok service
ufw --force enable
log "SUCCESS" "Firewall configured and enabled."

# Install Docker
log "STEP" "Installing Docker and Docker Compose..."
apt install -y apt-transport-https ca-certificates gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
usermod -aG docker $NEW_USER
log "SUCCESS" "Docker installed and user added to docker group."

# Create project directory
log "STEP" "Creating project directory..."
mkdir -p /home/$NEW_USER/supagrok-tipiservice
chown -R $NEW_USER:$NEW_USER /home/$NEW_USER/supagrok-tipiservice

# Copy deployment files
log "STEP" "Setting up Supagrok deployment files..."
cp -r /root/supagrok-files/* /home/$NEW_USER/supagrok-tipiservice/
chown -R $NEW_USER:$NEW_USER /home/$NEW_USER/supagrok-tipiservice/
chmod +x /home/$NEW_USER/supagrok-tipiservice/*.sh
log "SUCCESS" "Deployment files copied and permissions set."

# Summary
log "SUCCESS" "Server setup complete!"
log "INFO" "New user: $NEW_USER"
log "INFO" "Password: supagrok2025"
log "INFO" "SSH Port: $SSH_PORT"
log "INFO" "Next step: SSH to $NEW_USER@<server-ip> and run: cd ~/supagrok-tipiservice && ./deploy.sh"

exit 0
EOF

# Create deployment script
cat > "$TEMP_DIR/deploy.sh" << 'EOF'
#!/bin/bash
# PRF-SUPAGROK-DEPLOY-V1.0

# Logging function
log() {
  local level=$1
  local msg=$2
  local icon="ℹ️"
  
  case $level in
    "INFO") icon="🔵";;
    "WARN") icon="⚠️";;
    "ERROR") icon="❌";;
    "SUCCESS") icon="✅";;
    "STEP") icon="🔷";;
  esac
  
  echo -e "$icon [$level] $msg"
}

# Variables
PROJECT_DIR="$HOME/supagrok-tipiservice"
DATA_DIR="$PROJECT_DIR/data"
SOURCE_DIR="$DATA_DIR/source"
OUTPUT_DIR="$DATA_DIR/output"

# Main deployment process
log "STEP" "Starting Supagrok deployment process..."

# Create necessary directories
log "INFO" "Creating data directories..."
mkdir -p "$SOURCE_DIR" "$OUTPUT_DIR"

# Create test file
echo "This is a test file for snapshot created by the deployment script." > "$SOURCE_DIR/test_file.txt"
log "SUCCESS" "Data directories and test file created."

# Build and start the service
log "STEP" "Building and starting Supagrok service..."
cd "$PROJECT_DIR"
docker-compose up -d --build
log "SUCCESS" "Supagrok service started!"

# Check service status
log "STEP" "Checking service status..."
sleep 5
if curl -s http://localhost:8000/health | grep -q "healthy"; then
  log "SUCCESS" "Supagrok service is running and healthy!"
  log "INFO" "You can access the service at: http://<server-ip>:8000"
else
  log "WARN" "Service may not be fully started yet. Check status with: docker ps"
  log "INFO" "You can check logs with: docker logs supagrok_snapshot_service_container"
fi

exit 0
EOF

# Create docker-compose.yml
cat > "$TEMP_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  supagrok-snapshot-service:
    container_name: supagrok_snapshot_service_container
    build: .
    image: supagrok/snapshot-tipiservice:local
    ports:
      - "8000:8000"
    volumes:
      - ./data/source:/data/source
      - ./data/output:/data/output
    restart: unless-stopped
EOF

# Create Dockerfile
cat > "$TEMP_DIR/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends gnupg tar curl procps lsof && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY supagrok_snapshot_worker.py /app/snapshot.py

EXPOSE 8000

CMD ["uvicorn", "snapshot:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create requirements.txt
cat > "$TEMP_DIR/requirements.txt" << 'EOF'
fastapi==0.103.1
uvicorn==0.23.2
python-multipart==0.0.6
python-gnupg==0.5.1
EOF

# Create FastAPI application
cat > "$TEMP_DIR/supagrok_snapshot_worker.py" << 'EOF'
#!/usr/bin/env python3
# PRF-SUPAGROK-V3-SNAPSHOT-WORKER

import os
import time
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse

app = FastAPI(title="Supagrok Snapshot Service")

# Directories
SOURCE_DIR = "/data/source"
OUTPUT_DIR = "/data/output"

# Ensure directories exist
os.makedirs(SOURCE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Background task for snapshot processing
def process_snapshot(filename: str):
    """Process a snapshot in the background."""
    time.sleep(2)  # Simulate processing time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"snapshot_{timestamp}.tar.gz"
    snapshot_path = os.path.join(OUTPUT_DIR, snapshot_name)
    
    # Create a simple tar.gz archive
    shutil.make_archive(
        os.path.join(OUTPUT_DIR, f"snapshot_{timestamp}"),
        'gztar',
        SOURCE_DIR
    )
    
    print(f"Snapshot created: {snapshot_path}")
    return snapshot_path

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Supagrok Snapshot Tipi",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/snapshot")
async def create_snapshot(background_tasks: BackgroundTasks):
    """Trigger a new snapshot creation."""
    background_tasks.add_task(process_snapshot, "snapshot")
    return {"status": "processing", "message": "Snapshot creation started"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file to the source directory."""
    file_path = os.path.join(SOURCE_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": file.filename, "status": "uploaded"}

@app.get("/list")
async def list_snapshots():
    """List all available snapshots."""
    snapshots = []
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith(".tar.gz"):
            file_path = os.path.join(OUTPUT_DIR, filename)
            file_stats = os.stat(file_path)
            snapshots.append({
                "filename": filename,
                "size_bytes": file_stats.st_size,
                "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat()
            })
    
    return {"snapshots": snapshots}
EOF

# Make scripts executable
chmod +x "$TEMP_DIR/server_setup.sh"
chmod +x "$TEMP_DIR/deploy.sh"

echo "🔷 [STEP] Transferring files to server..."
echo "🔵 [INFO] You will be prompted for the root password"

# Create directory on server
ssh -o StrictHostKeyChecking=accept-new $SERVER_USER@$SERVER_IP "mkdir -p /root/supagrok-files"

# Transfer all files to server
scp -r "$TEMP_DIR"/* $SERVER_USER@$SERVER_IP:/root/supagrok-files/

echo "🔷 [STEP] Running server setup script remotely..."
ssh $SERVER_USER@$SERVER_IP "bash -c 'chmod +x /root/supagrok-files/server_setup.sh && /root/supagrok-files/server_setup.sh'"

echo "✅ [SUCCESS] Setup complete!"
echo "🔵 [INFO] To access your Supagrok service:"
echo "  1. SSH to the server: ssh supagrok@$SERVER_IP (password: supagrok2025)"
echo "  2. Run the deployment: cd ~/supagrok-tipiservice && ./deploy.sh"
echo "  3. Access the service at: http://$SERVER_IP:8000"

# Clean up temporary directory
rm -rf "$TEMP_DIR"