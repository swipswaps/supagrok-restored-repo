#!/usr/bin/env python3
# PRF-SUPAGROK-V3-MASTER-LAUNCHER-V3.0.3
# UUID: 7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d-fixed-v3
# Path: /home/supagrok/supagrok-tipiservice/supagrok_master_launcher.py
# Purpose: One-shot launcher for Supagrok Snapshot Tipi Service, ensuring environment setup, service deployment, and auto-creation of docker-compose.yml if missing.
# PRF Relevance: P01, P02, P03, P04, P05, P06, P07, P08, P09, P10, P11, P12, P13, P14, P15, P16, P17, P18, P19, P20, P21, P22, P23, P24, P25, P26, P27, P28, P29, P30, P31

import os
import sys
import subprocess
import time
import socket
import shutil
import platform
import re
import signal
import tempfile
import argparse
from pathlib import Path
from datetime import datetime
import json
import uuid

# --- Configuration ---
APP_PORT = 8000
GHCR_IMAGE_NAME = "ghcr.io/supagrok/snapshot-service:latest"
LOCAL_IMAGE_NAME = "supagrok/snapshot-tipiservice:local"
SERVICE_NAME_IN_COMPOSE = "supagrok-snapshot-service" # Should match the service name in your docker-compose.yml
CONTAINER_NAME = "supagrok_snapshot_service_container" # Desired container name
VERSION = "3.0.3" # Incremented version for docker-compose.yml auto-creation
SCRIPT_UUID = "7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d-fixed-v3"

# --- Logging ---
def log(level, msg):
    """PRF-P07, P13: Centralized logging with clear indicators."""
    icon = {"INFO": "🌀", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅", "STEP": "🛠️", "DEBUG": "🔍"}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} {icon.get(level.upper(), 'ℹ️')} [{level.upper()}] {msg}")

def ensure_yaml_installed():
    """PRF-P04: Ensure PyYAML is installed for docker-compose.yml manipulation."""
    try:
        import yaml
        globals()["yaml"] = yaml # Make it globally available after import
        return True
    except ImportError:
        log("INFO", "PyYAML not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "PyYAML"])
            log("SUCCESS", "Successfully installed PyYAML.")
            import yaml
            globals()["yaml"] = yaml # Make it globally available after import
            return True
        except Exception as e:
            log("ERROR", f"Failed to install PyYAML: {e}")
            log("INFO", "Please install manually with: pip install PyYAML")
            return False

def ensure_docker_installed():
    """PRF-P12: Verify Docker is installed, attempt to install if missing."""
    log("STEP", "Checking if Docker is installed...")
    if shutil.which("docker"):
        log("SUCCESS", "Docker is already installed.")
        try:
            version_check = subprocess.run(["docker", "--version"], capture_output=True, text=True, check=True)
            log("INFO", f"Docker version: {version_check.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            log("WARN", f"Docker is installed but 'docker --version' failed: {e}. Assuming it's usable.")
            return True
    log("INFO", "Docker not found. Attempting to install...")
    os_type = platform.system().lower()
    if os_type == "linux":
        try:
            if shutil.which("apt-get"):
                log("INFO", "Detected Debian/Ubuntu. Installing Docker via apt-get...")
                subprocess.run(["sudo", "apt-get", "update", "-y"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", "docker.io"], check=True)
            elif shutil.which("yum"):
                log("INFO", "Detected CentOS/RHEL/Fedora (yum). Installing Docker via yum...")
                subprocess.run(["sudo", "yum", "install", "-y", "docker"], check=True)
                subprocess.run(["sudo", "systemctl", "start", "docker"], check=True)
                subprocess.run(["sudo", "systemctl", "enable", "docker"], check=True)
            elif shutil.which("dnf"):
                log("INFO", "Detected Fedora (dnf). Installing Docker via dnf...")
                subprocess.run(["sudo", "dnf", "install", "-y", "docker"], check=True)
                subprocess.run(["sudo", "systemctl", "start", "docker"], check=True)
                subprocess.run(["sudo", "systemctl", "enable", "docker"], check=True)
            else:
                log("ERROR", "Unsupported Linux distribution for automatic Docker installation.")
                return False
            if shutil.which("docker"):
                log("SUCCESS", "Docker installed successfully.")
                return True
            else:
                log("ERROR", "Docker installation command ran, but 'docker' command still not found.")
                return False
        except subprocess.CalledProcessError as e:
            log("ERROR", f"Failed to install Docker: {e}")
            return False
    else:
        log("ERROR", f"Automatic Docker installation not supported on {os_type}.")
        return False

def fix_docker_permissions():
    """PRF-P05, P18: Fix Docker permissions for the current user to avoid sudo for Docker commands."""
    log("STEP", "Checking Docker permissions for current user...")
    if os.geteuid() == 0:
        log("INFO", "Script is running as root. Docker permissions are implicitly handled.")
        return False

    username = os.environ.get("USER")
    if not username:
        log("WARN", "Could not determine current username. Docker commands might require sudo.")
        return True

    try:
        subprocess.run(["docker", "ps"], check=True, capture_output=True)
        log("SUCCESS", f"User '{username}' can run Docker commands without sudo.")
        return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("INFO", f"User '{username}' cannot run Docker commands without sudo, or Docker is not running. Attempting to add to 'docker' group.")
        try:
            subprocess.run(["sudo", "usermod", "-aG", "docker", username], check=True)
            log("SUCCESS", f"User '{username}' added to 'docker' group. A logout/login or new shell session is typically required for this to take effect.")
            log("WARN", "Docker commands will be run with sudo for this session if direct access isn't immediately available.")
            try:
                subprocess.run(["docker", "ps"], check=True, capture_output=True)
                log("INFO", "Docker access without sudo confirmed after group add (unexpectedly fast).")
                return False
            except:
                return True
        except subprocess.CalledProcessError as e:
            log("ERROR", f"Failed to add user '{username}' to 'docker' group: {e}. Docker commands will require sudo.")
            return True

def setup_data_directories(needs_sudo_for_chown=False):
    """PRF-P05, P06, P28: Set up necessary data directories."""
    log("STEP", "Setting up data directories...")
    data_dir = Path("./data")
    source_dir = data_dir / "source"
    output_dir = data_dir / "output"
    try:
        data_dir.mkdir(exist_ok=True)
        source_dir.mkdir(exist_ok=True)
        output_dir.mkdir(exist_ok=True)
        test_file = source_dir / "test_file.txt"
        if not test_file.exists():
            with open(test_file, "w") as f:
                f.write(f"Test file created by Supagrok Master Launcher v{VERSION} on {datetime.now().isoformat()}\n")
            log("INFO", f"Created test file: {test_file}")

        if os.geteuid() == 0 and os.getenv("SUDO_USER"):
            target_user = os.getenv("SUDO_USER")
            log("INFO", f"Running as root, attempting to chown {data_dir} to user {target_user}")
            try:
                subprocess.run(["chown", "-R", f"{target_user}:{target_user}", str(data_dir)], check=True)
                log("SUCCESS", f"Changed ownership of {data_dir} to {target_user}.")
            except subprocess.CalledProcessError as e:
                log("WARN", f"Failed to change ownership of {data_dir}: {e}. Container might have permission issues with volume.")
        elif needs_sudo_for_chown:
             log("WARN", f"Script not running as root. Cannot chown {data_dir}. Container might have permission issues if user IDs don't match.")

        log("SUCCESS", "Data directories set up successfully.")
        return True
    except Exception as e:
        log("ERROR", f"Failed to set up data directories: {e}")
        return False

def get_compose_command(needs_sudo_for_docker):
    """PRF-P16: Determine the correct docker-compose command for this system."""
    log("STEP", "Determining Docker Compose command...")
    base_cmd = ["sudo"] if needs_sudo_for_docker else []

    try:
        cmd_v2 = base_cmd + ["docker", "compose", "version"]
        subprocess.run(cmd_v2, check=True, capture_output=True)
        log("INFO", "Using 'docker compose' (plugin v2).")
        return base_cmd + ["docker", "compose"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("INFO", "'docker compose' (plugin v2) not found or failed. Checking for standalone 'docker-compose' (v1).")

    try:
        cmd_v1 = base_cmd + ["docker-compose", "--version"]
        subprocess.run(cmd_v1, check=True, capture_output=True)
        log("INFO", "Using 'docker-compose' (standalone v1).")
        return base_cmd + ["docker-compose"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("ERROR", "Neither 'docker compose' (plugin v2) nor 'docker-compose' (standalone v1) found or functional.")
        log("INFO", "Attempting to install 'docker-compose' (standalone v1) as a fallback.")
        try:
            if platform.system().lower() == "linux":
                subprocess.run([
                    "sudo", "curl", "-L",
                    f"https://github.com/docker/compose/releases/download/1.29.2/docker-compose-{platform.system()}-{platform.machine()}",
                    "-o", "/usr/local/bin/docker-compose"
                ], check=True)
                subprocess.run(["sudo", "chmod", "+x", "/usr/local/bin/docker-compose"], check=True)
                log("SUCCESS", "Installed 'docker-compose' (standalone v1). Please re-run the script.")
                sys.exit(1)
            else:
                log("ERROR", "Automatic installation of 'docker-compose' not supported on this OS.")
                return None
        except Exception as e:
            log("ERROR", f"Failed to install 'docker-compose': {e}")
            return None

def ensure_base_compose_config():
    """PRF-P05, P31: Ensures docker-compose.yml exists, creating a default if not."""
    log("STEP", "Ensuring base docker-compose.yml configuration...")
    compose_file = Path("docker-compose.yml")

    if not ensure_yaml_installed():
        log("ERROR", "PyYAML is required. Cannot manage docker-compose.yml.")
        return False

    if not compose_file.exists():
        log("INFO", f"{compose_file} not found. Creating a default configuration.")
        default_compose_content = {
            "version": '3.9',
            "services": {
                SERVICE_NAME_IN_COMPOSE: {
                    "image": GHCR_IMAGE_NAME,
                    "container_name": CONTAINER_NAME,
                    "network_mode": "host",
                    "volumes": [
                        "./data/source:/app/data/source",
                        "./data/output:/app/data/output"
                    ],
                    "environment": {
                        "GPG_KEY_ID": "YOUR_GPG_KEY_ID_HERE", # User must configure
                        "GPG_PASSPHRASE": "YOUR_GPG_PASSPHRASE_HERE", # User must configure
                        "PYTHONUNBUFFERED": '1'
                    },
                    "restart": "unless-stopped",
                    "healthcheck": {
                        "test": ["CMD-SHELL", f"curl -f http://localhost:{APP_PORT}/health || exit 1"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3,
                        "start_period": "30s"
                    }
                    # 'build: .' will be added by update_compose_file_to_local_image if needed
                }
            }
        }
        try:
            with open(compose_file, "w") as f:
                yaml.dump(default_compose_content, f, default_flow_style=False, sort_keys=False)
            log("SUCCESS", f"Created default {compose_file} with GHCR image and host networking.")
            log("WARN", "Please ensure GPG_KEY_ID and GPG_PASSPHRASE environment variables are correctly set for the service, either in this file or in the host environment.")
        except IOError as e:
            log("ERROR", f"Failed to write default {compose_file}: {e}")
            return False
    else:
        log("INFO", f"{compose_file} found. Will use existing file and apply necessary modifications.")
        # Optionally, validate existing file structure here if desired.
        # For now, we assume if it exists, it's somewhat usable and will be adapted.
    return True


def attempt_ghcr_pull(compose_command_parts):
    """PRF-P25: Attempt to pull the image from GHCR."""
    log("STEP", f"Attempting to pull {GHCR_IMAGE_NAME} from GHCR...")
    pull_cmd = compose_command_parts + ["pull", SERVICE_NAME_IN_COMPOSE] # Pull service from compose file
    log("INFO", f"Running: {' '.join(pull_cmd)}")
    try:
        pull_result = subprocess.run(pull_cmd, check=True, capture_output=True, text=True)
        log("SUCCESS", f"Successfully pulled image for service '{SERVICE_NAME_IN_COMPOSE}' (likely {GHCR_IMAGE_NAME}).")
        return True
    except subprocess.CalledProcessError as e:
        log("WARN", f"Failed to pull image for service '{SERVICE_NAME_IN_COMPOSE}'. Stdout: {e.stdout.strip()} Stderr: {e.stderr.strip()}")
        if "denied" in e.stderr or "authentication" in e.stderr:
            log("INFO", "GHCR access denied. This may be a private image or authentication issue.")
        log("INFO", f"Will attempt to build {LOCAL_IMAGE_NAME} locally instead.")
        return False
    except FileNotFoundError:
        log("ERROR", f"Docker command '{compose_command_parts[0]}' not found. Cannot pull image.")
        return False

def build_local_image(compose_command_parts_for_build):
    """PRF-P25: Build the Docker image locally using docker-compose build or docker build."""
    log("STEP", f"Building {LOCAL_IMAGE_NAME} locally...")
    if not Path("Dockerfile").exists():
        log("ERROR", "Dockerfile not found in current directory. Cannot build local image.")
        return False

    build_successful = False
    if Path("docker-compose.yml").exists():
        try:
            with open("docker-compose.yml", "r") as f:
                if 'yaml' not in globals():
                    if not ensure_yaml_installed():
                        raise Exception("PyYAML not available for parsing docker-compose.yml")
                compose_config = yaml.safe_load(f)
            if compose_config and "services" in compose_config and SERVICE_NAME_IN_COMPOSE in compose_config["services"]:
                log("INFO", f"Attempting build via 'docker compose build {SERVICE_NAME_IN_COMPOSE}'...")
                # Ensure the compose file points to local build for this service
                if not update_compose_file_to_local_image(force_local_image_and_build=True):
                     log("ERROR", "Failed to update compose file for local build. Cannot proceed with compose build.")
                     return False

                build_cmd = compose_command_parts_for_build + ["build", SERVICE_NAME_IN_COMPOSE]
                log("INFO", f"Running: {' '.join(build_cmd)}")
                process = subprocess.run(build_cmd, capture_output=True, text=True)
                if process.returncode == 0:
                    log("SUCCESS", f"Successfully built {LOCAL_IMAGE_NAME} via Docker Compose.")
                    build_successful = True
                else:
                    log("WARN", f"Docker Compose build failed. Stdout: {process.stdout.strip()} Stderr: {process.stderr.strip()}")
            else:
                log("INFO", f"Service '{SERVICE_NAME_IN_COMPOSE}' not found in docker-compose.yml, or file is empty/invalid.")
        except Exception as e:
            log("WARN", f"Could not parse docker-compose.yml or execute compose build: {e}")

    if not build_successful:
        log("INFO", "Falling back to 'docker build'...")
        docker_build_cmd_base = ["docker"]
        if compose_command_parts_for_build[0] == "sudo":
             docker_build_cmd_base.insert(0, "sudo")

        build_cmd = docker_build_cmd_base + ["build", "-t", LOCAL_IMAGE_NAME, "."]
        log("INFO", f"Running: {' '.join(build_cmd)}")
        process = subprocess.run(build_cmd, capture_output=True, text=True)
        if process.returncode == 0:
            log("SUCCESS", f"Successfully built {LOCAL_IMAGE_NAME} via 'docker build'.")
            # If docker build was used, ensure compose file is updated to use this locally built image
            if not update_compose_file_to_local_image(force_local_image_and_build=True):
                log("WARN", "Built image with 'docker build' but failed to update compose file to use it.")
            build_successful = True
        else:
            log("ERROR", f"Failed to build {LOCAL_IMAGE_NAME} via 'docker build'. Stdout: {process.stdout.strip()} Stderr: {process.stderr.strip()}")
            build_successful = False
            
    return build_successful

def update_compose_file_to_local_image(force_local_image_and_build=False):
    """PRF-P05: Update docker-compose.yml to use the local image and host networking."""
    log("STEP", "Updating docker-compose.yml for local image and host networking...")
    if not ensure_yaml_installed():
        log("ERROR", "PyYAML is required to update docker-compose.yml. Cannot proceed.")
        return False

    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        log("ERROR", f"{compose_file} not found. This should have been created by ensure_base_compose_config().")
        return False # Should not happen if ensure_base_compose_config ran

    try:
        with open(compose_file, "r") as f:
            compose_data = yaml.safe_load(f)

        if not compose_data or "services" not in compose_data or SERVICE_NAME_IN_COMPOSE not in compose_data["services"]:
            log("ERROR", f"Service '{SERVICE_NAME_IN_COMPOSE}' not found in {compose_file} or file is malformed. Cannot update.")
            return False

        backup_file = compose_file.with_suffix(f".yml.bak.local.{int(time.time())}")
        shutil.copy2(compose_file, backup_file)
        log("INFO", f"Backed up {compose_file} to {backup_file}")

        service_config = compose_data["services"][SERVICE_NAME_IN_COMPOSE]
        
        if force_local_image_and_build:
            service_config["image"] = LOCAL_IMAGE_NAME
            service_config["build"] = {"context": "."} 
            log("INFO", f"Set image to '{LOCAL_IMAGE_NAME}' and added build context.")

        service_config["network_mode"] = "host"
        if "ports" in service_config:
            del service_config["ports"]
            log("INFO", "Removed explicit port mappings due to host networking.")
        
        service_config["container_name"] = CONTAINER_NAME # Ensure container name is set

        with open(compose_file, "w") as f:
            yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)
        log("SUCCESS", f"{compose_file} updated for local image '{service_config['image']}', host networking, and build context (if applicable).")
        return True
    except yaml.YAMLError as e:
        log("ERROR", f"Error parsing {compose_file}: {e}")
        return False
    except IOError as e:
        log("ERROR", f"File I/O error with {compose_file}: {e}")
        return False
    except Exception as e:
        log("ERROR", f"Unexpected error updating {compose_file}: {e}")
        return False

def free_port(port, compose_command_parts):
    """PRF-P27: Check if a port is in use and attempt to free it."""
    log("STEP", f"Checking if port {port} is in use...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        log("INFO", f"Port {port} is free (socket bind check).")
        is_free = True
    except socket.error:
        log("WARN", f"Port {port} is in use (socket bind check). Attempting to stop conflicting service...")
        is_free = False
    finally:
        s.close()

    if not is_free:
        try:
            down_cmd = compose_command_parts + ["down", "--remove-orphans"]
            log("INFO", f"Running: {' '.join(down_cmd)}")
            subprocess.run(down_cmd, check=False, capture_output=True, text=True)
            log("SUCCESS", f"Attempted to stop service using port {port} via Docker Compose.")
            time.sleep(3)

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.bind(("127.0.0.1", port))
                log("INFO", f"Port {port} is now free.")
                return True
            except socket.error:
                log("ERROR", f"Port {port} is still in use after attempting to stop service.")
                return False
            finally:
                s.close()
        except Exception as e:
            log("ERROR", f"Failed to stop service using port {port}: {e}")
            return False
    return True

def launch_service(compose_command_parts, needs_sudo_for_docker_inspect=False):
    """PRF-P22, P26, P29: Launch the Supagrok service using Docker Compose."""
    log("STEP", "Launching Supagrok Snapshot Tipi Service...")

    if not free_port(APP_PORT, compose_command_parts):
        log("ERROR", f"Cannot launch service as port {APP_PORT} is occupied and could not be freed.")
        return False

    if not ensure_yaml_installed(): return False
    
    try:
        with open("docker-compose.yml", "r") as f:
            compose_data = yaml.safe_load(f)
        if SERVICE_NAME_IN_COMPOSE in compose_data.get("services", {}):
            service_config = compose_data["services"][SERVICE_NAME_IN_COMPOSE]
            if service_config.get("network_mode") != "host":
                log("INFO", "Updating docker-compose.yml to ensure host networking mode for simplicity.")
                backup_file = Path("docker-compose.yml").with_suffix(f".yml.bak.hostnet.final.{int(time.time())}")
                shutil.copy2("docker-compose.yml", backup_file)
                log("INFO", f"Backed up docker-compose.yml to {backup_file}")
                
                service_config["network_mode"] = "host"
                if "ports" in service_config:
                    del service_config["ports"]
                service_config["container_name"] = CONTAINER_NAME # Ensure container name
                with open("docker-compose.yml", "w") as f:
                    yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)
                log("SUCCESS", "docker-compose.yml updated for host networking before final launch.")
    except Exception as e:
        log("WARN", f"Could not automatically update docker-compose.yml for host networking: {e}")

    up_cmd = compose_command_parts + ["up", "-d", "--build", "--force-recreate", "--remove-orphans"]
    log("INFO", f"Running: {' '.join(up_cmd)}")
    
    try:
        process = subprocess.run(up_cmd, check=True, capture_output=True, text=True)
        log("SUCCESS", "Docker Compose 'up' command executed.")
        if process.stdout: log("INFO", f"Stdout:\n{process.stdout.strip()}")
        if process.stderr: log("INFO", f"Stderr:\n{process.stderr.strip()}")

        log("INFO", "Waiting for service to become healthy (up to 60 seconds)...")
        for i in range(12):
            time.sleep(5)
            try:
                # Check container status using Docker ps and filter by the specific container name
                # This is more reliable than compose ps -q service_name if compose file changes service name
                docker_ps_cmd = ["docker", "ps", "--filter", f"name=^{CONTAINER_NAME}$", "--format", "{{.ID}}"]
                if needs_sudo_for_docker_inspect: # Assuming if inspect needs sudo, ps might too
                    docker_ps_cmd.insert(0, "sudo")
                
                container_id_process = subprocess.run(docker_ps_cmd, capture_output=True, text=True)
                container_id = container_id_process.stdout.strip()

                if not container_id:
                    log("WARN", f"Service container '{CONTAINER_NAME}' not found running. Attempt {i+1}/12.")
                    continue

                inspect_cmd_base = ["docker", "inspect", "--format='{{json .State.Health}}'", container_id]
                inspect_cmd = ["sudo"] + inspect_cmd_base if needs_sudo_for_docker_inspect else inspect_cmd_base
                
                health_status_process = subprocess.run(inspect_cmd, capture_output=True, text=True)
                
                if health_status_process.returncode == 0 and health_status_process.stdout.strip() not in ["null", "''"]:
                    try:
                        health_info_str = health_status_process.stdout.strip().strip("'")
                        health_info = json.loads(health_info_str)
                        log("DEBUG", f"Container health info: {health_info}")
                        if health_info.get("Status") == "healthy":
                            log("SUCCESS", "Supagrok Snapshot Tipi Service is up and healthy!")
                            log("INFO", f"Service should be accessible at http://<your-server-ip>:{APP_PORT}/health (due to host networking)")
                            return True
                        else:
                            log("INFO", f"Service status: {health_info.get('Status')}. Waiting... Attempt {i+1}/12.")
                    except json.JSONDecodeError as json_e:
                        log("WARN", f"Could not parse health status JSON: {json_e}. Raw: '{health_status_process.stdout.strip()}'")
                else: 
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        if s.connect_ex(('localhost', APP_PORT)) == 0:
                            log("SUCCESS", f"Port {APP_PORT} is active. Supagrok service likely running (health check might be missing or failing).")
                            log("INFO", f"Service should be accessible at http://<your-server-ip>:{APP_PORT}/health (due to host networking)")
                            return True
            except Exception as e:
                log("WARN", f"Error checking service status: {e}. Attempt {i+1}/12.")
        
        log("ERROR", "Service did not become healthy after 60 seconds.")
        logs_cmd = compose_command_parts + ["logs", "--tail=50", SERVICE_NAME_IN_COMPOSE] # Use service name for logs
        logs_process = subprocess.run(logs_cmd, capture_output=True, text=True)
        log("INFO", f"Last 50 lines of service logs for '{SERVICE_NAME_IN_COMPOSE}':\n{logs_process.stdout.strip()}\n{logs_process.stderr.strip()}")
        return False

    except subprocess.CalledProcessError as e:
        log("ERROR", f"Service launch failed with Docker Compose. Return code: {e.returncode}")
        if e.stdout: log("INFO", f"Stdout:\n{e.stdout.strip()}")
        if e.stderr: log("ERROR", f"Stderr:\n{e.stderr.strip()}")
        return False
    except Exception as e:
        log("ERROR", f"An unexpected error occurred during service launch: {e}")
        return False

def main():
    """PRF-P22: Main execution flow."""
    log("INFO", f"Supagrok Master Launcher v{VERSION} (UUID: {SCRIPT_UUID}) starting...")
    
    if not ensure_yaml_installed():
        sys.exit(1)

    if not ensure_docker_installed():
        sys.exit(1)
    
    needs_sudo_for_docker = fix_docker_permissions()
    
    if not setup_data_directories(needs_sudo_for_chown=needs_sudo_for_docker):
        sys.exit(1)

    # PRF-P31: Ensure docker-compose.yml exists and has a base configuration.
    if not ensure_base_compose_config():
        sys.exit(1)
    
    compose_command_parts = get_compose_command(needs_sudo_for_docker)
    if not compose_command_parts:
        sys.exit(1)

    use_local_image = False
    if not attempt_ghcr_pull(compose_command_parts):
        docker_build_cmd_base = ["sudo", "docker"] if needs_sudo_for_docker else ["docker"]
        if not build_local_image(docker_build_cmd_base): # Pass base docker command for 'docker build'
            log("ERROR", "Failed to pull GHCR image and failed to build local image. Cannot proceed.")
            sys.exit(1)
        use_local_image = True # Mark that local image should be used

    # If local image was built (or GHCR pull failed), ensure compose file uses it.
    if use_local_image:
        if not update_compose_file_to_local_image(force_local_image_and_build=True):
            sys.exit(1)
    else: # GHCR pull was successful, ensure compose file is still configured for host networking
        if not update_compose_file_to_local_image(force_local_image_and_build=False): # Don't force local image, just ensure host networking
            sys.exit(1)


    if not launch_service(compose_command_parts, needs_sudo_for_docker_inspect=needs_sudo_for_docker):
        log("ERROR", "Supagrok service deployment failed.")
        sys.exit(1)
    
    log("SUCCESS", "Supagrok Master Launcher finished successfully.")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda sig, frame: (log("INFO", "Launcher interrupted."), sys.exit(1)))
    main()
