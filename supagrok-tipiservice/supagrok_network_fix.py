#!/usr/bin/env python3
# PRF-SUPAGROK-V3-NETWORK-FIX-V1.0
# UUID: 7e9d2f8a-6b5c-4c3d-9e1f-8a7b6c5d4e3f
# Path: /home/supagrok/supagrok-tipiservice/supagrok_network_fix.py
# Purpose: One-shot script to fix network configuration for Supagrok Snapshot Tipi service,
#          ensuring proper Docker networking, firewall rules, and service accessibility.
# PRF Relevance: P01, P02, P03, P04, P05, P06, P07, P11, P12, P13, P14, P15, P16, P17, P18, P19, P21, P22, P24, P25, P26, P27, P28, P29, P30

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path
import socket
import requests
from datetime import datetime

# --- Configuration ---
COMPOSE_FILE_PATH = Path("docker-compose.yml")
APP_PORT = 8000
SERVICE_NAME_IN_COMPOSE = "supagrok-snapshot-service"
CONTAINER_NAME = "supagrok_snapshot_service_container"

# --- Logging ---
def log(level, msg):
    """PRF-P07: Centralized logging with clear indicators."""
    icon = {"INFO": "🌀", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅", "STEP": "🛠️"}
    print(f"{icon.get(level.upper(), 'ℹ️')} [{level.upper()}] {msg}")

# --- Command Execution Utility ---
def run_command(command_parts, check=True, capture_output=False, text=True, use_sudo_if_needed=False, needs_sudo_flag=False, cmd_input=None):
    """
    PRF-P16: Executes a command, optionally with sudo, and handles errors.
    """
    final_command = list(command_parts)  # Make a mutable copy
    if use_sudo_if_needed and needs_sudo_flag and os.geteuid() != 0:
        final_command.insert(0, "sudo")

    log("INFO", f"Executing: {' '.join(final_command)}")
    try:
        process = subprocess.run(
            final_command,
            check=check,
            capture_output=capture_output,
            text=text,
            input=cmd_input,
            env=os.environ.copy()  # Pass current environment
        )
        return process
    except subprocess.CalledProcessError as e:
        stderr = e.stderr if e.stderr else ""
        stdout = e.stdout if e.stdout else ""
        log("ERROR", f"Command '{' '.join(final_command)}' failed with exit code {e.returncode}.")
        if stdout: log("INFO", f"Stdout:\n{stdout.strip()}")
        if stderr: log("ERROR", f"Stderr:\n{stderr.strip()}")
        if check:  # Re-raise only if check=True
            raise
        return e  # Return the exception object if check=False for further inspection
    except FileNotFoundError:
        log("ERROR", f"Command not found: {final_command[0]}")
        if check:
            raise
        return None  # Indicate failure
    except Exception as e:
        log("ERROR", f"An unexpected error occurred with command '{' '.join(final_command)}': {e}")
        if check:
            raise
        return None

def get_server_ip():
    """PRF-P05, P12: Get the server's public IP address."""
    log("STEP", "Determining server IP address...")
    
    # Try to get the IP from the network interface
    try:
        # This gets the IP that would be used to connect to 8.8.8.8 (Google DNS)
        # It doesn't actually establish a connection
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
        response = requests.get("https://api.ipify.org", timeout=5)
        if response.status_code == 200:
            ip = response.text
            log("SUCCESS", f"Detected server IP via external service: {ip}")
            return ip
    except Exception as e:
        log("WARN", f"Could not determine IP via external service: {e}")
    
    log("WARN", "Could not automatically determine server IP. Using localhost for testing.")
    return "localhost"

def ensure_firewall_rules(port, needs_sudo=True):
    """PRF-P05, P12, P18: Ensures the firewall allows traffic on the specified port."""
    log("STEP", f"Checking firewall rules for port {port}...")
    
    # Check if ufw is installed and active
    ufw_status = run_command(["sudo", "ufw", "status"], check=False, capture_output=True)
    
    if ufw_status and ufw_status.returncode == 0:
        if "Status: active" in ufw_status.stdout:
            log("INFO", "UFW firewall is active. Checking rules...")
            
            # Check if the port is already allowed
            if f"{port}/tcp" in ufw_status.stdout:
                log("SUCCESS", f"Port {port} is already allowed in UFW.")
            else:
                log("INFO", f"Adding rule to allow port {port}...")
                run_command(["sudo", "ufw", "allow", f"{port}/tcp"], check=False)
                log("SUCCESS", f"Added UFW rule for port {port}.")
        else:
            log("INFO", "UFW is installed but not active. No firewall rules needed.")
    else:
        log("INFO", "UFW not found or not accessible. Checking iptables...")
        
        # Check iptables as a fallback
        iptables_check = run_command(["sudo", "iptables", "-L", "INPUT", "-n"], check=False, capture_output=True)
        
        if iptables_check and iptables_check.returncode == 0:
            if f"tcp dpt:{port}" in iptables_check.stdout:
                log("SUCCESS", f"Port {port} is already allowed in iptables.")
            else:
                log("INFO", f"Adding iptables rule for port {port}...")
                run_command(["sudo", "iptables", "-A", "INPUT", "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"], check=False)
                log("SUCCESS", f"Added iptables rule for port {port}.")
        else:
            log("WARN", "Could not check or modify firewall rules. Please ensure port {port} is accessible.")
    
    return True

def update_docker_compose_to_host_network():
    """PRF-P05, P12, P28: Updates docker-compose.yml to use host network mode."""
    log("STEP", "Updating docker-compose.yml to use host network mode...")
    
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
    
    try:
        # Create a backup of the original file
        if COMPOSE_FILE_PATH.exists():
            backup_path = COMPOSE_FILE_PATH.with_suffix('.yml.bak')
            shutil.copy2(COMPOSE_FILE_PATH, backup_path)
            log("INFO", f"Created backup of docker-compose.yml at {backup_path}")
        
        # Write the new content
        with open(COMPOSE_FILE_PATH, 'w') as f:
            f.write(compose_content)
        
        log("SUCCESS", "Updated docker-compose.yml to use host network mode.")
        return True
    except Exception as e:
        log("ERROR", f"Failed to update docker-compose.yml: {e}")
        return False

def restart_docker_service(needs_sudo=True):
    """PRF-P05, P12, P18: Restarts the Docker service with the new configuration."""
    log("STEP", "Restarting Docker service...")
    
    # Stop the service
    run_command(["sudo", "docker-compose", "down"], check=False)
    
    # Start the service
    result = run_command(["sudo", "docker-compose", "up", "-d"], check=False, capture_output=True)
    
    if result and result.returncode == 0:
        log("SUCCESS", "Docker service restarted successfully.")
        return True
    else:
        log("ERROR", "Failed to restart Docker service.")
        if result and result.stdout:
            log("INFO", f"Stdout: {result.stdout}")
        if result and result.stderr:
            log("ERROR", f"Stderr: {result.stderr}")
        return False

def verify_service_accessibility(server_ip, port):
    """PRF-P05, P12, P18: Verifies the service is accessible both locally and externally."""
    log("STEP", f"Verifying service accessibility on port {port}...")
    
    # Wait for the service to start
    log("INFO", "Waiting for service to start (5 seconds)...")
    time.sleep(5)
    
    # Check local accessibility
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            log("SUCCESS", f"Service is accessible locally at http://localhost:{port}/health")
            log("INFO", f"Response: {response.text}")
        else:
            log("WARN", f"Service returned status code {response.status_code} locally.")
    except Exception as e:
        log("WARN", f"Could not access service locally: {e}")
    
    # Check external accessibility
    if server_ip != "localhost":
        log("INFO", f"Testing external accessibility at http://{server_ip}:{port}/health")
        log("INFO", "Note: This may fail if testing from the server itself due to firewall rules.")
        log("INFO", f"To test externally, run: curl http://{server_ip}:{port}/health from another machine.")
    
    return True

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