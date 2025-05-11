#!/usr/bin/env python3
# PRF-SUPAGROK-V3-MASTER-LAUNCHER-V3.0.2
# UUID: 7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d-fixed-v2
# Path: /home/supagrok/supagrok-tipiservice/supagrok_master_launcher.py
# Purpose: One-shot launcher for Supagrok Snapshot Tipi Service, ensuring environment setup and service deployment.
# PRF Relevance: P01, P02, P03, P04, P05, P06, P07, P08, P09, P10, P11, P12, P13, P14, P15, P16, P17, P18, P19, P20, P21, P22, P23, P24, P25, P26, P27, P28, P29, P30

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
VERSION = "3.0.2" # Incremented version for syntax fix
SCRIPT_UUID = "7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d-fixed-v2"

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
            return True # Still proceed, assuming it might be a minor issue or already running
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
        return False # Sudo is not "needed" for docker commands if script is already root

    username = os.environ.get("USER")
    if not username:
        log("WARN", "Could not determine current username. Docker commands might require sudo.")
        return True # Assume sudo is needed if username can't be found

    try:
        # Test if user can run docker ps without sudo
        subprocess.run(["docker", "ps"], check=True, capture_output=True)
        log("SUCCESS", f"User '{username}' can run Docker commands without sudo.")
        return False # Sudo is not needed
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("INFO", f"User '{username}' cannot run Docker commands without sudo, or Docker is not running. Attempting to add to 'docker' group.")
        try:
            subprocess.run(["sudo", "usermod", "-aG", "docker", username], check=True)
            log("SUCCESS", f"User '{username}' added to 'docker' group. A logout/login or new shell session is typically required for this to take effect.")
            log("WARN", "Docker commands will be run with sudo for this session if direct access isn't immediately available.")
            # Re-check, though group changes usually need a new session
            try:
                subprocess.run(["docker", "ps"], check=True, capture_output=True)
                log("INFO", "Docker access without sudo confirmed after group add (unexpectedly fast).")
                return False
            except:
                return True # Sudo is still needed for this session
        except subprocess.CalledProcessError as e:
            log("ERROR", f"Failed to add user '{username}' to 'docker' group: {e}. Docker commands will require sudo.")
            return True # Sudo is needed

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

        # Attempt to chown if script is run as root and SUDO_USER is set
        if os.geteuid() == 0 and os.getenv("SUDO_USER"):
            target_user = os.getenv("SUDO_USER")
            log("INFO", f"Running as root, attempting to chown {data_dir} to user {target_user}")
            try:
                subprocess.run(["chown", "-R", f"{target_user}:{target_user}", str(data_dir)], check=True)
                log("SUCCESS", f"Changed ownership of {data_dir} to {target_user}.")
            except subprocess.CalledProcessError as e:
                log("WARN", f"Failed to change ownership of {data_dir}: {e}. Container might have permission issues with volume.")
        elif needs_sudo_for_chown: # If not root, but we determined sudo is needed for other docker ops
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

    # Try 'docker compose' (plugin v2)
    try:
        cmd_v2 = base_cmd + ["docker", "compose", "version"]
        subprocess.run(cmd_v2, check=True, capture_output=True)
        log("INFO", "Using 'docker compose' (plugin v2).")
        return base_cmd + ["docker", "compose"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("INFO", "'docker compose' (plugin v2) not found or failed. Checking for standalone 'docker-compose' (v1).")

    # Try 'docker-compose' (standalone v1)
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
                # This is a common way to install v1, might need adjustment for specific distros
                subprocess.run([
                    "sudo", "curl", "-L",
                    f"https://github.com/docker/compose/releases/download/1.29.2/docker-compose-{platform.system()}-{platform.machine()}",
                    "-o", "/usr/local/bin/docker-compose"
                ], check=True)
                subprocess.run(["sudo", "chmod", "+x", "/usr/local/bin/docker-compose"], check=True)
                log("SUCCESS", "Installed 'docker-compose' (standalone v1). Please re-run the script.")
                # It's better to exit and ask user to re-run so the new command is picked up cleanly.
                sys.exit(1)
            else:
                log("ERROR", "Automatic installation of 'docker-compose' not supported on this OS.")
                return None
        except Exception as e:
            log("ERROR", f"Failed to install 'docker-compose': {e}")
            return None

def attempt_ghcr_pull(compose_command_parts):
    """PRF-P25: Attempt to pull the image from GHCR."""
    log("STEP", f"Attempting to pull {GHCR_IMAGE_NAME} from GHCR...")
    pull_cmd = compose_command_parts + ["pull", GHCR_IMAGE_NAME]
    log("INFO", f"Running: {' '.join(pull_cmd)}")
    try:
        pull_result = subprocess.run(pull_cmd, check=True, capture_output=True, text=True)
        log("SUCCESS", f"Successfully pulled {GHCR_IMAGE_NAME}.")
        return True
    except subprocess.CalledProcessError as e:
        log("WARN", f"Failed to pull {GHCR_IMAGE_NAME}. Stdout: {e.stdout.strip()} Stderr: {e.stderr.strip()}")
        if "denied" in e.stderr or "authentication" in e.stderr:
            log("INFO", "GHCR access denied. This may be a private image or authentication issue.")
        log("INFO", f"Will attempt to build {LOCAL_IMAGE_NAME} locally instead.")
        return False
    except FileNotFoundError: # If compose_command_parts[0] (e.g. "docker") is not found
        log("ERROR", f"Docker command '{compose_command_parts[0]}' not found. Cannot pull image.")
        return False


def build_local_image(compose_command_parts_for_build):
    """PRF-P25: Build the Docker image locally using docker-compose build or docker build."""
    log("STEP", f"Building {LOCAL_IMAGE_NAME} locally...")
    if not Path("Dockerfile").exists():
        log("ERROR", "Dockerfile not found in current directory. Cannot build local image.")
        return False

    # Prefer docker-compose build if SERVICE_NAME_IN_COMPOSE is defined in docker-compose.yml
    # This handles build contexts and arguments defined in the compose file.
    build_successful = False
    if Path("docker-compose.yml").exists():
        try:
            with open("docker-compose.yml", "r") as f:
                # Ensure yaml is available
                if 'yaml' not in globals():
                    if not ensure_yaml_installed():
                        raise Exception("PyYAML not available for parsing docker-compose.yml")
                compose_config = yaml.safe_load(f)
            if compose_config and "services" in compose_config and SERVICE_NAME_IN_COMPOSE in compose_config["services"]:
                log("INFO", f"Attempting build via 'docker compose build {SERVICE_NAME_IN_COMPOSE}'...")
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
        # Determine if sudo is needed for 'docker build'
        docker_build_cmd_base = ["docker"]
        if compose_command_parts_for_build[0] == "sudo": # Infer from compose command
             docker_build_cmd_base.insert(0, "sudo")

        build_cmd = docker_build_cmd_base + ["build", "-t", LOCAL_IMAGE_NAME, "."]
        log("INFO", f"Running: {' '.join(build_cmd)}")
        process = subprocess.run(build_cmd, capture_output=True, text=True)
        if process.returncode == 0:
            log("SUCCESS", f"Successfully built {LOCAL_IMAGE_NAME} via 'docker build'.")
            build_successful = True
        else:
            log("ERROR", f"Failed to build {LOCAL_IMAGE_NAME} via 'docker build'. Stdout: {process.stdout.strip()} Stderr: {process.stderr.strip()}")
            build_successful = False
            
    return build_successful


def update_compose_file_to_local_image():
    """PRF-P05: Update docker-compose.yml to use the local image and host networking."""
    log("STEP", "Updating docker-compose.yml to use local image and host networking...")
    if not ensure_yaml_installed():
        log("ERROR", "PyYAML is required to update docker-compose.yml. Cannot proceed with this step.")
        return False

    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        log("WARN", f"{compose_file} not found. Cannot update to local image.")
        # Optionally, create a default one here if desired, but for now, we'll assume it should exist or be created by user/another process.
        return False

    try:
        with open(compose_file, "r") as f:
            compose_data = yaml.safe_load(f)

        if not compose_data or "services" not in compose_data or SERVICE_NAME_IN_COMPOSE not in compose_data["services"]:
            log("ERROR", f"Service '{SERVICE_NAME_IN_COMPOSE}' not found in {compose_file} or file is malformed. Cannot update.")
            return False

        # Backup the original file
        backup_file = compose_file.with_suffix(f".yml.bak.{int(time.time())}")
        shutil.copy2(compose_file, backup_file)
        log("INFO", f"Backed up {compose_file} to {backup_file}")

        service_config = compose_data["services"][SERVICE_NAME_IN_COMPOSE]
        service_config["image"] = LOCAL_IMAGE_NAME
        service_config["build"] = {"context": "."} # Ensure build context is explicitly set
        service_config["network_mode"] = "host" # PRF-P27: Use host networking
        if "ports" in service_config: # Remove explicit port mappings if host network is used
            del service_config["ports"]

        with open(compose_file, "w") as f:
            yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False) # Corrected: yaml.dump call
        log("SUCCESS", f"{compose_file} updated to use local image '{LOCAL_IMAGE_NAME}' and host networking.")
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
    # Check with socket
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
            # Attempt to bring down compose services if they might be using the port
            down_cmd = compose_command_parts + ["down", "--remove-orphans"]
            log("INFO", f"Running: {' '.join(down_cmd)}")
            subprocess.run(down_cmd, check=False, capture_output=True, text=True) # Don't check=True, it might fail if no services are up
            log("SUCCESS", f"Attempted to stop service using port {port} via Docker Compose.")
            time.sleep(3) # Give a moment for the port to free up

            # Re-check with socket
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

    # Ensure docker-compose.yml uses host networking for the service
    if not ensure_yaml_installed(): return False # yaml might not be in globals() yet
    
    try:
        with open("docker-compose.yml", "r") as f:
            compose_data = yaml.safe_load(f)
        if SERVICE_NAME_IN_COMPOSE in compose_data.get("services", {}):
            service_config = compose_data["services"][SERVICE_NAME_IN_COMPOSE]
            if service_config.get("network_mode") != "host":
                log("INFO", "Updating docker-compose.yml to ensure host networking mode for simplicity.")
                backup_file = Path("docker-compose.yml").with_suffix(f".yml.bak.hostnet.{int(time.time())}")
                shutil.copy2("docker-compose.yml", backup_file)
                log("INFO", f"Backed up docker-compose.yml to {backup_file}")
                
                service_config["network_mode"] = "host"
                if "ports" in service_config: # Remove explicit port mappings if host network is used
                    del service_config["ports"]
                with open("docker-compose.yml", "w") as f:
                    yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)
                log("SUCCESS", "docker-compose.yml updated for host networking.")
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
        for i in range(12): # Check every 5 seconds for 60 seconds
            time.sleep(5)
            try:
                # Check container status
                ps_cmd = compose_command_parts + ["ps", "-q", SERVICE_NAME_IN_COMPOSE]
                container_id_process = subprocess.run(ps_cmd, capture_output=True, text=True)
                container_id = container_id_process.stdout.strip()

                if not container_id:
                    log("WARN", f"Service container '{SERVICE_NAME_IN_COMPOSE}' not found running. Attempt {i+1}/12.")
                    continue

                # Check health status via Docker inspect if healthcheck is defined
                inspect_cmd_base = ["docker", "inspect", "--format='{{json .State.Health}}'", container_id]
                inspect_cmd = ["sudo"] + inspect_cmd_base if needs_sudo_for_docker_inspect else inspect_cmd_base
                
                health_status_process = subprocess.run(inspect_cmd, capture_output=True, text=True)
                
                if health_status_process.returncode == 0 and health_status_process.stdout.strip() not in ["null", "''"]:
                    try:
                        # The output is like "'{\"Status\":\"healthy\",...}'" so strip quotes and parse
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
                else: # Fallback to port check if no healthcheck or inspect fails
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        if s.connect_ex(('localhost', APP_PORT)) == 0:
                            log("SUCCESS", f"Port {APP_PORT} is active. Supagrok service likely running.")
                            log("INFO", f"Service should be accessible at http://<your-server-ip>:{APP_PORT}/health (due to host networking)")
                            return True
            except Exception as e:
                log("WARN", f"Error checking service status: {e}. Attempt {i+1}/12.")
        
        log("ERROR", "Service did not become healthy after 60 seconds.")
        logs_cmd = compose_command_parts + ["logs", "--tail=50", SERVICE_NAME_IN_COMPOSE]
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
    
    # PRF-P04: Ensure PyYAML is installed first as it's used by other functions.
    if not ensure_yaml_installed():
        sys.exit(1) # Critical dependency

    if not ensure_docker_installed(): # This function attempts to install Docker if not present
        sys.exit(1)
    
    # Determine if sudo is needed for Docker commands based on current user's access
    # fix_docker_permissions returns True if sudo is needed, False otherwise.
    needs_sudo_for_docker = fix_docker_permissions()
    
    if not setup_data_directories(needs_sudo_for_chown=needs_sudo_for_docker): # Pass sudo context for chown
        sys.exit(1)
    
    compose_command_parts = get_compose_command(needs_sudo_for_docker) # Pass sudo context for compose command
    if not compose_command_parts:
        sys.exit(1)

    use_local_image = False
    if not attempt_ghcr_pull(compose_command_parts): # Pass full compose command including sudo if needed
        # Pass only the base 'docker' command part for 'docker build', with sudo if needed
        docker_build_cmd_base = ["sudo", "docker"] if needs_sudo_for_docker else ["docker"]
        if not build_local_image(docker_build_cmd_base):
            log("ERROR", "Failed to pull GHCR image and failed to build local image. Cannot proceed.")
            sys.exit(1)
        use_local_image = True

    if use_local_image:
        if not update_compose_file_to_local_image(): # This uses PyYAML, already checked
            sys.exit(1)

    if not launch_service(compose_command_parts, needs_sudo_for_docker_inspect=needs_sudo_for_docker):
        log("ERROR", "Supagrok service deployment failed.")
        sys.exit(1)
    
    log("SUCCESS", "Supagrok Master Launcher finished successfully.")

if __name__ == "__main__":
    # PRF-P17: Handle SIGINT for graceful shutdown (though less critical for a launcher)
    signal.signal(signal.SIGINT, lambda sig, frame: (log("INFO", "Launcher interrupted."), sys.exit(1)))
    main()
