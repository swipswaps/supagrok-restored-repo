#!/usr/bin/env python3
# PRF-SUPAGROK-V3-NETWORK-DOCTOR-V1.0
# UUID: f8b3d9c1-a0e5-4f2b-8c7d-1e9a0b3d7f2a
# Path: (Save this script on your local machine, e.g., ~/supagrok_network_doctor.py)
# Purpose: Diagnose and attempt to fix network connectivity issues for the Supagrok Snapshot Tipi service on a remote server.
#          Includes SSH key setup, remote script execution for server-side fixes, and local verification.
# PRF Relevance: P01, P02, P03, P04, P05, P06, P07, P08, P09, P10, P11, P12, P13, P14, P15, P16, P17, P18, P19, P20, P21, P22, P23, P24, P25, P26, P27, P28, P29, P30

import os
import sys
import subprocess
import time
import socket
import json
import argparse
import tempfile
from pathlib import Path
from datetime import datetime

try:
    import websocket
except ImportError:
    print("⚠️ [WARN] Python 'websocket-client' library not found. Attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"])
        import websocket
        print("✅ [SUCCESS] 'websocket-client' installed successfully.")
    except Exception as e:
        print(f"❌ [ERROR] Failed to install 'websocket-client': {e}. Please install it manually ('pip install websocket-client') and re-run.")
        sys.exit(1)

# --- Configuration ---
DEFAULT_PORT = 8000
HEALTH_TIMEOUT = 10  # seconds for health check
WS_TIMEOUT = 10      # seconds for WebSocket check
SSH_CONNECT_TIMEOUT = 15 # seconds for SSH connection
REMOTE_SCRIPT_PATH = "/tmp/supagrok_server_fix.sh"
REMOTE_APP_DIR = "~/supagrok-tipiservice" # Standardized path on the server
VERSION = "1.0"
SCRIPT_UUID = "f8b3d9c1-a0e5-4f2b-8c7d-1e9a0b3d7f2a"

# --- Logging ---
def log(level, msg):
    icon = {"INFO": "🌀", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅", "STEP": "🛠️", "DEBUG": "🔍", "REPORT": "📊"}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} {icon.get(level.upper(), 'ℹ️')} [{level.upper()}] {msg}")

# --- Command Execution Utility ---
def run_local_command(command_parts, check=True, capture_output=False, text=True, timeout=None, cmd_input=None):
    log("INFO", f"Executing locally: {' '.join(command_parts)}")
    try:
        process = subprocess.run(
            command_parts,
            check=check,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            input=cmd_input,
            env=os.environ.copy()
        )
        if capture_output:
            log("DEBUG", f"Stdout: {process.stdout.strip() if process.stdout else 'None'}")
            log("DEBUG", f"Stderr: {process.stderr.strip() if process.stderr else 'None'}")
        return process
    except subprocess.CalledProcessError as e:
        stderr = e.stderr if e.stderr else ""
        stdout = e.stdout if e.stdout else ""
        log("ERROR", f"Local command '{' '.join(command_parts)}' failed with exit code {e.returncode}.")
        if stdout: log("INFO", f"Stdout:\n{stdout.strip()}")
        if stderr: log("ERROR", f"Stderr:\n{stderr.strip()}")
        if check: raise
        return e
    except subprocess.TimeoutExpired:
        log("ERROR", f"Local command '{' '.join(command_parts)}' timed out after {timeout} seconds.")
        if check: raise
        return None
    except FileNotFoundError:
        log("ERROR", f"Local command not found: {command_parts[0]}")
        if check: raise
        return None
    except Exception as e:
        log("ERROR", f"An unexpected error occurred with local command '{' '.join(command_parts)}': {e}")
        if check: raise
        return None

def run_remote_command(ssh_target, command, check=True, capture_output=False, timeout=30):
    ssh_cmd = ["ssh", "-o", f"ConnectTimeout={SSH_CONNECT_TIMEOUT}", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", ssh_target, command]
    log("INFO", f"Executing on {ssh_target}: {command}")
    try:
        process = subprocess.run(ssh_cmd, check=check, capture_output=capture_output, text=True, timeout=timeout)
        if capture_output:
            log("DEBUG", f"Remote stdout: {process.stdout.strip() if process.stdout else 'None'}")
            log("DEBUG", f"Remote stderr: {process.stderr.strip() if process.stderr else 'None'}")
        return process
    except subprocess.CalledProcessError as e:
        stderr = e.stderr if e.stderr else ""
        stdout = e.stdout if e.stdout else ""
        log("ERROR", f"Remote command '{command}' on {ssh_target} failed with exit code {e.returncode}.")
        if stdout: log("INFO", f"Stdout:\n{stdout.strip()}")
        if stderr: log("ERROR", f"Stderr:\n{stderr.strip()}")
        if check: raise
        return e
    except subprocess.TimeoutExpired:
        log("ERROR", f"Remote command '{command}' on {ssh_target} timed out after {timeout} seconds.")
        if check: raise
        return None
    except Exception as e:
        log("ERROR", f"An unexpected error occurred with remote command '{command}' on {ssh_target}: {e}")
        if check: raise
        return None

def setup_ssh_key_auth(server_ip, username):
    log("STEP", f"Setting up SSH key-based authentication for {username}@{server_ip}...")
    ssh_key_path = Path.home() / ".ssh" / "id_rsa"
    ssh_target = f"{username}@{server_ip}"

    if not ssh_key_path.exists():
        log("INFO", f"SSH key {ssh_key_path} not found. Generating a new key...")
        try:
            run_local_command(["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", str(ssh_key_path), "-N", ""], check=True)
            log("SUCCESS", "New SSH key generated.")
        except Exception as e:
            log("ERROR", f"Failed to generate SSH key: {e}")
            return False

    log("INFO", f"Attempting to copy SSH key to {ssh_target} using ssh-copy-id. You may be prompted for the password.")
    try:
        # ssh-copy-id can be interactive, so we don't use BatchMode=yes here
        copy_cmd = ["ssh-copy-id", "-o", "StrictHostKeyChecking=no", ssh_target]
        log("INFO", f"Please enter the password for {ssh_target} if prompted.")
        process = subprocess.run(copy_cmd, check=True, text=True, input=None) # Allow interactive password prompt
        log("SUCCESS", f"SSH key copied to {ssh_target}.")
    except subprocess.CalledProcessError as e:
        log("ERROR", f"Failed to copy SSH key to {ssh_target}. Error: {e.stderr}")
        log("INFO", "Please ensure you can SSH to the server with password authentication and that ssh-copy-id is installed locally.")
        return False
    except FileNotFoundError:
        log("ERROR", "ssh-copy-id command not found. Please install it or manually copy your public key.")
        return False

    log("INFO", "Verifying passwordless SSH connection...")
    try:
        run_remote_command(ssh_target, "echo 'SSH key authentication successful'", check=True, capture_output=True)
        log("SUCCESS", "Passwordless SSH connection verified.")
        return True
    except Exception as e:
        log("ERROR", f"Passwordless SSH connection test failed: {e}")
        return False

def verify_health_endpoint(server_ip, port, timeout=HEALTH_TIMEOUT):
    log("STEP", f"Verifying health endpoint at http://{server_ip}:{port}/health...")
    url = f"http://{server_ip}:{port}/health"
    try:
        response = urllib.request.urlopen(url, timeout=timeout)
        if response.status == 200:
            data = response.read().decode('utf-8')
            log("SUCCESS", f"Health endpoint is accessible! Response: {data}")
            return True, data
        else:
            log("WARN", f"Health endpoint returned status code {response.status}.")
            return False, f"Status code: {response.status}"
    except socket.timeout:
        log("ERROR", f"Health endpoint connection timed out after {timeout} seconds.")
        return False, "Timeout"
    except urllib.error.URLError as e:
        log("ERROR", f"Failed to access health endpoint: {e.reason}")
        return False, str(e.reason)
    except Exception as e:
        log("ERROR", f"Unexpected error accessing health endpoint: {e}")
        return False, str(e)

def verify_websocket(server_ip, port, path="/ws/snapshot", timeout=WS_TIMEOUT):
    log("STEP", f"Verifying WebSocket endpoint at ws://{server_ip}:{port}{path}...")
    url = f"ws://{server_ip}:{port}{path}"
    
    result_queue = [] # Using a list as a simple queue for thread communication

    def on_open(ws):
        log("SUCCESS", "WebSocket connection established!")
        result_queue.append(True)
        ws.close()

    def on_error(ws, error):
        log("ERROR", f"WebSocket error: {error}")
        result_queue.append(False)
        # ws.close() # ws might already be closed or in an error state

    def on_close(ws, close_status_code, close_msg):
        log("INFO", f"WebSocket connection closed. Status: {close_status_code}, Msg: {close_msg}")
        if not result_queue: # If on_open or on_error wasn't called
            result_queue.append(False)

    ws_app = websocket.WebSocketApp(url,
                                  on_open=on_open,
                                  on_error=on_error,
                                  on_close=on_close)
    
    wst = threading.Thread(target=ws_app.run_forever)
    wst.daemon = True
    wst.start()

    wst.join(timeout=timeout) # Wait for the thread to finish or timeout

    if wst.is_alive():
        log("WARN", f"WebSocket connection attempt timed out after {timeout} seconds. Closing.")
        ws_app.close() # Attempt to close the socket if it's still open
        return False, "Timeout"
    
    if result_queue and result_queue[0]:
        return True, "Connected"
    else:
        log("ERROR", f"Failed to connect to WebSocket at {url}.")
        return False, "Connection failed or error"

def create_server_fix_script_content(app_dir, port, container_name, service_name):
    return f"""#!/bin/bash
# PRF-SUPAGROK-SERVER-FIX-V1.0
# This script is run on the remote server to fix Supagrok service issues.

set -e # Exit immediately if a command exits with a non-zero status.

APP_DIR="{app_dir}"
PORT="{port}"
CONTAINER_NAME="{container_name}"
SERVICE_NAME="{service_name}" # Service name in docker-compose.yml

log_remote() {{
    echo "🌀 [REMOTE] $1"
}}

log_remote "Starting Supagrok Server Fix Script..."

# 1. Ensure Docker service is running
log_remote "Ensuring Docker service is running..."
if ! sudo systemctl is-active --quiet docker; then
    log_remote "Docker service is not active. Attempting to start..."
    sudo systemctl start docker
    sleep 5 # Give it a moment to start
    if ! sudo systemctl is-active --quiet docker; then
        log_remote "❌ [REMOTE] Failed to start Docker service. Please check Docker installation."
        exit 1
    fi
    log_remote "✅ [REMOTE] Docker service started."
else
    log_remote "✅ [REMOTE] Docker service is active."
fi

# 2. Ensure UFW is configured (if active)
log_remote "Checking UFW status..."
if sudo ufw status | grep -q "Status: active"; then
    log_remote "UFW is active. Ensuring port $PORT is allowed..."
    if sudo ufw status | grep -q "$PORT/tcp.*ALLOW"; then
        log_remote "✅ [REMOTE] Port $PORT/tcp is already allowed in UFW."
    else
        log_remote "Port $PORT/tcp is not allowed. Adding rule..."
        sudo ufw allow $PORT/tcp
        # sudo ufw reload # Reload might disconnect SSH if not careful, often rules apply immediately or on next restart
        log_remote "✅ [REMOTE] UFW rule for port $PORT/tcp added. You might need to reload UFW manually if changes don't take effect."
    fi
else
    log_remote "UFW is inactive or not installed. Skipping UFW configuration."
fi

# 3. Navigate to the application directory
log_remote "Changing to application directory: $APP_DIR"
if [ ! -d "$APP_DIR" ]; then
    log_remote "❌ [REMOTE] Application directory $APP_DIR does not exist. Please ensure the service files are present."
    exit 1
fi
cd "$APP_DIR"

# 4. Ensure docker-compose.yml is present and configured for host networking
log_remote "Ensuring docker-compose.yml is configured for host networking..."
COMPOSE_FILE="docker-compose.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    log_remote "❌ [REMOTE] $COMPOSE_FILE not found in $APP_DIR. Creating a default one."
    cat << EOF > $COMPOSE_FILE
version: '3.9'
services:
  {SERVICE_NAME}:
    image: supagrok/snapshot-tipiservice:local
    container_name: {CONTAINER_NAME}
    network_mode: "host"
    volumes:
      - ./data/source:/app/data/source
      - ./data/output:/app/data/output
    environment:
      GPG_KEY_ID: "tipi-backup@supagrok.io"
      PYTHONUNBUFFERED: '1'
      # GPG_PASSPHRASE should be set via .env file or other secure means
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:{PORT}/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    build:
      context: .
      dockerfile: Dockerfile
EOF
    log_remote "✅ [REMOTE] Default $COMPOSE_FILE created with host networking."
    log_remote "⚠️ [REMOTE] IMPORTANT: You may need to set GPG_PASSPHRASE in a .env file or directly in the environment for the service to function fully."
else
    # Create a backup
    cp "$COMPOSE_FILE" "${COMPOSE_FILE}.bak.$(date +%s)"
    log_remote "Backed up $COMPOSE_FILE to ${COMPOSE_FILE}.bak.*"

    # Use Python to modify YAML safely if available, otherwise use sed (less robust)
    if command -v python3 &> /dev/null && python3 -c "import yaml" &> /dev/null; then
        log_remote "Using Python to update docker-compose.yml for host networking."
        python3 -c "
import yaml, sys
compose_file_path = '$COMPOSE_FILE'
service_name = '$SERVICE_NAME'
container_name_val = '$CONTAINER_NAME'
try:
    with open(compose_file_path, 'r') as f:
        data = yaml.safe_load(f)
    if 'services' not in data or not isinstance(data['services'], dict): data['services'] = {{}}
    if service_name not in data['services']: data['services'][service_name] = {{}} # Create service if not exists
    
    data['services'][service_name]['network_mode'] = 'host'
    data['services'][service_name]['container_name'] = container_name_val
    if 'ports' in data['services'][service_name]:
        del data['services'][service_name]['ports']
    if 'build' not in data['services'][service_name]: # Ensure build context if not present
        data['services'][service_name]['build'] = {{'context': '.'}}
    if 'image' not in data['services'][service_name]: # Ensure image name if not present
        data['services'][service_name]['image'] = 'supagrok/snapshot-tipiservice:local'

    with open(compose_file_path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)
    print(f'✅ [REMOTE] {compose_file_path} updated for host networking and container name.')
except Exception as e:
    print(f'❌ [REMOTE] Error updating {compose_file_path} with Python: {{e}}')
    sys.exit(1)
"
    else
        log_remote "Python or PyYAML not found, using sed to update docker-compose.yml (less robust)."
        # Ensure service entry exists (very basic check)
        grep -q "^\s*${SERVICE_NAME}:" "$COMPOSE_FILE" || echo -e "\nservices:\n  ${SERVICE_NAME}:" >> "$COMPOSE_FILE"
        
        # Remove existing ports section for the service
        sed -i "/^\s*${SERVICE_NAME}:/,/^\s*[[:alnum:]]/ {{ /^\s*ports:/,/^\s*-/d; }}" "$COMPOSE_FILE"
        
        # Add/update network_mode: host
        if grep -q "^\s*network_mode:\s*host" "$COMPOSE_FILE"; then
            log_remote "network_mode: host already set."
        else
            sed -i "/^\s*${SERVICE_NAME}:/a \ \ \ \ network_mode: \"host\"" "$COMPOSE_FILE"
            log_remote "Added network_mode: host."
        fi
        # Add/update container_name
        if grep -q "^\s*container_name:\s*${CONTAINER_NAME}" "$COMPOSE_FILE"; then
            log_remote "container_name: ${CONTAINER_NAME} already set."
        else
            sed -i "/^\s*${SERVICE_NAME}:/a \ \ \ \ container_name: ${CONTAINER_NAME}" "$COMPOSE_FILE"
            log_remote "Added container_name: ${CONTAINER_NAME}."
        fi
    fi
fi

# 5. Stop and remove the specific container if it exists
log_remote "Checking for existing container '$CONTAINER_NAME'..."
if sudo docker ps -a --format '{{{{.Names}}}}' | grep -Eq "^${CONTAINER_NAME}$"; then
    log_remote "Container '$CONTAINER_NAME' found. Stopping and removing..."
    sudo docker stop "$CONTAINER_NAME" || log_remote "⚠️ [REMOTE] Could not stop container (maybe already stopped)."
    sudo docker rm -f "$CONTAINER_NAME" || log_remote "⚠️ [REMOTE] Could not remove container (maybe already removed)."
    log_remote "✅ [REMOTE] Existing container '$CONTAINER_NAME' removed."
else
    log_remote "No existing container named '$CONTAINER_NAME' found."
fi

# 6. Restart the service using docker-compose
log_remote "Starting/Restarting Supagrok service with docker-compose..."
# Use docker-compose with project name to avoid conflicts if other compose files are in parent dirs
# The -p flag sets the project name, which influences network and volume naming.
# Using a consistent project name like 'supagrok' can help manage resources.
if sudo docker-compose -p supagrok up -d --build --force-recreate --remove-orphans; then
    log_remote "✅ [REMOTE] Docker Compose 'up' command successful."
else
    log_remote "❌ [REMOTE] Docker Compose 'up' command failed. See logs above."
    sudo docker-compose -p supagrok logs --tail=50 "$SERVICE_NAME"
    exit 1
fi

# 7. Verify service is running locally
log_remote "Verifying service locally (waiting up to 30 seconds)..."
for i in {{1..6}}; do
    if curl --fail --silent http://localhost:$PORT/health; then
        log_remote "✅ [REMOTE] Service is healthy locally."
        echo "✅ [REMOTE] Supagrok Server Fix completed successfully."
        exit 0
    fi
    log_remote "Waiting for service to become healthy... (attempt $i/6)"
    sleep 5
done

log_remote "❌ [REMOTE] Service did not become healthy locally after 30 seconds."
log_remote "Dumping last 50 lines of container logs:"
sudo docker logs "$CONTAINER_NAME" --tail 50 || log_remote "⚠️ [REMOTE] Could not get logs for $CONTAINER_NAME."
exit 1
"""

def fix_remote_connectivity(server_ip, port, username, remote_app_dir, container_name, service_name_in_compose):
    """PRF-P18: Transfers and executes the fix script on the remote server."""
    log("STEP", f"Attempting to fix connectivity issues on {server_ip}...")
    ssh_target = f"{username}@{server_ip}"

    fix_script_content = create_server_fix_script_content(remote_app_dir, port, container_name, service_name_in_compose)
    
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, prefix="supagrok_fix_", suffix=".sh") as tmp_script:
            tmp_script.write(fix_script_content)
            local_script_path = tmp_script.name
        
        log("INFO", f"Generated fix script: {local_script_path}")

        # Transfer the script
        scp_cmd = ["scp", "-o", f"ConnectTimeout={SSH_CONNECT_TIMEOUT}", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", local_script_path, f"{ssh_target}:{REMOTE_SCRIPT_PATH}"]
        transfer_result = run_local_command(scp_cmd, check=False, capture_output=True)
        if transfer_result is None or transfer_result.returncode != 0:
            log("ERROR", f"Failed to transfer fix script to {ssh_target}:{REMOTE_SCRIPT_PATH}.")
            if transfer_result and transfer_result.stderr: log("ERROR", f"SCP Stderr: {transfer_result.stderr}")
            return False, "SCP failed"
        log("SUCCESS", f"Fix script transferred to {ssh_target}:{REMOTE_SCRIPT_PATH}")

        # Make it executable
        chmod_result = run_remote_command(ssh_target, f"chmod +x {REMOTE_SCRIPT_PATH}", check=False, capture_output=True)
        if chmod_result is None or chmod_result.returncode != 0:
            log("ERROR", f"Failed to make fix script executable on {ssh_target}.")
            if chmod_result and chmod_result.stderr: log("ERROR", f"Chmod Stderr: {chmod_result.stderr}")
            return False, "Chmod failed"
        log("SUCCESS", "Fix script made executable on server.")

        # Execute the script
        # The script itself uses sudo internally for commands that need it.
        exec_command = f"cd {remote_app_dir} && {REMOTE_SCRIPT_PATH}"
        log("INFO", f"Executing remote script: {exec_command}")
        
        # Use Popen for real-time output streaming
        ssh_exec_cmd = ["ssh", "-o", f"ConnectTimeout={SSH_CONNECT_TIMEOUT}", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", ssh_target, exec_command]
        process = subprocess.Popen(ssh_exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        stdout_lines = []
        stderr_lines = []

        log("INFO", "--- Remote Script Output START ---")
        # Read stdout and stderr in a non-blocking way or use select
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip()) # Print remote output directly
                stdout_lines.append(output.strip())
        
        while True:
            error_output = process.stderr.readline()
            if error_output == '' and process.poll() is not None:
                break
            if error_output:
                print(error_output.strip(), file=sys.stderr) # Print remote error directly
                stderr_lines.append(error_output.strip())
        
        return_code = process.wait()
        log("INFO", "--- Remote Script Output END ---")

        # Clean up the remote script
        run_remote_command(ssh_target, f"rm -f {REMOTE_SCRIPT_PATH}", check=False)
        log("INFO", f"Removed temporary script {REMOTE_SCRIPT_PATH} from server.")

        if return_code == 0:
            log("SUCCESS", "Fix script executed successfully on remote server.")
            return True, "\n".join(stdout_lines)
        else:
            log("ERROR", f"Fix script execution failed on remote server with exit code {return_code}.")
            return False, f"Stdout:\n{' '.join(stdout_lines)}\nStderr:\n{' '.join(stderr_lines)}"

    except Exception as e:
        log("ERROR", f"An error occurred during remote fix execution: {e}")
        return False, str(e)
    finally:
        if 'local_script_path' in locals() and os.path.exists(local_script_path):
            os.unlink(local_script_path)
            log("INFO", f"Removed local temporary script: {local_script_path}")

def get_server_ip():
    """Attempt to get the primary public IP of the machine. Fallback for some environments."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1" # Fallback

def main():
    """PRF-P22: Main execution flow."""
    parser = argparse.ArgumentParser(
        description="Supagrok Network Verifier & Fixer. Verifies connectivity and attempts to fix common server-side issues.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("server_ip", nargs='?', default=None, help="The IP address or hostname of the Supagrok server. If not provided, will attempt to use local machine's IP.")
    parser.add_argument("-u", "--username", help="SSH username for the remote server (required for --fix and --setup-ssh).")
    parser.add_argument("-p", "--port", type=int, default=DEFAULT_PORT, help=f"Port number the service is expected on (default: {DEFAULT_PORT}).")
    parser.add_argument("--setup-ssh", action="store_true", help="Attempt to set up SSH key-based authentication for passwordless access.")
    parser.add_argument("--fix", action="store_true", help="Attempt to automatically fix common server-side issues if verification fails.")
    parser.add_argument("--remote-app-dir", default=REMOTE_APP_DIR, help=f"Path to the Supagrok application directory on the server (default: {REMOTE_APP_DIR}).")
    parser.add_argument("--container-name", default=CONTAINER_NAME, help=f"Name of the Docker container (default: {CONTAINER_NAME}).")
    parser.add_argument("--service-name", default=SERVICE_NAME_IN_COMPOSE, help=f"Service name in docker-compose.yml (default: {SERVICE_NAME_IN_COMPOSE}).")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION} (UUID: {SCRIPT_UUID})")

    args = parser.parse_args()

    server_ip = args.server_ip if args.server_ip else get_server_ip()
    log("INFO", f"Supagrok Network Doctor v{VERSION} (UUID: {SCRIPT_UUID})")
    log("INFO", f"Target Server: {server_ip}, Port: {args.port}")

    if (args.fix or args.setup_ssh) and not args.username:
        log("ERROR", "Username (-u/--username) is required when using --fix or --setup-ssh.")
        parser.print_help()
        sys.exit(1)

    if not check_dependencies():
        log("ERROR", "WebSocket client dependency not met. Please install it and try again.")
        sys.exit(1)

    if args.setup_ssh:
        if not setup_ssh_key_auth(server_ip, args.username):
            log("WARN", "SSH key setup failed or was not completed. You might be prompted for passwords frequently.")
        else:
            log("SUCCESS", "SSH key authentication setup completed. Subsequent SSH operations should be passwordless.")

    report = {
        "timestamp": datetime.now().isoformat(),
        "server_ip": server_ip,
        "port": args.port,
        "tests": {},
        "actions_taken": [],
        "recommendations": []
    }

    log("STEP", "Initial Connectivity Check (from local machine)")
    health_ok, health_msg = verify_health_endpoint(server_ip, args.port)
    report["tests"]["initial_health_check"] = {"status": "PASS" if health_ok else "FAIL", "details": health_msg}

    ws_ok, ws_msg = verify_websocket(server_ip, args.port)
    report["tests"]["initial_websocket_check"] = {"status": "PASS" if ws_ok else "FAIL", "details": ws_msg}

    if health_ok and ws_ok:
        log("SUCCESS", "Initial connectivity checks passed. Service appears to be accessible externally.")
    else:
        log("WARN", "Initial connectivity checks failed. Service may not be accessible externally.")
        if args.fix:
            log("INFO", "Attempting to fix server-side issues as --fix flag was provided.")
            fix_successful, fix_output = fix_remote_connectivity(server_ip, args.port, args.username, args.remote_app_dir, args.container_name, args.service_name)
            report["actions_taken"].append({
                "action": "Remote Fix Script Execution",
                "success": fix_successful,
                "output": fix_output
            })

            if fix_successful:
                log("SUCCESS", "Remote fix script completed. Re-verifying connectivity...")
                health_ok, health_msg = verify_health_endpoint(server_ip, args.port)
                report["tests"]["post_fix_health_check"] = {"status": "PASS" if health_ok else "FAIL", "details": health_msg}
                ws_ok, ws_msg = verify_websocket(server_ip, args.port)
                report["tests"]["post_fix_websocket_check"] = {"status": "PASS" if ws_ok else "FAIL", "details": ws_msg}

                if health_ok and ws_ok:
                    log("SUCCESS", "Connectivity established after fixes!")
                else:
                    log("ERROR", "Connectivity issues persist even after attempting fixes.")
                    report["recommendations"].append("Connectivity issues persist. Review server logs and IONOS Cloud Panel firewall settings.")
            else:
                log("ERROR", "Remote fix script failed. Cannot re-verify connectivity.")
                report["recommendations"].append("Remote fix script failed. Review script output and server logs.")
        else:
            log("INFO", "Run with --fix to attempt automatic server-side corrections.")
            report["recommendations"].append("Service not accessible externally. Consider running with --fix or manually checking server-side configuration and IONOS Cloud Panel firewall.")

    # Final Report
    log("REPORT", "Network Verification Report:")
    print(json.dumps(report, indent=2))

    if not (health_ok and ws_ok):
        log("WARN", "One or more connectivity checks failed.")
        log("IMPORTANT", "If the service is confirmed running correctly ON THE SERVER (e.g., `curl http://localhost:8000/health` works on the server), "
                       "the most likely cause for external connection failure is the **IONOS Cloud Panel Firewall**. "
                       "Please log in to your IONOS account and ensure that you have a firewall policy assigned to your server's IP address (67.217.243.191) "
                       "that explicitly ALLOWS incoming TCP traffic on port 8000 (or the port you are using) from 'Any IP' or '0.0.0.0/0'.")
        sys.exit(1)
    else:
        log("SUCCESS", "All connectivity checks passed. The Supagrok service should be accessible.")
        sys.exit(0)

if __name__ == "__main__":
    # Ensure PyYAML is available for the fix script generation part
    ensure_yaml_installed()
    main()
