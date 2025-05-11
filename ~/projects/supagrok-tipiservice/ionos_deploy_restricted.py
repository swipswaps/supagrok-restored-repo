#!/usr/bin/env python3
# PRF-SUPAGROK-IONOS-DEPLOY-RESTRICTED-V1.0
# UUID: 8e7d6c5b-4a3b-2c1d-0e9f-8a7b6c5d4e3f
# Path: ~/projects/supagrok-tipiservice/ionos_deploy_restricted.py
# Purpose: Restricted environment deployment script for Supagrok Tipi Service on IONOS servers
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
import platform
import urllib.request
from urllib.error import URLError

# --- Configuration ---
SCRIPT_UUID = "8e7d6c5b-4a3b-2c1d-0e9f-8a7b6c5d4e3f"
SCRIPT_VERSION = "1.0-restricted"
APP_PORT = 8000
REQUIRED_FILES = [
    "supagrok_snapshot_worker.py",
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
    # In restricted environment, we ignore use_sudo
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
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 6):
        log("ERROR", f"Python 3.6+ required, found {python_version.major}.{python_version.minor}")
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
    
    # Check for PyYAML - not critical in restricted mode
    try:
        import yaml
        log("INFO", "PyYAML is installed.")
    except ImportError:
        log("WARN", "PyYAML not found. Some functionality may be limited.")
    
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

def check_environment_restrictions():
    """PRF18, PRF20: Check environment restrictions."""
    log("STEP", "Checking environment restrictions...")
    
    # Check if we have sudo access
    has_sudo = False
    if shutil.which("sudo"):
        try:
            result = run_command(["sudo", "-n", "true"], check=False, capture_output=True)
            has_sudo = result and result.returncode == 0
        except:
            has_sudo = False
    
    if not has_sudo:
        log("WARN", "No sudo access detected. Running in restricted mode.")
        log("INFO", "Some features requiring elevated privileges will be skipped.")
    
    # Check if we can write to our home directory
    home_dir = os.path.expanduser("~")
    try:
        test_file = os.path.join(home_dir, ".test_write_permission")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        log("INFO", f"Write access to home directory ({home_dir}) confirmed.")
    except:
        log("ERROR", f"Cannot write to home directory ({home_dir}).")
        return False
    
    # Check if Docker is available
    has_docker = shutil.which("docker") is not None
    if has_docker:
        try:
            result = run_command(["docker", "info"], check=False, capture_output=True)
            has_docker = result and result.returncode == 0
        except:
            has_docker = False
    
    if not has_docker:
        log("WARN", "Docker not available. Container deployment will be skipped.")
    
    # Check external connectivity
    has_internet = False
    try:
        urllib.request.urlopen("https://www.google.com", timeout=5)
        has_internet = True
        log("INFO", "Internet connectivity confirmed.")
    except URLError:
        log("WARN", "No internet connectivity detected. Some features may be limited.")
    
    # Get server information
    server_info = {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "has_sudo": has_sudo,
        "has_docker": has_docker,
        "has_internet": has_internet
    }
    
    log("INFO", f"Server information: {json.dumps(server_info, indent=2)}")
    return True

# --- Setup Functions ---
def setup_environment():
    """PRF4, PRF5, PRF6: Set up the environment."""
    log("STEP", "Setting up environment...")
    
    # Create a test file in the source directory
    test_file_path = Path("data/source/test_file.txt")
    with open(test_file_path, "w") as f:
        f.write("This is a test file for the Supagrok Tipi Service.\n")
        f.write(f"Created by ionos_deploy_restricted.py (UUID: {SCRIPT_UUID}) on {datetime.now().isoformat()}\n")
    
    # Check and set permissions for data directories
    for dir_path in REQUIRED_DIRS:
        path = Path(dir_path)
        try:
            # Ensure directory exists
            path.mkdir(parents=True, exist_ok=True)
            log("INFO", f"Created directory {dir_path}")
        except Exception as e:
            log("WARN", f"Could not create directory {dir_path}: {str(e)}")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(f"APP_PORT={APP_PORT}\n")
            f.write("DEBUG=true\n")
            f.write(f"DATA_SOURCE_DIR={os.path.abspath('data/source')}\n")
            f.write(f"DATA_OUTPUT_DIR={os.path.abspath('data/output')}\n")
        log("INFO", "Created .env file with default settings.")
    
    log("SUCCESS", "Environment set up successfully.")
    return True

def create_mock_docker_files():
    """PRF17, PRF23: Create mock Docker files for testing."""
    log("STEP", "Creating mock Docker files...")
    
    # Create Dockerfile if it doesn't exist
    dockerfile = Path("Dockerfile")
    if not dockerfile.exists():
        with open(dockerfile, "w") as f:
            f.write("# Mock Dockerfile for restricted environment\n")
            f.write("FROM python:3.9-slim\n\n")
            f.write("WORKDIR /app\n\n")
            f.write("COPY requirements.txt .\n")
            f.write("RUN pip install --no-cache-dir -r requirements.txt\n\n")
            f.write("COPY . .\n\n")
            f.write("EXPOSE 8000\n\n")
            f.write('CMD ["python", "-m", "uvicorn", "supagrok_snapshot_worker:app", "--host", "0.0.0.0", "--port", "8000"]\n')
        log("INFO", "Created mock Dockerfile.")
    
    # Create docker-compose.yml if it doesn't exist
    docker_compose = Path("docker-compose.yml")
    if not docker_compose.exists():
        with open(docker_compose, "w") as f:
            f.write("# Mock docker-compose.yml for restricted environment\n")
            f.write("version: '3'\n\n")
            f.write("services:\n")
            f.write("  supagrok_snapshot_service:\n")
            f.write("    build: .\n")
            f.write("    image: supagrok/snapshot-tipiservice:local\n")
            f.write("    container_name: supagrok_snapshot_service\n")
            f.write("    ports:\n")
            f.write("      - \"8000:8000\"\n")
            f.write("    volumes:\n")
            f.write("      - ./data/source:/app/data/source\n")
            f.write("      - ./data/output:/app/data/output\n")
            f.write("    restart: unless-stopped\n")
        log("INFO", "Created mock docker-compose.yml.")
    
    log("SUCCESS", "Mock Docker files created successfully.")
    return True

def create_test_api():
    """PRF10, PRF23: Create a test API for local testing."""
    log("STEP", "Creating test API...")
    
    # Create supagrok_snapshot_worker.py if it doesn't exist
    api_file = Path("supagrok_snapshot_worker.py")
    if not api_file.exists():
        with open(api_file, "w") as f:
            f.write("# Test API for restricted environment\n")
            f.write("from fastapi import FastAPI\n")
            f.write("from datetime import datetime\n")
            f.write("import os\n\n")
            f.write("app = FastAPI()\n\n")
            f.write("@app.get('/health')\n")
            f.write("async def health_check():\n")
            f.write("    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}\n\n")
            f.write("@app.get('/')\n")
            f.write("async def root():\n")
            f.write("    return {'message': 'Welcome to Supagrok Snapshot Service', 'version': '1.0.0'}\n\n")
            f.write("@app.get('/info')\n")
            f.write("async def info():\n")
            f.write("    return {\n")
            f.write("        'service': 'Supagrok Snapshot Service',\n")
            f.write("        'version': '1.0.0',\n")
            f.write("        'environment': 'restricted',\n")
            f.write("        'hostname': os.uname().nodename,\n")
            f.write("        'timestamp': datetime.now().isoformat()\n")
            f.write("    }\n")
        log("INFO", "Created test API file.")
    
    # Create requirements.txt if it doesn't exist
    req_file = Path("requirements.txt")
    if not req_file.exists():
        with open(req_file, "w") as f:
            f.write("fastapi>=0.95.0\n")
            f.write("uvicorn>=0.21.1\n")
            f.write("pydantic>=1.10.7\n")
        log("INFO", "Created requirements.txt file.")
    
    log("SUCCESS", "Test API created successfully.")
    return True

def install_dependencies():
    """PRF4, PRF21: Install Python dependencies locally."""
    log("STEP", "Installing Python dependencies...")
    
    # Check if pip is available
    if not shutil.which("pip") and not shutil.which("pip3"):
        log("ERROR", "pip/pip3 not found. Cannot install dependencies.")
        return False
    
    pip_cmd = shutil.which("pip3") or shutil.which("pip")
    
    # Create a virtual environment
    venv_dir = Path("venv")
    if not venv_dir.exists():
        try:
            log("INFO", "Creating virtual environment...")
            if shutil.which("python3"):
                run_command(["python3", "-m", "venv", "venv"], check=True)
            else:
                run_command(["python", "-m", "venv", "venv"], check=True)
            log("SUCCESS", "Virtual environment created.")
        except Exception as e:
            log("WARN", f"Could not create virtual environment: {str(e)}")
            log("INFO", "Will attempt to install dependencies globally.")
    
    # Install dependencies
    try:
        if venv_dir.exists():
            # Use the virtual environment
            if os.name == 'nt':  # Windows
                pip_path = os.path.join("venv", "Scripts", "pip")
            else:  # Unix/Linux
                pip_path = os.path.join("venv", "bin", "pip")
            
            run_command([pip_path, "install", "-r", "requirements.txt"], check=True)
        else:
            # Use global pip
            run_command([pip_cmd, "install", "--user", "-r", "requirements.txt"], check=True)
        
        log("SUCCESS", "Dependencies installed successfully.")
        return True
    except Exception as e:
        log("ERROR", f"Failed to install dependencies: {str(e)}")