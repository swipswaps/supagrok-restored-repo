#!/usr/bin/env python3
# PRF-SUPAGROK-IONOS-DEPLOY-V1.0
# UUID: 9d8c7b6a-5e4f-3d2c-1b0a-9f8e7d6c5b4a
# Path: /home/username/projects/supagrok-tipiservice/ionos_deploy.py
# Purpose: One-shot deployment script for Supagrok Tipi Service on IONOS servers
# PRF Relevance: PRF1-PRF28

import os
import sys
import subprocess
import shutil
import time
import socket
from pathlib import Path
from datetime import datetime
import signal
import json
import re
import urllib.request
import platform

# --- Configuration ---
SCRIPT_UUID = "9d8c7b6a-5e4f-3d2c-1b0a-9f8e7d6c5b4a"
SCRIPT_VERSION = "1.0"
APP_PORT = 8000
REQUIRED_FILES = [
    "supagrok_master_launcher.py",
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt"
]
REQUIRED_DIRS = [
    "data",
    "data/source",
    "data/output"
]
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# --- Logging and Output Formatting ---
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

def run_command(cmd_parts, check=True, capture_output=False, use_sudo=False):
    """PRF14, PRF18: Execute a command with proper error handling."""
    if use_sudo and os.geteuid() != 0:
        cmd_parts = ["sudo"] + cmd_parts
    
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
            if hasattr(e, 'stdout') and e.stdout:
                log("ERROR", f"STDOUT: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                log("ERROR", f"STDERR: {e.stderr}")
        if check:
            raise
        return e
    except Exception as e:
        log("ERROR", f"Exception running command: {str(e)}")
        if check:
            raise
        return None

# --- Verification Functions ---
def verify_prerequisites():
    """PRF12: Verify all prerequisites are met."""
    log("STEP", "Verifying prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        log("ERROR", f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        return False
    
    # Check required files
    missing_files = []
    for file in REQUIRED_FILES:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        log("ERROR", f"Missing required files: {', '.join(missing_files)}")
        return False
    
    # Create required directories
    for dir_path in REQUIRED_DIRS:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Check for PyYAML
    try:
        import yaml
        log("INFO", "PyYAML is installed.")
    except ImportError:
        log("INFO", "PyYAML not found. Will be installed by the master launcher.")
    
    log("SUCCESS", "All prerequisites verified.")
    return True

def check_port_availability():
    """PRF12, PRF15: Check if the required port is available."""
    log("STEP", f"Checking if port {APP_PORT} is available...")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(('localhost', APP_PORT))
        if result == 0:
            log("WARN", f"Port {APP_PORT} is already in use.")
            return False
        else:
            log("SUCCESS", f"Port {APP_PORT} is available.")
            return True

def check_ionos_specific_settings():
    """PRF20: Check IONOS-specific settings and firewall rules."""
    log("STEP", "Checking IONOS-specific settings...")
    
    # Check if this is likely an IONOS server
    is_ionos = False
    try:
        with open('/etc/os-release', 'r') as f:
            os_info = f.read().lower()
            if 'ionos' in os_info or '1&1' in os_info:
                is_ionos = True
    except:
        pass
    
    if not is_ionos:
        # Try to detect IONOS by checking for specific files or directories
        ionos_indicators = [
            '/etc/ionos',
            '/etc/1and1',
            '/usr/local/ionos'
        ]
        for indicator in ionos_indicators:
            if os.path.exists(indicator):
                is_ionos = True
                break
    
    if is_ionos:
        log("INFO", "IONOS server detected.")
    else:
        log("INFO", "Could not confirm this is an IONOS server. Proceeding with generic checks.")
    
    # Check if firewall is enabled and if port 8000 is open
    firewall_tools = ['ufw', 'firewalld', 'iptables']
    firewall_detected = False
    
    for tool in firewall_tools:
        if shutil.which(tool):
            firewall_detected = True
            if tool == 'ufw':
                result = run_command(["ufw", "status"], check=False, capture_output=True)
                if result and "active" in result.stdout.lower():
                    if f"{APP_PORT}" not in result.stdout:
                        log("WARN", f"UFW firewall is active but port {APP_PORT} may not be open.")
                        log("INFO", f"Consider running: sudo ufw allow {APP_PORT}/tcp")
            elif tool == 'firewalld':
                result = run_command(["firewall-cmd", "--list-ports"], check=False, capture_output=True)
                if result and f"{APP_PORT}/tcp" not in result.stdout:
                    log("WARN", f"Firewalld is active but port {APP_PORT} may not be open.")
                    log("INFO", f"Consider running: sudo firewall-cmd --permanent --add-port={APP_PORT}/tcp && sudo firewall-cmd --reload")
            elif tool == 'iptables':
                result = run_command(["iptables", "-L", "-n"], check=False, capture_output=True, use_sudo=True)
                if result and f"dpt:{APP_PORT}" not in result.stdout:
                    log("WARN", f"iptables may be blocking port {APP_PORT}.")
                    log("INFO", f"Consider running: sudo iptables -A INPUT -p tcp --dport {APP_PORT} -j ACCEPT")
    
    if not firewall_detected:
        log("INFO", "No firewall detected. Port should be accessible if no external firewall is blocking it.")
    
    # Check if IONOS panel firewall might be blocking
    log("INFO", "Please ensure port 8000 is open in your IONOS control panel firewall settings.")
    
    # Check external connectivity (optional)
    try:
        external_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
        log("INFO", f"External IP address: {external_ip}")
        log("INFO", f"Your service will be accessible at: http://{external_ip}:{APP_PORT}")
    except:
        log("WARN", "Could not determine external IP address.")
    
    return True

# --- Setup Functions ---
def setup_environment():
    """PRF4, PRF5, PRF6: Set up the environment."""
    log("STEP", "Setting up environment...")
    
    # Create a test file in the source directory
    test_file_path = Path("data/source/test_file.txt")
    with open(test_file_path, "w") as f:
        f.write("This is a test file for the Supagrok Tipi Service.\n")
        f.write(f"Created by ionos_deploy.py (UUID: {SCRIPT_UUID}) on {datetime.now().isoformat()}\n")
    
    # Check and set permissions for data directories
    for dir_path in REQUIRED_DIRS:
        path = Path(dir_path)
        try:
            # Ensure directory exists
            path.mkdir(parents=True, exist_ok=True)
            
            # Set permissions (rwxrwxr-x)
            os.chmod(path, 0o775)
            
            log("INFO", f"Set permissions for {dir_path}")
        except Exception as e:
            log("WARN", f"Could not set permissions for {dir_path}: {str(e)}")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(f"APP_PORT={APP_PORT}\n")
            f.write("DEBUG=false\n")
            f.write(f"DATA_SOURCE_DIR={os.path.abspath('data/source')}\n")
            f.write(f"DATA_OUTPUT_DIR={os.path.abspath('data/output')}\n")
        log("INFO", "Created .env file with default settings.")
    
    log("SUCCESS", "Environment set up successfully.")
    return True

def ensure_docker_installed():
    """PRF4, PRF21: Ensure Docker is installed."""
    log("STEP", "Checking Docker installation...")
    
    if shutil.which("docker"):
        # Check if Docker daemon is running
        result = run_command(["docker", "info"], check=False, capture_output=True)
        if result and result.returncode == 0:
            log("SUCCESS", "Docker is installed and running.")
            return True
        else:
            log("WARN", "Docker is installed but may not be running.")
    
    log("INFO", "Docker not found or not running. Attempting to install/start...")
    
    # Determine OS
    os_type = platform.system().lower()
    if os_type == "linux":
        # Determine Linux distribution
        try:
            with open('/etc/os-release', 'r') as f:
                os_info = f.read().lower()
                if 'ubuntu' in os_info or 'debian' in os_info:
                    # Ubuntu/Debian installation
                    run_command(["apt-get", "update"], check=False, use_sudo=True)
                    run_command(["apt-get", "install", "-y", "docker.io", "docker-compose"], check=False, use_sudo=True)
                elif 'centos' in os_info or 'rhel' in os_info or 'fedora' in os_info:
                    # CentOS/RHEL/Fedora installation
                    run_command(["yum", "install", "-y", "docker", "docker-compose"], check=False, use_sudo=True)
                else:
                    log("WARN", "Unsupported Linux distribution. Please install Docker manually.")
                    return False
        except:
            log("WARN", "Could not determine Linux distribution. Trying apt-get...")
            run_command(["apt-get", "update"], check=False, use_sudo=True)
            run_command(["apt-get", "install", "-y", "docker.io", "docker-compose"], check=False, use_sudo=True)
    else:
        log("ERROR", f"Unsupported OS: {os_type}. Please install Docker manually.")
        return False
    
    # Start and enable Docker
    run_command(["systemctl", "start", "docker"], check=False, use_sudo=True)
    run_command(["systemctl", "enable", "docker"], check=False, use_sudo=True)
    
    # Add current user to docker group
    user = os.getenv("USER")
    if user:
        run_command(["usermod", "-aG", "docker", user], check=False, use_sudo=True)
        log("INFO", f"Added user {user} to docker group. You may need to log out and back in for this to take effect.")
    
    # Verify Docker is now working
    result = run_command(["docker", "info"], check=False, capture_output=True)
    if result and result.returncode == 0:
        log("SUCCESS", "Docker installed and running successfully.")
        return True
    else:
        log("ERROR", "Failed to install or start Docker.")
        return False

# --- Deployment Functions ---
def run_master_launcher():
    """PRF3, PRF22: Run the master launcher script."""
    log("STEP", "Running supagrok_master_launcher.py...")
    
    # Make the script executable
    try:
        os.chmod("supagrok_master_launcher.py", 0o755)
    except:
        log("WARN", "Could not make supagrok_master_launcher.py executable. Will run with python3.")
    
    # Run the script
    for attempt in range(1, MAX_RETRIES + 1):
        log("INFO", f"Attempt {attempt}/{MAX_RETRIES} to run master launcher...")
        
        result = run_command(["python3", "supagrok_master_launcher.py"], check=False, capture_output=True)
        
        if result and result.returncode == 0:
            log("SUCCESS", "Master launcher completed successfully.")
            return True
        else:
            if result:
                if hasattr(result, 'stdout') and result.stdout:
                    log("INFO", "Master launcher output:")
                    print(result.stdout)
                if hasattr(result, 'stderr') and result.stderr:
                    log("ERROR", "Master launcher errors:")
                    print(result.stderr)
            
            if attempt < MAX_RETRIES:
                log("WARN", f"Master launcher failed. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                log("ERROR", "Master launcher failed after all retry attempts.")
                return False
    
    return False

def verify_service_running():
    """PRF3, PRF28: Verify the service is running."""
    log("STEP", "Verifying service is running...")
    
    for attempt in range(1, MAX_RETRIES + 1):
        # Check if container is running
        result = run_command(["docker", "ps"], check=False, capture_output=True)
        if result and ("supagrok_snapshot_service" in result.stdout or "supagrok-snapshot-service" in result.stdout):
            log("SUCCESS", "Supagrok container is running.")
            
            # Check if service is responding
            time.sleep(5)  # Give the service a moment to fully start
            
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)