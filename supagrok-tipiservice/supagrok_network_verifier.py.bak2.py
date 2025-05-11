
#!/usr/bin/env python3
# PRF-SUPAGROK-V3-NETWORK-VERIFIER-V3.1
# UUID: 5e4d3c2b-1a9f-8b7e-6d5c-4f3e2d1c0b9a
# Path: /home/owner/supagrok-tipiservice/supagrok_network_verifier.py
# Purpose: Verify network connectivity to Supagrok Snapshot Service
# PRF Relevance: P01, P07, P16, P18, P26, P29, P30

import sys
import time
import urllib.request
import socket
import json
import argparse
import subprocess
import os
import tempfile
from datetime import datetime
from pathlib import Path
import threading
import ipaddress
import signal

# --- Configuration ---
DEFAULT_PORT = 8000
HEALTH_TIMEOUT = 15  # seconds
WS_TIMEOUT = 10  # seconds
SSH_OPTIONS = ["-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes"]
MAX_RETRIES = 3  # Number of fix attempts before giving up
VERSION = "3.1"

# --- Logging ---
def log(level, msg):
    """PRF-P07: Centralized logging with clear indicators."""
    icon = {"INFO": "🌀", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅", "STEP": "🛠️", "DEBUG": "🔍"}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} {icon.get(level.upper(), 'ℹ️')} [{level.upper()}] {msg}")

def check_dependencies():
    """PRF-P04: Check for required Python packages and install if missing."""
    try:
        import websocket
        return True
    except ImportError:
        log("INFO", "WebSocket package not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"])
            log("SUCCESS", "Successfully installed websocket-client package.")
            import websocket
            globals()["websocket"] = websocket
            return True
        except Exception as e:
            log("ERROR", f"Failed to install websocket-client: {e}")
            log("INFO", "Please install manually with: pip install websocket-client")
            return False

def validate_ip_address(ip_str):
    """PRF-P12: Validate IP address format."""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def validate_port(port):
    """PRF-P12: Validate port number."""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except ValueError:
        return False

def setup_ssh_key_auth(server_ip, username=None):
    """PRF-P18: Set up SSH key authentication to reduce password prompts."""
    log("STEP", "Setting up SSH key authentication...")
    
    # Validate IP address
    if not validate_ip_address(server_ip):
        log("ERROR", f"Invalid IP address: {server_ip}")
        return False
    
    # Determine SSH target
    ssh_target = f"{username}@{server_ip}" if username else server_ip
    
    # Check if SSH key exists
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")
    if not os.path.exists(ssh_key_path):
        log("INFO", "SSH key not found. Generating a new key...")
        
        # Generate SSH key
        keygen_cmd = ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", ssh_key_path, "-N", ""]
        try:
            subprocess.run(keygen_cmd, check=True, capture_output=True)
            log("SUCCESS", "SSH key generated successfully.")
        except subprocess.CalledProcessError as e:
            log("WARN", f"Failed to generate SSH key: {e}")
            return False
    
    # Test if we already have passwordless access
    test_cmd = ["ssh"] + SSH_OPTIONS + [ssh_target, "echo 'SSH key authentication test'"]
    test_result = subprocess.run(test_cmd, capture_output=True, text=True)
    
    if test_result.returncode == 0:
        log("SUCCESS", "SSH key authentication already working.")
        return True
    
    # Copy SSH key to remote server
    log("INFO", f"Copying SSH key to {ssh_target}...")
    
    copy_cmd = ["ssh-copy-id", "-o", "StrictHostKeyChecking=no", ssh_target]
    try:
        subprocess.run(copy_cmd, check=True, capture_output=True)
        log("SUCCESS", f"SSH key copied to {ssh_target}. Future connections should not require a password.")
        
        # Test passwordless connection
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
    """PRF-P26: Verify that the health endpoint is accessible."""
    log("STEP", f"Verifying health endpoint at http://{server_ip}:{port}/health...")
    
    # Validate inputs
    if not validate_ip_address(server_ip):
        log("ERROR", f"Invalid IP address: {server_ip}")
        return False
    
    if not validate_port(port):
        log("ERROR", f"Invalid port: {port}")
        return False
    
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
    """PRF-P26: Verify that the WebSocket endpoint is accessible."""
    # Ensure websocket module is available
    if not check_dependencies():
        log("ERROR", "WebSocket verification requires the websocket-client package.")
        log("INFO", "Please install with: pip install websocket-client")
        return False
    
    # Import websocket here to ensure it's available
    import websocket
    
    # Validate inputs
    if not validate_ip_address(server_ip):
        log("ERROR", f"Invalid IP address: {server_ip}")
        return False
    
    if not validate_port(port):
        log("ERROR", f"Invalid port: {port}")
        return False
    
    log("STEP", f"Verifying WebSocket endpoint at ws://{server_ip}:{port}/ws/snapshot...")
    
    url = f"ws://{server_ip}:{port}/ws/snapshot"
    log("INFO", f"Attempting to connect to {url}")
    
    connected = False
    message_received = False
    connection_error = None
    
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
        nonlocal connection_error
        log("ERROR", f"WebSocket error: {error}")
        connection_error = error
    
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
        
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Wait for the timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            if connected:
                log("SUCCESS", "WebSocket connection verified!")
                return True
            if connection_error:
                log("ERROR", f"WebSocket connection failed: {connection_error}")
                break
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
    """PRF-P26: Check if Docker is running on the remote server."""
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
    """PRF-P26: Check if the Supagrok container is running on the remote server."""
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
    """PRF-P26: Check if the port is listening on the remote server."""
    log("STEP", f"Checking if port {port} is listening on remote server...")
    
    # Validate port
    if not validate_port(port):
        log("ERROR", f"Invalid port: {port}")
        return False
    
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
    """PRF-P18: Fix connectivity issues on the remote server with minimal password prompts."""
    log("STEP", f"Attempting to fix connectivity issues on {server_ip}...")
    
    # Validate inputs
    if not validate_ip_address(server_ip):
        log("ERROR", f"Invalid IP address: {server_ip}")
        return False
    
    if not validate_port(port):
        log("ERROR", f"Invalid port: {port}")
        return False
    
    # Determine SSH target
    ssh_target = f"{username}@{server_ip}" if username else server_ip
    
    # Check Docker status first
    if not check_remote_docker_status(ssh_target):
        log("STEP", "Attempting to start Docker service...")
        subprocess.run(["ssh"] + SSH_OPTIONS + [ssh_target, "sudo systemctl start docker"], capture_output=True)
    
    # Create a temporary fix script
    fix_script_content = """#!/bin/bash
# PRF-SUPAGROK-V3-QUICK-FIX-V1.2
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
    echo "🌀 [INFO] docker-compose not found. Attempting to install..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ [SUCCESS] docker-compose installed."
fi

# Check if Supagrok container is running
if ! docker ps | grep -q supagrok_snapshot_service_container; then
    echo "🌀 [INFO] Supagrok container not found. Attempting to start..."
    docker-compose -f /etc/supagrok/docker-compose.yml up -d
    echo "✅ [SUCCESS] Supagrok container started."
else
    echo "🌀 [INFO] Supagrok container is already running."
fi

# Verify if the container is running
if ! docker ps | grep -q supagrok_snapshot_service_container; then
    echo "❌ [ERROR] Supagrok container failed to start. Please check the logs."
    return 1
fi

# Verify if the health endpoint is accessible
if ! curl -s http://localhost:8000/health; then
    echo "❌ [ERROR] Health endpoint not accessible. Please check the container logs."
    return 1
fi

echo "✅ [SUCCESS] Supagrok Quick Fix completed successfully! The service should now be accessible."
"""
    fix_script_path = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.sh')
    fix_script_path.write(fix_script_content)
    fix_script_path.close()
    
    # Set the script as executable
    subprocess.run(["ssh"] + SSH_OPTIONS + [ssh_target, f"chmod +x {fix_script_path.name}"])
    
    # Run the fix script on the remote server
    log("STEP", "Running fix script on remote server...")
    result = subprocess.run(["ssh"] + SSH_OPTIONS + [ssh_target, f"./{fix_script_path.name}"], capture_output=True, text=True)
    
    # Remove the temporary script file
    subprocess.run(["ssh"] + SSH_OPTIONS + [ssh_target, f"rm {fix_script_path.name}"])
    
    if result.returncode == 0:
        log("SUCCESS", "Connectivity issues fixed successfully! The service should now be accessible.")
        return True
    else:
        log("ERROR", "Failed to fix connectivity issues. Please check the logs for more information.")
        log("DEBUG", f"Output from fix script: {result.stdout}")
        log("DEBUG", f"Errors from fix script: {result.stderr}")
        return False

def main():
    """PRF-P01: Main function to handle command-line arguments and execute the network verification process."""
    parser = argparse.ArgumentParser(description="Supagrok Network Verifier")
    parser.add_argument("server_ip", help="IP address of the Supagrok server")
    parser.add_argument("-p", "--port", type=int, default=DEFAULT_PORT, help="Port number to connect to (default: 8000)")
    parser.add_argument("-u", "--username", help="SSH username for remote server (optional)")
    parser.add_argument("-f", "--fix", action="store_true", help="Attempt to fix connectivity issues if verification fails")

    args = parser.parse_args()

    log("INFO", f"Supagrok Network Verifier {VERSION} started! Checking connectivity to {args.server_ip}:{args.port}...")

    # Verify health endpoint
    if verify_health_endpoint(args.server_ip, args.port):
        log("SUCCESS", "Health endpoint is accessible! The service is running correctly.")
        return

    log("WARN", "Health endpoint is not accessible! Attempting to fix connectivity issues...")

    # Attempt to fix connectivity issues
    if args.fix:
        if fix_remote_connectivity(args.server_ip, args.port, args.username):
            log("SUCCESS", "Connectivity issues fixed! The service should now be accessible.")
            return
        else:
            log("ERROR", "Failed to fix connectivity issues. Please check the logs for more information.")
    else:
        log("INFO", "Connectivity issues detected! Use the -f option to attempt to fix them.")

if __name__ == "__main__":
    main()

