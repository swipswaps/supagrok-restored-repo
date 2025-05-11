#!/usr/bin/env python3
# PRF-SUPAGROK-V3-NETWORK-DOCTOR-V1.0
# UUID: 5a4b3c2d-1e0f-9a8b-7c6d-5e4f3a2b1c0d
# Path: ./supagrok_network_doctor.py
# Purpose: One-shot script to diagnose and fix network issues for Supagrok Snapshot Tipi service.
# PRF Relevance: P01, P02, P03, P04, P05, P06, P07, P11, P12, P13, P14, P15, P16, P17, P18, P19

import os
import sys
import subprocess
import tempfile
import time
import socket
import getpass
from pathlib import Path
import argparse

# --- Configuration ---
REMOTE_SCRIPT_PATH = "/tmp/supagrok_network_fix.py"
APP_PORT = 8000

# --- Logging ---
def log(level, msg):
    """PRF-P07: Centralized logging with clear indicators."""
    icon = {"INFO": "🌀", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅", "STEP": "🛠️", "TEST": "🧪"}
    print(f"{icon.get(level.upper(), 'ℹ️')} [{level.upper()}] {msg}")

def run_local_command(command_parts, check=True, capture_output=False, text=True):
    """PRF-P16: Execute a command locally with proper error handling."""
    log("INFO", f"Executing locally: {' '.join(command_parts)}")
    try:
        process = subprocess.run(
            command_parts,
            check=check,
            capture_output=capture_output,
            text=text
        )
        return process
    except subprocess.CalledProcessError as e:
        stderr = e.stderr if e.stderr else ""
        log("ERROR", f"Command '{' '.join(command_parts)}' failed with exit code {e.returncode}.")
        if stderr: log("ERROR", f"Stderr:\n{stderr.strip()}")
        if check:
            raise
        return e
    except Exception as e:
        log("ERROR", f"An unexpected error occurred with command '{' '.join(command_parts)}': {e}")
        if check:
            raise
        return None

def run_remote_command(ssh_target, command, check=True):
    """PRF-P16: Execute a command on the remote server with proper error handling."""
    full_command = ["ssh", ssh_target, command]
    return run_local_command(full_command, check=check, capture_output=True, text=True)

def create_network_fix_script():
    """PRF-P01, P02: Create the network fix script content."""
    return '''#!/usr/bin/env python3
# PRF-SUPAGROK-V3-NETWORK-FIX-V1.0
# UUID: 7e9d2f8a-6b5c-4c3d-9e1f-8a7b6c5d4e3f
# Path: /tmp/supagrok_network_fix.py
# Purpose: One-shot script to fix network configuration for Supagrok Snapshot Tipi service

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path
import socket
import urllib.request
from datetime import datetime

# --- Configuration ---
COMPOSE_FILE_PATH = Path("docker-compose.yml")
APP_PORT = 8000
SERVICE_NAME_IN_COMPOSE = "supagrok-snapshot-service"
CONTAINER_NAME = "supagrok_snapshot_service_container"

# --- Logging ---
def log(level, msg):
    icon = {"INFO": "🌀", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅", "STEP": "🛠️"}
    print(f"{icon.get(level.upper(), 'ℹ️')} [{level.upper()}] {msg}")

# --- Command Execution Utility ---
def run_command(command_parts, check=True, capture_output=False, text=True, use_sudo=False):
    final_command = list(command_parts)
    if use_sudo and os.geteuid() != 0:
        final_command.insert(0, "sudo")

    log("INFO", f"Executing: {' '.join(final_command)}")
    try:
        process = subprocess.run(
            final_command,
            check=check,
            capture_output=capture_output,
            text=text
        )
        return process
    except subprocess.CalledProcessError as e:
        stderr = e.stderr if e.stderr else ""
        stdout = e.stdout if e.stdout else ""
        log("ERROR", f"Command '{' '.join(final_command)}' failed with exit code {e.returncode}.")
        if stdout: log("INFO", f"Stdout: {stdout.strip()}")
        if stderr: log("ERROR", f"Stderr: {stderr.strip()}")
        if check:
            raise
        return e
    except Exception as e:
        log("ERROR", f"An unexpected error occurred with command '{' '.join(final_command)}': {e}")
        if check:
            raise
        return None

def get_server_ip():
    """Get the server's public IP address."""
    log("STEP", "Determining server IP address...")
    
    # Try to get the IP from the network interface
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        log("SUCCESS", f"Detected server IP: {ip}")
        return ip
    except Exception as e:
        log("WARN", f"Could not determine IP via socket: {e}")
    
    # Fallback to using hostname
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip != "127.0.0.1":
            log("SUCCESS", f"Detected server IP via hostname: {ip}")
            return ip
    except Exception as e:
        log("WARN", f"Could not determine IP via hostname: {e}")
    
    # Last resort - try to use external service
    try:
        response = urllib.request.urlopen("https://api.ipify.org", timeout=5)
        ip = response.read().decode('utf-8')
        log("SUCCESS", f"Detected server IP via external service: {ip}")
        return ip
    except Exception as e:
        log("WARN", f"Could not determine IP via external service: {e}")
    
    log("WARN", "Could not automatically determine server IP. Using localhost for testing.")
    return "localhost"

def ensure_firewall_rules(port):
    """Check and update firewall rules to allow traffic on the specified port."""
    log("STEP", f"Ensuring firewall allows traffic on port {port}...")
    
    # Check UFW status if available
    try:
        ufw_cmd = ["ufw", "status"]
        result = run_command(ufw_cmd, check=True, capture_output=True, text=True, use_sudo=True)
        
        if "Status: inactive" in result.stdout:
            log("INFO", "UFW firewall is inactive.")
            return True
        
        log("INFO", "UFW firewall is active. Checking rules...")
        
        # Check if port is allowed
        if f"{port}/tcp" in result.stdout or f"{port}" in result.stdout:
            log("SUCCESS", f"Port {port} is already allowed in UFW.")
            return True
        else:
            log("WARN", f"Port {port} does not appear to be explicitly allowed in UFW. Adding rule...")
            
            # Add rule to allow port
            allow_cmd = ["ufw", "allow", f"{port}/tcp"]
            allow_result = run_command(allow_cmd, check=True, capture_output=True, text=True, use_sudo=True)
            
            # Reload UFW
            reload_cmd = ["ufw", "reload"]
            reload_result = run_command(reload_cmd, check=True, capture_output=True, text=True, use_sudo=True)
            
            log("SUCCESS", f"Added UFW rule to allow port {port}/tcp and reloaded firewall.")
            return True
    except Exception as e:
        log("WARN", f"Error checking or updating UFW: {e}")
    
    # Check iptables if available
    try:
        iptables_cmd = ["iptables", "-L", "-n"]
        result = run_command(iptables_cmd, check=True, capture_output=True, text=True, use_sudo=True)
        
        # This is a very basic check and might not catch all rules
        if f"tcp dpt:{port}" in result.stdout or "ACCEPT" in result.stdout:
            log("INFO", "iptables appears to have rules that might allow traffic.")
            return True
        else:
            log("WARN", f"Adding iptables rule to allow port {port}...")
            
            # Add rule to allow port
            add_cmd = ["iptables", "-A", "INPUT", "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"]
            add_result = run_command(add_cmd, check=True, capture_output=True, text=True, use_sudo=True)
            
            log("SUCCESS", f"Added iptables rule to allow port {port}.")
            return True
    except Exception as e:
        log("WARN", f"Error checking or updating iptables: {e}")
    
    log("WARN", f"Could not update firewall rules. Please manually ensure port {port} is allowed.")
    return False

def update_docker_compose_to_host_network():
    """Update docker-compose.yml to use host network mode."""
    log("STEP", "Updating docker-compose.yml to use host network mode...")
    
    if not COMPOSE_FILE_PATH.exists():
        log("ERROR", f"docker-compose.yml not found at {COMPOSE_FILE_PATH}. Please run this script from the supagrok-tipiservice directory.")
        return False
    
    # Create backup
    backup_path = COMPOSE_FILE_PATH.with_suffix('.yml.bak')
    shutil.copy2(COMPOSE_FILE_PATH, backup_path)
    log("INFO", f"Created backup of docker-compose.yml at {backup_path}")
    
    compose_content = f"""version: '3.9'
services:
  {SERVICE_NAME_IN_COMPOSE}:
    image: supagrok/snapshot-tipiservice:local
    container_name: {CONTAINER_NAME}
    network_mode: "host"  # Use host networking instead of port mapping
    volumes:
      - ./data:/data
    environment:
      GPG_KEY_ID: tipi-backup@supagrok.io
      GPG_PASSPHRASE: secureTipiSnapshotPass123
      PYTHONUNBUFFERED: '1'
    restart: unless-stopped
    healthcheck:
      test:
        - CMD-SHELL
        - curl -f http://localhost:{APP_PORT}/health || exit 1
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    build: .
"""
    
    # Write the updated content
    with open(COMPOSE_FILE_PATH, 'w') as f:
        f.write(compose_content)
    
    log("SUCCESS", "Updated docker-compose.yml to use host network mode.")
    return True

def restart_docker_service():
    """Restart the Docker service to apply changes."""
    log("STEP", "Restarting Docker service...")
    
    # Check for existing container
    log("INFO", "Checking for existing container...")
    container_cmd = ["docker", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"]
    container_result = run_command(container_cmd, check=False, capture_output=True, text=True)
    
    if container_result and container_result.stdout and CONTAINER_NAME in container_result.stdout:
        log("INFO", f"Found existing container: {CONTAINER_NAME}. Removing...")
        
        # Stop and remove the container
        rm_cmd = ["docker", "rm", "-f", CONTAINER_NAME]
        rm_result = run_command(rm_cmd, check=False, capture_output=True, text=True, use_sudo=True)
        
        if rm_result and rm_result.returncode == 0:
            log("SUCCESS", f"Successfully removed container: {CONTAINER_NAME}")
        else:
            log("WARN", f"Failed to remove container: {CONTAINER_NAME}")
    
    # Bring down any existing services
    down_cmd = ["docker-compose", "down"]
    down_result = run_command(down_cmd, check=False, capture_output=True, text=True)
    
    # Start the service
    up_cmd = ["docker-compose", "up", "-d"]
    up_result = run_command(up_cmd, check=False, capture_output=True, text=True)
    
    if up_result and up_result.returncode == 0:
        log("SUCCESS", "Docker service restarted successfully.")
        return True
    else:
        log("ERROR", "Failed to restart Docker service.")
        if up_result and up_result.stdout:
            log("INFO", f"Stdout: {up_result.stdout}")
        if up_result and up_result.stderr:
            log("ERROR", f"Stderr: {up_result.stderr}")
        return False

def verify_service_accessibility(server_ip, port):
    """Verify that the service is accessible."""
    log("STEP", f"Verifying service accessibility at http://{server_ip}:{port}/health...")
    
    # Wait for service to start
    log("INFO", "Waiting for service to start (10 seconds)...")
    time.sleep(10)
    
    # Try to access the health endpoint
    try:
        response = urllib.request.urlopen(f"http://localhost:{port}/health", timeout=5)
        if response.status == 200:
            data = response.read().decode('utf-8')
            log("SUCCESS", f"Service is accessible locally. Response: {data}")
            
            # Try with server IP
            try:
                response = urllib.request.urlopen(f"http://{server_ip}:{port}/health", timeout=5)
                if response.status == 200:
                    data = response.read().decode('utf-8')
                    log("SUCCESS", f"Service is accessible via server IP. Response: {data}")
                    return True
                else:
                    log("ERROR", f"Service returned status code {response.status} via server IP.")
            except Exception as e:
                log("ERROR", f"Error accessing service via server IP: {e}")
            
            return True
        else:
            log("ERROR", f"Service returned status code {response.status}.")
            return False
    except Exception as e:
        log("ERROR", f"Error accessing service: {e}")
        return False

def main():
    """PRF-P22: Main one-shot execution flow."""
    log("INFO", "Starting Supagrok Network Fix Script V1.0...")
    
    # Get the server's IP address
    server_ip = get_server_ip()
    
    # Ensure firewall rules
    if not ensure_firewall_rules(APP_PORT):
        log("WARN", f"Could not verify firewall rules for port {APP_PORT}. Continuing anyway...")
    
    # Update docker-compose.yml
    if not update_docker_compose_to_host_network():
        log("ERROR", "Failed to update docker-compose.yml. Exiting.")
        sys.exit(1)
    
    # Restart Docker service
    if not restart_docker_service():
        log("ERROR", "Failed to restart Docker service. Exiting.")
        sys.exit(1)
    
    # Verify service accessibility
    verify_service_accessibility(server_ip, APP_PORT)
    
    log("SUCCESS", "Supagrok Network Fix completed successfully!")
    log("INFO", f"Service should be accessible at http://{server_ip}:{APP_PORT}/health")
    log("INFO", f"To verify externally, run: curl http://{server_ip}:{APP_PORT}/health")

if __name__ == "__main__":
    main()
'''

def transfer_and_execute(ssh_target):
    """PRF-P05, P12, P18: Transfer the fix script to the server and execute it."""
    log("STEP", f"Connecting to {ssh_target}...")
    
    # Test SSH connection
    test_cmd = "echo 'SSH connection successful'"
    test_result = run_remote_command(ssh_target, test_cmd, check=False)
    
    if not test_result or test_result.returncode != 0:
        log("ERROR", f"Failed to connect to {ssh_target}. Please check your SSH credentials and try again.")
        return False
    
    log("SUCCESS", "SSH connection established.")
    
    # Get remote username and hostname
    username, hostname = ssh_target.split('@')
    
    # Create the fix script
    fix_script_content = create_network_fix_script()
    
    # Create a temporary file for the fix script
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(fix_script_content)
        temp_file_path = temp_file.name
    
    log("INFO", f"Created temporary fix script at {temp_file_path}")
    
    # Transfer the fix script to the server
    log("STEP", "Transferring fix script to server...")
    scp_cmd = ["scp", temp_file_path, f"{ssh_target}:{REMOTE_SCRIPT_PATH}"]
    scp_result = run_local_command(scp_cmd, check=False)
    
    if not scp_result or scp_result.returncode != 0:
        log("ERROR", "Failed to transfer fix script to server.")
        os.unlink(temp_file_path)
        return False
    
    log("SUCCESS", "Fix script transferred to server.")
    
    # Make the fix script executable
    chmod_cmd = f"chmod +x {REMOTE_SCRIPT_PATH}"
    chmod_result = run_remote_command(ssh_target, chmod_cmd, check=False)
    
    if not chmod_result or chmod_result.returncode != 0:
        log("ERROR", "Failed to make fix script executable.")
        os.unlink(temp_file_path)
        return False
    
    # Execute the fix script on the server
    log("STEP", "Executing fix script on server...")
    
    # First, check if the supagrok-tipiservice directory exists
    check_dir_cmd = "cd ~/supagrok-tipiservice && echo 'Directory exists' || echo 'Directory not found'"
    check_dir_result = run_remote_command(ssh_target, check_dir_cmd, check=False)
    
    if check_dir_result and "Directory exists" in check_dir_result.stdout:
        log("INFO", "Found supagrok-tipiservice directory.")
        execute_cmd = f"cd ~/supagrok-tipiservice && python3 {REMOTE_SCRIPT_PATH}"
    else:
        log("WARN", "supagrok-tipiservice directory not found in home directory. Searching...")
        
        # Try to find the directory
        find_cmd = "find ~ -name 'supagrok-tipiservice' -type d 