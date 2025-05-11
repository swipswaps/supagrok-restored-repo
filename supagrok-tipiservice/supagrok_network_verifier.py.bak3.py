#!/usr/bin/env python3
# PRF-SUPAGROK-V3-NETWORK-VERIFIER-V3.0.1
# UUID: 5e4d3c2b-1a9f-8b7e-6d5c-4f3e2d1c0b9a-fixed-v1
# Path: /home/owner/supagrok-tipiservice/supagrok_network_verifier.py
# Purpose: Verify network connectivity to Supagrok Snapshot Service and optionally fix issues.
# PRF Relevance: P01-P30

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
import threading # For WebSocket timeout

# --- Configuration ---
DEFAULT_PORT = 8000
HEALTH_TIMEOUT = 10  # seconds
WS_TIMEOUT = 5   # seconds
SSH_OPTIONS = ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "LogLevel=ERROR"] # BatchMode=yes can be too restrictive for initial key copy
MAX_RETRIES = 1  # Number of fix attempts before giving up (kept low for one-shot feel)
SERVICE_NAME_IN_COMPOSE = "supagrok-snapshot-service" # Must match the service name in docker-compose.yml on the server
CONTAINER_NAME = "supagrok_snapshot_service_container" # Must match the container_name in docker-compose.yml
VERSION = "3.0.1"
SCRIPT_UUID = "5e4d3c2b-1a9f-8b7e-6d5c-4f3e2d1c0b9a-fixed-v1"

# --- Logging ---
def log(level, msg):
    """PRF-P07, P13: Centralized logging with clear indicators."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    icon = {"INFO": "🌀", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅", "STEP": "🛠️", "DEBUG": "🔍", "REPORT": "📊"}
    print(f"{timestamp} {icon.get(level.upper(), 'ℹ️')} [{level.upper()}] {msg}")

def ensure_websocket_client_installed():
    """PRF-P04: Ensure websocket-client is installed."""
    try:
        import websocket
        globals()["websocket"] = websocket # Make it globally available
        return True
    except ImportError:
        log("INFO", "WebSocket client not found. Attempting to install websocket-client...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"])
            import websocket
            globals()["websocket"] = websocket # Make it globally available
            log("SUCCESS", "Successfully installed websocket-client.")
            return True
        except Exception as e:
            log("ERROR", f"Failed to install websocket-client: {e}. Please install manually: pip install websocket-client")
            return False

def run_local_command(command_parts, check=True, capture_output=True, text=True, cmd_input=None, timeout=None):
    """PRF-P16: Executes a local command and handles errors."""
    log("DEBUG", f"Running local command: {' '.join(command_parts)}")
    try:
        process = subprocess.run(
            command_parts,
            check=check,
            capture_output=capture_output,
            text=text,
            input=cmd_input,
            timeout=timeout
        )
        return process
    except subprocess.TimeoutExpired:
        log("ERROR", f"Local command '{' '.join(command_parts)}' timed out after {timeout} seconds.")
        return None
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else ""
        stdout = e.stdout.strip() if e.stdout else ""
        log("ERROR", f"Local command '{' '.join(command_parts)}' failed with exit code {e.returncode}.")
        if stdout: log("INFO", f"Stdout:\n{stdout}")
        if stderr: log("ERROR", f"Stderr:\n{stderr}")
        if check: raise
        return e
    except FileNotFoundError:
        log("ERROR", f"Local command not found: {command_parts[0]}")
        if check: raise
        return None
    except Exception as e:
        log("ERROR", f"An unexpected error occurred with local command '{' '.join(command_parts)}': {e}")
        if check: raise
        return None

def run_remote_command(ssh_target, command_str, check=True, capture_output=True, text=True, timeout=30):
    """PRF-P16: Executes a command on the remote server via SSH."""
    ssh_cmd = ["ssh"] + SSH_OPTIONS + [ssh_target, command_str]
    log("DEBUG", f"Running remote command on {ssh_target}: {command_str}")
    try:
        process = subprocess.run(
            ssh_cmd,
            check=check,
            capture_output=capture_output,
            text=text,
            timeout=timeout
        )
        return process
    except subprocess.TimeoutExpired:
        log("ERROR", f"Remote command on {ssh_target} timed out after {timeout} seconds: {command_str}")
        return None
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else ""
        stdout = e.stdout.strip() if e.stdout else ""
        log("ERROR", f"Remote command '{command_str}' on {ssh_target} failed with exit code {e.returncode}.")
        if stdout: log("INFO", f"Stdout:\n{stdout}")
        if stderr: log("ERROR", f"Stderr:\n{stderr}")
        if check: raise
        return e
    except Exception as e:
        log("ERROR", f"An unexpected error occurred with remote command on {ssh_target}: {e}")
        if check: raise
        return None

def setup_ssh_key_auth(server_ip, username):
    """PRF-P18: Set up SSH key authentication to reduce password prompts."""
    log("STEP", "Setting up SSH key authentication...")
    ssh_target = f"{username}@{server_ip}"
    ssh_key_path = Path.home() / ".ssh" / "id_rsa"

    if not ssh_key_path.exists():
        log("INFO", "SSH key not found. Generating a new key...")
        keygen_cmd = ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", str(ssh_key_path), "-N", ""]
        try:
            run_local_command(keygen_cmd, check=True)
            log("SUCCESS", "SSH key generated successfully.")
        except Exception as e:
            log("ERROR", f"Failed to generate SSH key: {e}")
            return False

    # Test if passwordless access already works
    # Use BatchMode=yes for this specific test to avoid hanging on password prompt
    test_cmd_options = SSH_OPTIONS + ["-o", "BatchMode=yes", "-o", "ConnectTimeout=5"]
    test_ssh_cmd = ["ssh"] + test_cmd_options + [ssh_target, "echo 'SSH key auth test'"]
    log("DEBUG", f"Testing passwordless SSH with: {' '.join(test_ssh_cmd)}")
    test_result = run_local_command(test_ssh_cmd, check=False)

    if test_result and test_result.returncode == 0:
        log("SUCCESS", "SSH key authentication already working.")
        return True

    log("INFO", f"Attempting to copy SSH key to {ssh_target} using ssh-copy-id...")
    log("INFO", "You will likely be prompted for your SSH password for the remote server ONCE.")
    copy_cmd = ["ssh-copy-id", "-i", str(ssh_key_path.with_suffix(".pub")), ssh_target]
    
    # ssh-copy-id is interactive, so we can't easily use run_local_command with capture_output=True
    # and check=True in the same way. We'll run it and check its success based on a subsequent test.
    try:
        process = subprocess.Popen(copy_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # ssh-copy-id might prompt for password. We can't automate this part easily without expect or similar.
        # We rely on the user to enter it.
        stdout, stderr = process.communicate(timeout=60) # Give ample time for password entry
        if process.returncode != 0:
            log("WARN", f"ssh-copy-id command may have failed or had issues. Return code: {process.returncode}")
            log("INFO", f"ssh-copy-id stdout: {stdout.decode(errors='ignore').strip()}")
            log("ERROR", f"ssh-copy-id stderr: {stderr.decode(errors='ignore').strip()}")
            # Even if it "fails", it might have succeeded if key was already there.
            # The true test is the next passwordless login attempt.
    except subprocess.TimeoutExpired:
        log("ERROR", "ssh-copy-id timed out. Please ensure you can manually run ssh-copy-id.")
        return False
    except Exception as e:
        log("ERROR", f"Failed to run ssh-copy-id: {e}")
        return False

    # Test passwordless connection again after attempting ssh-copy-id
    log("INFO", "Verifying passwordless SSH connection after ssh-copy-id...")
    test_result_after_copy = run_local_command(test_ssh_cmd, check=False)
    if test_result_after_copy and test_result_after_copy.returncode == 0:
        log("SUCCESS", "Passwordless SSH connection verified after ssh-copy-id.")
        return True
    else:
        log("ERROR", "SSH key copied (or attempt made), but passwordless connection still failed. Manual SSH setup might be required.")
        return False

def verify_health_endpoint(server_ip, port, timeout=HEALTH_TIMEOUT):
    """PRF-P26: Verify that the health endpoint is accessible."""
    log("STEP", f"Verifying health endpoint at http://{server_ip}:{port}/health...")
    url = f"http://{server_ip}:{port}/health"
    log("DEBUG", f"Attempting to connect to {url}")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'SupagrokNetworkVerifier/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = response.read().decode('utf-8')
                log("SUCCESS", f"Health endpoint is accessible! Response: {data}")
                return True
            else:
                log("WARN", f"Health endpoint returned status code {response.status}.")
                return False
    except socket.timeout:
        log("ERROR", f"Failed to access health endpoint: Connection timed out after {timeout} seconds.")
        return False
    except urllib.error.URLError as e:
        log("ERROR", f"Failed to access health endpoint: {e.reason}")
        return False
    except Exception as e:
        log("ERROR", f"Failed to access health endpoint: {e}")
        return False

def verify_websocket(server_ip, port, timeout=WS_TIMEOUT):
    """PRF-P26: Verify that the WebSocket endpoint is accessible."""
    if not ensure_websocket_client_installed():
        return False
    
    log("STEP", f"Verifying WebSocket endpoint at ws://{server_ip}:{port}/ws/snapshot...")
    url = f"ws://{server_ip}:{port}/ws/snapshot"
    log("DEBUG", f"Attempting to connect to {url}")
    
    ws_app = None
    connection_status = {"connected": False, "message_received": False, "error": None}

    def on_open(ws):
        log("DEBUG", "WebSocket connection opened.")
        connection_status["connected"] = True
        # Optionally send a test message if your server expects one
        # ws.send(json.dumps({"type": "ping"}))

    def on_message(ws, message):
        log("DEBUG", f"WebSocket message received: {message}")
        connection_status["message_received"] = True # Or check for specific message
        ws.close()

    def on_error(ws, error):
        log("DEBUG", f"WebSocket error: {error}")
        connection_status["error"] = str(error)
        # ws.close() # Often already closed or will be

    def on_close(ws, close_status_code, close_msg):
        log("DEBUG", f"WebSocket connection closed. Status: {close_status_code}, Msg: {close_msg}")

    try:
        ws_app = websocket.WebSocketApp(url,
                                     on_open=on_open,
                                     on_message=on_message,
                                     on_error=on_error,
                                     on_close=on_close)
        
        wst = threading.Thread(target=ws_app.run_forever, kwargs={'ping_interval': 10, 'ping_timeout': 5})
        wst.daemon = True
        wst.start()

        # Wait for connection or timeout
        elapsed_time = 0
        while not connection_status["connected"] and elapsed_time < timeout:
            time.sleep(0.1)
            elapsed_time += 0.1
            if connection_status["error"]: # Error occurred
                break
        
        if ws_app: # Ensure ws_app was initialized
            ws_app.close() # Ensure thread is signaled to stop
        wst.join(timeout=2) # Wait for thread to finish

        if connection_status["connected"]:
            log("SUCCESS", "WebSocket connection verified!")
            return True
        elif connection_status["error"]:
            log("ERROR", f"WebSocket connection failed with error: {connection_status['error']}")
            return False
        else:
            log("ERROR", f"Failed to connect to WebSocket after {timeout} seconds.")
            return False
            
    except Exception as e:
        log("ERROR", f"Exception during WebSocket test: {e}")
        if ws_app: ws_app.close()
        return False

def check_remote_docker_status(ssh_target):
    """PRF-P26: Check if Docker is running on the remote server."""
    log("STEP", "Checking Docker status on remote server...")
    process = run_remote_command(ssh_target, "sudo docker ps", check=False)
    if process and process.returncode == 0:
        log("SUCCESS", "Docker is running on remote server.")
        return True
    else:
        log("WARN", "Docker may not be running on remote server or 'docker ps' failed.")
        if process: log("DEBUG", f"Docker ps stderr: {process.stderr}")
        return False

def check_remote_container_status(ssh_target):
    """PRF-P26: Check if the Supagrok container is running on the remote server."""
    log("STEP", f"Checking Supagrok container '{CONTAINER_NAME}' status...")
    cmd = f"sudo docker ps --filter name=^{CONTAINER_NAME}$ --format '{{{{.Names}}}}'"
    process = run_remote_command(ssh_target, cmd, check=False)
    if process and process.returncode == 0 and CONTAINER_NAME in process.stdout:
        log("SUCCESS", f"Supagrok container '{CONTAINER_NAME}' is running.")
        return True
    else:
        log("WARN", f"Supagrok container '{CONTAINER_NAME}' is not running or not found.")
        if process: log("DEBUG", f"Container status check stdout: {process.stdout} stderr: {process.stderr}")
        return False

def check_remote_port_listening(ssh_target, port):
    """PRF-P26: Check if the port is listening on the remote server."""
    log("STEP", f"Checking if port {port} is listening on remote server...")
    # Try netstat (more common)
    cmd_netstat = f"sudo netstat -tulnp | grep ':{port} ' | grep LISTEN"
    process = run_remote_command(ssh_target, cmd_netstat, check=False)
    if process and process.returncode == 0 and process.stdout.strip():
        log("SUCCESS", f"Port {port} is listening on remote server (netstat). Output:\n{process.stdout.strip()}")
        return True
    
    # Try ss (newer, might not be available or user might not have perms even with sudo for -p)
    cmd_ss = f"sudo ss -tulnp | grep ':{port} ' | grep LISTEN"
    process = run_remote_command(ssh_target, cmd_ss, check=False)
    if process and process.returncode == 0 and process.stdout.strip():
        log("SUCCESS", f"Port {port} is listening on remote server (ss). Output:\n{process.stdout.strip()}")
        return True
        
    log("WARN", f"Port {port} does not appear to be listening on remote server, or tools (netstat, ss) failed.")
    return False

def fix_remote_connectivity(server_ip, port, username):
    """PRF-P18, P27: Fix connectivity issues on the remote server."""
    log("STEP", f"Attempting to fix connectivity issues on {server_ip}...")
    ssh_target = f"{username}@{server_ip}"

    fix_script_content = f"""#!/bin/bash
# PRF-SUPAGROK-V3-QUICK-FIX-V1.2
# Purpose: Quick fix for network connectivity issues, focusing on firewall and service state.
set -e

TARGET_PORT="{port}"
SERVICE_NAME="{SERVICE_NAME_IN_COMPOSE}"
PROJECT_DIR_NAME="supagrok-tipiservice" # Assuming this is the project directory name

echo "🛠️ [STEP] Starting Supagrok Quick Fix (v1.2) for port $TARGET_PORT and service $SERVICE_NAME..."

# Find project directory
PROJECT_PATH=$(find ~ -name "$PROJECT_DIR_NAME" -type d -print -quit 2>/dev/null)
if [ -z "$PROJECT_PATH" ]; then
    echo "❌ [ERROR] Project directory '$PROJECT_DIR_NAME' not found in user's home. Cannot proceed with compose commands."
    PROJECT_PATH="." # Fallback to current directory, though likely won't work if not already there
else
    echo "🌀 [INFO] Found project directory at $PROJECT_PATH. Changing to it."
    cd "$PROJECT_PATH" || {{ echo "❌ [ERROR] Failed to cd to $PROJECT_PATH"; exit 1; }}
fi
echo "Current directory for compose commands: $(pwd)"

# 1. Ensure Docker service is running
echo "🌀 [INFO] Ensuring Docker service is running..."
if ! sudo systemctl is-active --quiet docker; then
    echo "🌀 [INFO] Docker service is not active. Starting Docker..."
    sudo systemctl start docker
    sudo systemctl status docker --no-pager || echo "⚠️ Docker status check failed after start attempt."
else
    echo "✅ [SUCCESS] Docker service is active."
fi

# 2. Ensure firewall allows the target port
echo "🌀 [INFO] Ensuring firewall allows port $TARGET_PORT..."
if command -v ufw &> /dev/null && sudo ufw status | grep -qw active; then
    echo "🌀 [INFO] UFW detected. Checking rule for port $TARGET_PORT..."
    if sudo ufw status | grep -qw "$TARGET_PORT[/tcp]* ALLOW"; then # More flexible grep
        echo "✅ [SUCCESS] UFW rule for port $TARGET_PORT already allows traffic."
    else
        echo "🌀 [INFO] UFW rule for port $TARGET_PORT not found or not allowing. Adding rule..."
        sudo ufw allow $TARGET_PORT/tcp
        sudo ufw status verbose
        echo "✅ [SUCCESS] UFW rule added/updated for port $TARGET_PORT."
    fi
elif command -v firewall-cmd &> /dev/null && sudo systemctl is-active --quiet firewalld; then
    echo "🌀 [INFO] Firewalld detected. Checking rule for port $TARGET_PORT..."
    if sudo firewall-cmd --list-ports --permanent | grep -qw "$TARGET_PORT/tcp"; then
        echo "✅ [SUCCESS] Firewalld rule for port $TARGET_PORT already exists."
    else
        echo "🌀 [INFO] Firewalld rule for port $TARGET_PORT not found. Adding rule..."
        sudo firewall-cmd --permanent --add-port=$TARGET_PORT/tcp
        sudo firewall-cmd --reload
        echo "✅ [SUCCESS] Firewalld rule added for port $TARGET_PORT."
    fi
else
    echo "⚠️ [WARN] No active UFW or Firewalld detected/managed. Manual firewall check might be needed if external access fails."
fi

# 3. Check Docker Compose command
COMPOSE_CMD_EXEC="sudo docker-compose"
if sudo docker compose version &>/dev/null; then
    COMPOSE_CMD_EXEC="sudo docker compose"
    echo "🌀 [INFO] Using 'docker compose' (plugin v2 with sudo)."
else
    echo "🌀 [INFO] Using 'docker-compose' (standalone v1 with sudo)."
fi

# 4. Ensure the service is up and running (restart if necessary)
echo "🛠️ [STEP] Attempting to restart service '$SERVICE_NAME' via Docker Compose..."
# This assumes docker-compose.yml is correctly configured by supagrok_master_launcher.py
# (e.g., network_mode: "host", correct image)
# We use --force-recreate to ensure it picks up any changes if the container was stuck.
# We avoid --build as the image should be correct from the master_launcher.
$COMPOSE_CMD_EXEC up -d --force-recreate --remove-orphans $SERVICE_NAME
sleep 5 # Give it time to (re)start

# 5. Verify service container status
echo "🛠️ [STEP] Verifying service '$SERVICE_NAME' container status..."
if $COMPOSE_CMD_EXEC ps | grep $SERVICE_NAME | grep -qi "Up"; then
    echo "✅ [SUCCESS] Container for service '$SERVICE_NAME' is running."
else
    echo "⚠️ [WARN] Container for service '$SERVICE_NAME' does not appear to be running or healthy after restart attempt."
    echo "🌀 [INFO] Displaying last 20 lines of logs for '$SERVICE_NAME':"
    $COMPOSE_CMD_EXEC logs --tail=20 $SERVICE_NAME
fi

# 6. Check if port is listening locally
echo "🛠️ [STEP] Checking if port $TARGET_PORT is listening locally..."
if sudo netstat -tulnp | grep -q ":$TARGET_PORT "; then
    echo "✅ [SUCCESS] Port $TARGET_PORT is listening locally (netstat)."
elif sudo ss -tulnp | grep -q ":$TARGET_PORT "; then
    echo "✅ [SUCCESS] Port $TARGET_PORT is listening locally (ss)."
else
    echo "⚠️ [WARN] Port $TARGET_PORT is NOT listening locally after fix attempt. This is unexpected with host networking."
fi

echo "✅ [SUCCESS] Supagrok Quick Fix (v1.2) completed!"
echo "🌀 [INFO] Service should now be correctly configured and running."
echo "🌀 [INFO] Please re-verify external connectivity from your local machine: curl http://<your-server-ip>:$TARGET_PORT/health"
"""

    remote_script_path = "/tmp/supagrok_quick_fix.sh"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, prefix='supagrok_local_fix_script_', suffix='.sh') as temp_file:
        temp_file.write(fix_script_content)
        local_script_path = temp_file.name
    
    try:
        os.chmod(local_script_path, 0o755)
        log("DEBUG", f"Created temporary local fix script at {local_script_path}")

        scp_cmd = ["scp", SSH_OPTIONS[0], SSH_OPTIONS[1], SSH_OPTIONS[2], SSH_OPTIONS[3], local_script_path, f"{ssh_target}:{remote_script_path}"]
        scp_process = run_local_command(scp_cmd, check=False)
        if not scp_process or scp_process.returncode != 0:
            log("ERROR", f"Failed to copy fix script to remote server: {ssh_target}:{remote_script_path}")
            return False
        log("SUCCESS", "Fix script copied to remote server.")

        chmod_cmd_str = f"chmod +x {remote_script_path}"
        run_remote_command(ssh_target, chmod_cmd_str, check=True)

        # Execute the script on the remote server. It will cd into the project dir.
        # The project dir is assumed to be ~/supagrok-tipiservice
        exec_cmd_str = f"cd ~/supagrok-tipiservice && {remote_script_path}"
        log("INFO", f"Executing remote fix script: {exec_cmd_str}")
        fix_process = run_remote_command(ssh_target, exec_cmd_str, check=False, capture_output=True, timeout=120)

        if fix_process and fix_process.returncode == 0:
            log("SUCCESS", "Fix script executed successfully on remote server.")
            log("INFO", f"Fix script output:\n{fix_process.stdout.strip()}")
            return True
        else:
            log("ERROR", "Fix script execution failed on remote server.")
            if fix_process:
                log("INFO", f"Fix script stdout:\n{fix_process.stdout.strip()}")
                log("ERROR", f"Fix script stderr:\n{fix_process.stderr.strip()}")
            return False
    finally:
        log("DEBUG", f"Cleaning up local temporary script: {local_script_path}")
        if os.path.exists(local_script_path):
            os.unlink(local_script_path)
        log("DEBUG", "Cleaning up remote temporary script...")
        run_remote_command(ssh_target, f"rm -f {remote_script_path}", check=False)
        log("DEBUG", "Remote script cleanup attempted.")

def get_remote_logs(ssh_target):
    """PRF-P26, P30: Get logs from the remote container for diagnostics."""
    log("STEP", f"Retrieving logs for container '{CONTAINER_NAME}' from remote server...")
    # Determine compose command on remote
    cmd_check_compose_v2 = "if sudo docker compose version &>/dev/null; then echo 'docker compose'; else echo 'docker-compose'; fi"
    process = run_remote_command(ssh_target, cmd_check_compose_v2, capture_output=True, text=True, check=False)
    
    compose_cmd_base = "sudo docker-compose" # Default to v1
    if process and process.returncode == 0 and "docker compose" in process.stdout:
        compose_cmd_base = "sudo docker compose"
    
    # The project dir is assumed to be ~/supagrok-tipiservice
    logs_cmd_str = f"cd ~/supagrok-tipiservice && {compose_cmd_base} logs --tail 50 {SERVICE_NAME_IN_COMPOSE}"
    process = run_remote_command(ssh_target, logs_cmd_str, check=False, capture_output=True)
    
    if process and process.returncode == 0:
        log("DEBUG", f"Retrieved container logs:\n{process.stdout.strip()}")
        return process.stdout.strip()
    else:
        log("WARN", "Failed to retrieve container logs.")
        if process:
            log("DEBUG", f"Get logs stdout: {process.stdout.strip()}")
            log("DEBUG", f"Get logs stderr: {process.stderr.strip()}")
        return None

def generate_report(server_ip, port, health_ok, ws_ok, docker_running=None, container_running=None, port_listening=None, logs=None):
    """PRF-P28: Generate a summary report of the verification results."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "server_ip": server_ip,
        "port": port,
        "health_endpoint": {
            "status": "accessible" if health_ok else "not_accessible",
            "url": f"http://{server_ip}:{port}/health"
        },
        "websocket_endpoint": {
            "status": "accessible" if ws_ok else "not_accessible",
            "url": f"ws://{server_ip}:{port}/ws/snapshot"
        }
    }
    if docker_running is not None:
        report["remote_docker_status"] = "running" if docker_running else "not_running_or_failed_check"
    if container_running is not None:
        report["remote_container_status"] = "running" if container_running else "not_running_or_not_found"
    if port_listening is not None:
        report["remote_port_listening_status"] = "listening" if port_listening else "not_listening"
    if logs:
        report["remote_logs_excerpt"] = logs.strip().split('\n')[-20:] # Last 20 lines

    log("REPORT", "Verification Report:")
    print(json.dumps(report, indent=2))
    return report

def main():
    """PRF-P22: Main execution flow."""
    parser = argparse.ArgumentParser(
        description=f"Supagrok Network Verifier v{VERSION}. Verifies and optionally fixes network connectivity to a Supagrok service.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("server_ip", help="IP address of the Supagrok server.")
    parser.add_argument("-p", "--port", type=int, default=DEFAULT_PORT, help=f"Port number for the Supagrok service (default: {DEFAULT_PORT}).")
    parser.add_argument("-u", "--username", required=True, help="SSH username for the remote server (e.g., 'supagrok' or 'owner').")
    parser.add_argument("--setup-ssh", action="store_true", help="Set up SSH key authentication for passwordless access. Run this once if password prompts are frequent.")
    parser.add_argument("--fix", action="store_true", help="Attempt to automatically fix connectivity issues on the remote server if verification fails.")
    parser.add_argument("--diagnose-remote", action="store_true", help="Run remote diagnostics (Docker status, container status, port listening status on server).")
    parser.add_argument("--get-logs", action="store_true", help="Retrieve the last 50 lines of remote container logs.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging (sets log level to DEBUG).")

    args = parser.parse_args()

    if args.verbose:
        # This simple logger doesn't have levels, but we can print DEBUG messages
        # A more sophisticated logger would set a level.
        log("INFO", "Verbose mode enabled (DEBUG messages will be shown).")

    log("INFO", f"Starting Supagrok Network Verifier v{VERSION} for {args.server_ip}:{args.port}...")

    if not ensure_websocket_client_installed():
        log("ERROR", "WebSocket client is required. Please install 'websocket-client' and try again.")
        sys.exit(1)

    if args.setup_ssh:
        if not args.username:
            log("ERROR", "SSH username (-u/--username) is required for --setup-ssh.")
            sys.exit(1)
        setup_ssh_key_auth(args.server_ip, args.username)
        log("INFO", "SSH key setup process completed. You can now try running the verifier again. For SSH operations, it should now be passwordless if setup was successful.")
        # return # Optionally exit here to let user confirm, or continue

    health_ok = verify_health_endpoint(args.server_ip, args.port)
    ws_ok = verify_websocket(args.server_ip, args.port)

    docker_running, container_running, port_listening, remote_logs_data = None, None, None, None
    ssh_target = f"{args.username}@{args.server_ip}"

    if args.diagnose_remote or args.get_logs or (args.fix and not (health_ok and ws_ok)):
        if not args.username:
            log("ERROR", "SSH username (-u/--username) is required for remote diagnostics or fixes.")
            if not (health_ok and ws_ok) and args.fix: sys.exit(1)
        else:
            log("INFO", f"Attempting SSH connection to {ssh_target} for diagnostics/fix...")
            # Test SSH connection before proceeding with more operations
            ssh_test_process = run_remote_command(ssh_target, "echo SSH_OK", check=False)
            if not ssh_test_process or ssh_test_process.returncode != 0:
                log("ERROR", f"Failed to establish SSH connection to {ssh_target}. Please check credentials and network.")
                if not (health_ok and ws_ok) and args.fix: sys.exit(1) # Critical if fix is needed
            else:
                log("SUCCESS", f"SSH connection to {ssh_target} successful.")
                if args.diagnose_remote:
                    docker_running = check_remote_docker_status(ssh_target)
                    if docker_running: # Only check container and port if Docker is running
                        container_running = check_remote_container_status(ssh_target)
                        port_listening = check_remote_port_listening(ssh_target, args.port)
                if args.get_logs:
                    remote_logs_data = get_remote_logs(ssh_target)

    print("\n" + "="*60)
    log("REPORT", "INITIAL VERIFICATION SUMMARY:")
    log("REPORT", f"Server: {args.server_ip}:{args.port}")
    log("REPORT", f"HTTP Health Endpoint (/health): {'✅ Accessible' if health_ok else '❌ Not Accessible'}")
    log("REPORT", f"WebSocket Endpoint (/ws/snapshot): {'✅ Accessible' if ws_ok else '❌ Not Accessible'}")
    if args.diagnose_remote:
        log("REPORT", f"Remote Docker Service Status: {'✅ Running' if docker_running else '❌ Not Running' if docker_running is not None else '❔ Not Checked'}")
        log("REPORT", f"Remote Container '{CONTAINER_NAME}' Status: {'✅ Running' if container_running else '❌ Not Running' if container_running is not None else '❔ Not Checked'}")
        log("REPORT", f"Remote Port {args.port} Listening: {'✅ Listening' if port_listening else '❌ Not Listening' if port_listening is not None else '❔ Not Checked'}")
    if remote_logs_data:
        log("REPORT", f"Remote Container Logs (last 50 lines):\n{remote_logs_data}")
    print("="*60 + "\n")

    if not (health_ok and ws_ok) and args.fix:
        log("STEP", "Connectivity issues detected. Attempting to apply remote fix...")
        if not args.username:
            log("ERROR", "SSH username (-u/--username) is required to attempt fixes.")
            sys.exit(1)
        
        fix_successful = fix_remote_connectivity(args.server_ip, args.port, args.username)
        if fix_successful:
            log("INFO", "Fix attempt completed. Waiting 10 seconds for service to stabilize before re-verifying...")
            time.sleep(10)
            log("INFO", "Re-verifying connectivity...")
            health_ok_after_fix = verify_health_endpoint(args.server_ip, args.port)
            ws_ok_after_fix = verify_websocket(args.server_ip, args.port)
            
            print("\n" + "="*60)
            log("REPORT", "POST-FIX VERIFICATION SUMMARY:")
            log("REPORT", f"Server: {args.server_ip}:{args.port}")
            log("REPORT", f"HTTP Health Endpoint (/health): {'✅ Accessible' if health_ok_after_fix else '❌ Not Accessible'}")
            log("REPORT", f"WebSocket Endpoint (/ws/snapshot): {'✅ Accessible' if ws_ok_after_fix else '❌ Not Accessible'}")
            print("="*60 + "\n")
            
            if health_ok_after_fix and ws_ok_after_fix:
                log("SUCCESS", "Service is now accessible after fix!")
                sys.exit(0)
            else:
                log("ERROR", "Service is still not accessible after fix attempt.")
                if args.get_logs or args.diagnose_remote: # If logs were not fetched before, fetch now
                    remote_logs_data_after_fix = get_remote_logs(ssh_target)
                    if remote_logs_data_after_fix:
                        log("REPORT", f"Remote Container Logs (after fix attempt):\n{remote_logs_data_after_fix}")
                sys.exit(1)
        else:
            log("ERROR", "Fix attempt failed or was not fully successful.")
            sys.exit(1)
    elif not (health_ok and ws_ok):
        log("ERROR", "Service is not accessible. Run with --fix to attempt automatic correction.")
        sys.exit(1)
    else:
        log("SUCCESS", "Service is accessible and healthy.")
        sys.exit(0)

if __name__ == "__main__":
    # Handle SIGINT for graceful shutdown (though less critical for a verifier)
    signal.signal(signal.SIGINT, lambda sig, frame: (log("INFO", "Verifier interrupted."), sys.exit(1)))
    main()

