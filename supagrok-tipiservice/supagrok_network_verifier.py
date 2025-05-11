#!/usr/bin/env python3
# PRF-SUPAGROK-V3-NETWORK-VERIFIER-V3.0
# UUID: 5e4d3c2b-1a9f-8b7e-6d5c-4f3e-2d1c0b9a-fixed-v3
# Path: /home/owner/supagrok-tipiservice/supagrok_network_verifier.py
# Purpose: Verify network connectivity to Supagrok Snapshot Service, set up SSH, and apply fixes for common issues.
# PRF Relevance: P01, P07, P16, P18, P26, P29, P30, P31

import sys
import time
import urllib.request
import socket
import json
import argparse
import subprocess
import os
import tempfile
import signal # Added for signal handling
from datetime import datetime
from pathlib import Path
import threading # For WebSocket timeout
import platform # Used for OS-specific commands

# --- Configuration ---
DEFAULT_PORT = 8000
HEALTH_TIMEOUT = 15  # seconds
WS_TIMEOUT = 10  # seconds
SSH_OPTIONS = ["-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes"]
MAX_RETRIES = 3  # Number of fix attempts before giving up
VERSION = "3.0.3"
SCRIPT_UUID = "5e4d3c2b-1a9f-8b7e-6d5c-4f3e2d1c0b9a-fixed-v3"

# --- Logging ---
def log(level, msg):
    """PRF-P07, P13: Centralized logging with clear indicators."""
    icon = {"INFO": "🌀", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅", "STEP": "🛠️", "DEBUG": "🔍", "REPORT": "📊"}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} {icon.get(level.upper(), 'ℹ️')} [{level.upper()}] {msg}")

def check_dependencies():
    """Check for required Python packages and install if missing."""
    try:
        import websocket
        return True
    except ImportError:
        log("INFO", "WebSocket package not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"])
            log("SUCCESS", "Successfully installed websocket-client package.")
            import websocket
            return True
        except Exception as e:
            log("ERROR", f"Failed to install websocket-client: {e}")
            log("INFO", "Please install manually with: pip install websocket-client")
            return False

def setup_ssh_key_auth(server_ip, username=None):
    """Set up SSH key authentication to reduce password prompts."""
    log("STEP", "Setting up SSH key authentication...")
    ssh_target = f"{username}@{server_ip}" if username else server_ip
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

    if not os.path.exists(ssh_key_path):
        log("INFO", "SSH key not found. Generating a new key...")
        keygen_cmd = ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", ssh_key_path, "-N", ""]
        try:
            subprocess.run(keygen_cmd, check=True, capture_output=True)
            log("SUCCESS", "SSH key generated successfully.")
        except subprocess.CalledProcessError as e:
            log("WARN", f"Failed to generate SSH key: {e}")
            return False

    test_cmd = ["ssh"] + SSH_OPTIONS + [ssh_target, "echo 'SSH key authentication test'"]
    test_result = subprocess.run(test_cmd, capture_output=True, text=True)

    if test_result.returncode == 0:
        log("SUCCESS", "SSH key authentication already working.")
        return True

    log("INFO", f"Copying SSH key to {ssh_target}...")
    copy_cmd = ["ssh-copy-id", "-o", "StrictHostKeyChecking=no", ssh_target]
    try:
        subprocess.run(copy_cmd, check=True, capture_output=True)
        log("SUCCESS", f"SSH key copied to {ssh_target}.")
        test_cmd = ["ssh"] + SSH_OPTIONS + [ssh_target, "echo 'SSH key authentication successful'"]
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            log("SUCCESS", "Passwordless SSH connection verified.")
            return True
        else:
            log("WARN", "SSH key copied but passwordless connection failed. You may still be prompted for passwords.")
            return False
    except subprocess.CalledProcessError as e:
        log("WARN", f"Failed to copy SSH key: {e}")
        return False

def verify_health_endpoint(server_ip, port, timeout=HEALTH_TIMEOUT):
    """Verify that the health endpoint is accessible."""
    log("STEP", f"Verifying health endpoint at http://{server_ip}:{port}/health...")
    url = f"http://{server_ip}:{port}/health"
    log("INFO", f"Attempting to connect to {url}")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(url, timeout=5)
            if response.status == 200:
                data = response.read().decode('utf-8')
                log("SUCCESS", f"Health endpoint is accessible! Response: {data}")
                return True
            else:
                log("WARN", f"Health endpoint returned status code {response.status}. Retrying...")
        except Exception as e:
            log("INFO", f"Failed to access health endpoint: {e}. Retrying...")

        time.sleep(1)  # Wait before retrying

    log("ERROR", f"Failed to access the health endpoint after {timeout} seconds.")
    return False

def verify_websocket(server_ip, port, timeout=WS_TIMEOUT):
    """Verify that the WebSocket endpoint is accessible."""
    try:
        import websocket
    except ImportError:
        log("ERROR", "WebSocket verification requires the websocket-client package.")
        log("INFO", "Please install with: pip install websocket-client")
        return False

    log("STEP", f"Verifying WebSocket endpoint at ws://{server_ip}:{port}/ws/snapshot...")
    url = f"ws://{server_ip}:{port}/ws/snapshot"
    log("INFO", f"Attempting to connect to {url}")

    connected = False
    message_received = False

    def on_open(ws):
        nonlocal connected
        log("SUCCESS", "WebSocket connection established!")
        connected = True

    def on_message(ws, message):
        nonlocal message_received
        log("SUCCESS", f"Received message from WebSocket: {message}")
        message_received = True
        ws.close()

    def on_error(ws, error):
        log("ERROR", f"WebSocket error: {error}")

    def on_close(ws, close_status_code, close_msg):
        log("INFO", f"WebSocket connection closed. Status code: {close_status_code}, Message: {close_msg}")

    try:
        ws = websocket.WebSocketApp(
            url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        import threading
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # Wait for the timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            if connected:
                log("SUCCESS", "WebSocket connection verified!")
                return True
            time.sleep(0.5)

        ws.close()

        if connected:
            log("SUCCESS", "WebSocket connection verified!")
            return True
        else:
            log("ERROR", f"Failed to connect to WebSocket after {timeout} seconds.")
            return False
    except Exception as e:
        log("ERROR", f"Failed to test WebSocket connection: {e}")
        return False

def check_remote_docker_status(ssh_target):
    """Check if Docker is running on the remote server."""
    log("STEP", "Checking Docker status on remote server...")
    
    cmd = ["ssh"] + SSH_OPTIONS + [ssh_target, "sudo docker ps"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        log("SUCCESS", "Docker is running on remote server.")
        return True
    else:
        log("WARN", "Docker may not be running on remote server.")
        return False

def check_remote_container_status(ssh_target):
    """Check if the Supagrok container is running on the remote server."""
    log("STEP", "Checking Supagrok container status...")
    
    cmd = ["ssh"] + SSH_OPTIONS + [ssh_target, "sudo docker ps | grep supagrok_snapshot_service_container"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout.strip():
        log("SUCCESS", "Supagrok container is running.")
        return True
    else:
        log("WARN", "Supagrok container is not running.")
        return False

def check_remote_port_listening(ssh_target, port):
    """Check if the port is listening on the remote server."""
    log("STEP", f"Checking if port {port} is listening on remote server...")
    
    # Try netstat first
    cmd = ["ssh"] + SSH_OPTIONS + [ssh_target, f"sudo netstat -tuln | grep :{port}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout.strip():
        log("SUCCESS", f"Port {port} is listening on remote server (netstat).")
        return True
    
    # Try ss if netstat fails
    cmd = ["ssh"] + SSH_OPTIONS + [ssh_target, f"sudo ss -tuln | grep :{port}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout.strip():
        log("SUCCESS", f"Port {port} is listening on remote server (ss).")
        return True
    
    # Try lsof as a last resort
    cmd = ["ssh"] + SSH_OPTIONS + [ssh_target, f"sudo lsof -i :{port}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout.strip():
        log("SUCCESS", f"Port {port} is listening on remote server (lsof).")
        return True
    
    log("WARN", f"Port {port} is not listening on remote server.")
    return False

def fix_remote_connectivity(server_ip, port, username=None):
    """Fix connectivity issues on the remote server with minimal password prompts."""
    log("STEP", f"Attempting to fix connectivity issues on {server_ip}...")
    
    # Determine SSH target
    ssh_target = f"{username}@{server_ip}" if username else server_ip
    
    # Check Docker status first
    if not check_remote_docker_status(ssh_target):
        log("STEP", "Attempting to start Docker service...")
        subprocess.run(["ssh"] + SSH_OPTIONS + [ssh_target, "sudo systemctl start docker"], capture_output=True)
    
    # Create a temporary fix script
    fix_script_content = """#!/bin/bash
# PRF-SUPAGROK-V3-QUICK-FIX-V1.1
# Purpose: Quick fix for network connectivity issues

echo "🛠️ [STEP] Starting Supagrok Quick Fix..."

# Ensure Docker is running
echo "🌀 [INFO] Ensuring Docker is running..."
sudo systemctl start docker
sudo systemctl status docker --no-pager

# Ensure firewall allows port
if command -v firewall-cmd &> /dev/null; then
    echo "🌀 [INFO] Firewalld detected. Adding port rule..."
    sudo firewall-cmd --permanent --add-port=8000/tcp
    sudo firewall-cmd --reload
elif command -v ufw &> /dev/null; then
    echo "🌀 [INFO] UFW detected. Adding port rule..."
    sudo ufw allow 8000/tcp
fi

# Check if docker-compose exists
if ! command -v docker-compose &> /dev/null; then
    echo "🌀 [INFO] docker-compose not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y docker-compose
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y docker-compose
    elif command -v yum &> /dev/null; then
        sudo yum install -y docker-compose
    fi
fi

# Update docker-compose.yml to use host network
if [ -f docker-compose.yml ]; then
    echo "🌀 [INFO] Backing up docker-compose.yml..."
    cp docker-compose.yml docker-compose.yml.bak
    
    echo "🌀 [INFO] Updating docker-compose.yml to use host network..."
    cat > docker-compose.yml << 'EOF'
version: '3.9'
services:
  supagrok-snapshot-service:
    image: supagrok/snapshot-tipiservice:local
    container_name: supagrok_snapshot_service_container
    network_mode: "host"  # Use host networking instead of port mapping
    volumes:
      - ./data:/data
    environment:
      GPG_KEY_ID: tipi-backup@supagrok.io
      PYTHONUNBUFFERED: '1'
    restart: unless-stopped
    healthcheck:
      test:
        - CMD-SHELL
        - curl -f http://localhost:8000/health || exit 1
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    build: .
EOF
    echo "✅ [SUCCESS] docker-compose.yml updated."
fi

# Restart the service
echo "🛠️ [STEP] Restarting Docker service..."
sudo docker-compose down --remove-orphans
sudo docker-compose up -d --build

# Verify service is running
echo "🛠️ [STEP] Verifying service is running..."
sleep 5
sudo docker ps | grep supagrok_snapshot_service_container

# Check if port is listening
echo "🛠️ [STEP] Checking if port is listening..."
