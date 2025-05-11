#!/usr/bin/env python3
# PRF-SUPAGROK-COMPOSE-WATCH-V1.1
# UUID: a7bc7976-ca86-4334-981d-96a4f02128dd
# Path: /home/owner/supagrok-tipiservice/supagrok_compose_watch.py
# Purpose: Monitor and manage Docker Compose services for the Supagrok Tipi Service
# PRF Relevance: PRF3, PRF7, PRF17, PRF28, PRF30

import os
import subprocess
import time
import sys
import signal
import json
from datetime import datetime
from pathlib import Path

# Configuration
COMPOSE_FILE = "docker-compose.yml"
SERVICE_NAME = "supagrok-snapshot-service"
CHECK_INTERVAL = 10  # seconds
MAX_RESTARTS = 3

def log(level, message):
    """PRF7: Structured logging with timestamp and level."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level_colors = {
        "ERROR": "\033[91m",  # Red
        "WARN": "\033[93m",   # Yellow
        "SUCCESS": "\033[92m", # Green
        "INFO": "\033[94m",   # Blue
        "STEP": "\033[95m",   # Purple
        "DEBUG": "\033[96m"   # Cyan
    }
    reset_color = "\033[0m"
    
    color = level_colors.get(level, level_colors["INFO"])
    print(f"{color}[{timestamp}] [{level}] {message}{reset_color}")

def run_command(cmd_parts, check=True, capture_output=False):
    """PRF14, PRF28: Execute a command with proper error handling."""
    try:
        log("DEBUG", f"Running command: {' '.join(cmd_parts)}")
        result = subprocess.run(
            cmd_parts,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if capture_output:
            log("ERROR", f"Command failed with exit code {e.returncode}")
            log("ERROR", f"STDOUT: {e.stdout}")
            log("ERROR", f"STDERR: {e.stderr}")
        if check:
            raise
        return e
    except Exception as e:
        log("ERROR", f"Exception running command: {str(e)}")
        if check:
            raise
        return None

def get_compose_command():
    """PRF16: Determine the correct Docker Compose command."""
    if os.path.exists("/usr/bin/docker-compose"):
        return ["docker-compose"]
    elif os.path.exists("/usr/bin/docker") and os.system("docker compose version > /dev/null 2>&1") == 0:
        return ["docker", "compose"]
    else:
        log("ERROR", "Docker Compose not found. Please install Docker Compose.")
        return None

def is_service_running():
    """PRF3, PRF17: Check if the service is running."""
    compose_cmd = get_compose_command()
    if not compose_cmd:
        return False
    
    cmd = compose_cmd + ["ps", "--format", "json"]
    result = run_command(cmd, check=False, capture_output=True)
    
    if result and result.returncode == 0:
        try:
            # Parse JSON output (Docker Compose v2)
            services = json.loads(result.stdout)
            for service in services:
                if SERVICE_NAME in service.get("Name", "") and service.get("State") == "running":
                    return True
        except json.JSONDecodeError:
            # Fall back to text parsing (Docker Compose v1)
            for line in result.stdout.splitlines():
                if SERVICE_NAME in line and "Up" in line:
                    return True
    
    return False

def start_service():
    """PRF17, PRF30: Start the service with orphan container cleanup."""
    log("STEP", f"Starting {SERVICE_NAME} service...")
    
    compose_cmd = get_compose_command()
    if not compose_cmd:
        return False
    
    cmd = compose_cmd + ["up", "-d", "--remove-orphans"]
    result = run_command(cmd, check=False)
    
    if result and result.returncode == 0:
        log("SUCCESS", f"Service {SERVICE_NAME} started successfully.")
        return True
    else:
        log("ERROR", f"Failed to start service {SERVICE_NAME}.")
        return False

def restart_service():
    """PRF15, PRF17: Restart the service with proper error handling."""
    log("STEP", f"Restarting {SERVICE_NAME} service...")
    
    compose_cmd = get_compose_command()
    if not compose_cmd:
        return False
    
    # Stop first
    stop_cmd = compose_cmd + ["stop", SERVICE_NAME]
    run_command(stop_cmd, check=False)
    
    # Then start with orphan cleanup
    cmd = compose_cmd + ["up", "-d", "--remove-orphans"]
    result = run_command(cmd, check=False)
    
    if result and result.returncode == 0:
        log("SUCCESS", f"Service {SERVICE_NAME} restarted successfully.")
        return True
    else:
        log("ERROR", f"Failed to restart service {SERVICE_NAME}.")
        return False

def watch_service():
    """PRF3, PRF15: Monitor the service and restart if needed."""
    log("INFO", f"Starting service watcher for {SERVICE_NAME}...")
    
    restart_count = 0
    
    while True:
        if not is_service_running():
            log("WARN", f"Service {SERVICE_NAME} is not running.")
            
            if restart_count < MAX_RESTARTS:
                restart_count += 1
                log("INFO", f"Attempting restart ({restart_count}/{MAX_RESTARTS})...")
                restart_service()
            else:
                log("ERROR", f"Maximum restart attempts ({MAX_RESTARTS}) reached. Please check the service logs.")
                return False
        else:
            # Reset restart count if service is running
            restart_count = 0
            log("INFO", f"Service {SERVICE_NAME} is running. Next check in {CHECK_INTERVAL} seconds.")
        
        time.sleep(CHECK_INTERVAL)

def handle_signal(sig, frame):
    """PRF28: Handle termination signals gracefully."""
    log("INFO", "Received termination signal. Shutting down watcher...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Check if compose file exists
    if not Path(COMPOSE_FILE).exists():
        log("ERROR", f"Compose file not found: {COMPOSE_FILE}")
        sys.exit(1)
    
    # Start the service
    if not is_service_running():
        if not start_service():
            log("ERROR", "Failed to start the service. Exiting.")
            sys.exit(1)
    
    # Watch the service
    watch_service()
