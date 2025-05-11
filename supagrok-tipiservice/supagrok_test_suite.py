#!/usr/bin/env python3
# 📂 supagrok-tipiservice/supagrok_test_suite.py
# Comprehensive test suite for Supagrok Snapshot Service
# PRF-SUPAGROK-TEST-SCRIPT-2025-05-06

import os
import sys
import time
import json
import socket
import subprocess
import requests
import yaml
import websocket
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
SERVICE_PORT = 8000
SERVICE_HOST = "localhost"
BASE_URL = f"http://{SERVICE_HOST}:{SERVICE_PORT}"
HEALTH_ENDPOINT = f"{BASE_URL}/health"
SNAPSHOT_ENDPOINT = f"{BASE_URL}/snapshot"
WEBSOCKET_URL = f"ws://{SERVICE_HOST}:{SERVICE_PORT}/ws/snapshot"

COMPOSE_FILE_PATH = Path("docker-compose.yml")
MASTER_LAUNCHER_PATH = Path("supagrok_master_launcher.py")
TEST_DATA_DIR = Path("./test_data")
TEST_SOURCE_DIR = TEST_DATA_DIR / "source"
TEST_OUTPUT_DIR = TEST_DATA_DIR / "output"
TEST_FILE_PATH = TEST_SOURCE_DIR / f"test_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

# Service name in docker-compose.yml
SERVICE_NAME = "supagrok-snapshot-service"  # Service name in docker-compose.yml
CONTAINER_NAME = "supagrok_snapshot_service_container"  # Container name

# Test configuration
MAX_STARTUP_WAIT_TIME = 15  # seconds (reduced from 30)
HEALTH_CHECK_INTERVAL = 1   # seconds
TEST_TIMEOUT = 5            # seconds (reduced from 10)
SNAPSHOT_WAIT_TIME = 3      # seconds to wait for snapshot processing
VERBOSE = True

# --- Utility Functions ---
def log(level, message):
    """PRF-P10: Log a message with timestamp and level."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level_colors = {
        "STEP": "\033[1;36m",  # Bold Cyan
        "INFO": "\033[0;37m",  # Light Gray
        "SUCCESS": "\033[0;32m",  # Green
        "WARN": "\033[0;33m",  # Yellow
        "ERROR": "\033[0;31m",  # Red
    }
    
    color = level_colors.get(level, "\033[0m")
    reset = "\033[0m"
    
    print(f"{timestamp} [{color}{level}{reset}] {message}")

def run_command(command, check=True, capture_output=True):
    """PRF-P11: Run a shell command and return the result."""
    if VERBOSE:
        log("INFO", f"Running command: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        log("ERROR", f"Command failed with exit code {e.returncode}: {' '.join(command)}")
        if e.stdout:
            log("INFO", f"Command stdout: {e.stdout}")
        if e.stderr:
            log("ERROR", f"Command stderr: {e.stderr}")
        if check:
            raise
        return e
    except Exception as e:
        log("ERROR", f"Failed to run command: {e}")
        if check:
            raise
        return None

def is_port_in_use(port):
    """PRF-P13: Check if a port is in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            is_in_use = result == 0
            log("INFO", f"Port {port} is{' ' if is_in_use else ' not '}in use")
            return is_in_use
    except Exception as e:
        log("ERROR", f"Error checking if port {port} is in use: {e}")
        return False

def port_guard(port):
    """PRF-P13: Ensure a port is free for use."""
    if not is_port_in_use(port):
        return True
    
    log("WARN", f"Port {port} is already in use. Attempting to stop existing service...")
    
    # Try to stop with docker compose (both V1 and V2 variants) with and without sudo
    try:
        run_command(["docker", "compose", "down", "--remove-orphans"], check=False)
        run_command(["docker-compose", "down", "--remove-orphans"], check=False)
        run_command(["sudo", "docker", "compose", "down", "--remove-orphans"], check=False)
        run_command(["sudo", "docker-compose", "down", "--remove-orphans"], check=False)
        time.sleep(1)
    except Exception:
        pass
    
    # Check if port is still in use
    if is_port_in_use(port):
        log("ERROR", f"Failed to free port {port}")
        return False
    
    log("SUCCESS", f"Port {port} is now available")
    return True

def wait_for_service(url, timeout=MAX_STARTUP_WAIT_TIME, interval=HEALTH_CHECK_INTERVAL):
    """PRF-P13: Wait for a service to become available with timeout."""
    log("STEP", f"Waiting for service at {url} (timeout: {timeout}s)...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            log("INFO", f"Attempting to connect to {url}...")
            response = requests.get(url, timeout=2)
            log("INFO", f"Got response: {response.status_code}")
            if response.status_code == 200:
                elapsed = time.time() - start_time
                log("SUCCESS", f"Service is up after {elapsed:.2f} seconds")
                return True
        except requests.RequestException as e:
            log("INFO", f"Connection failed: {e}")
        
        time.sleep(interval)
    
    log("ERROR", f"Service did not become available within {timeout} seconds")
    return False

# --- Test Components ---
def test_dependencies():
    """PRF-P04, P12: Test that all required dependencies are installed."""
    log("STEP", "Testing dependencies...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        log("ERROR", f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        return False
    log("SUCCESS", f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check Docker
    try:
        docker_result = run_command(["docker", "--version"])
        log("SUCCESS", f"Docker installed: {docker_result.stdout.strip()}")
    except (subprocess.SubprocessError, FileNotFoundError):
        log("ERROR", "Docker not found or not working properly")
        return False
    
    # Check Docker Compose
    try:
        # Try docker compose (v2)
        compose_result = run_command(["docker", "compose", "version"], check=False)
        if compose_result.returncode == 0:
            log("SUCCESS", f"Docker Compose V2 installed: {compose_result.stdout.strip()}")
        else:
            # Try docker-compose (v1)
            compose_result = run_command(["docker-compose", "--version"], check=False)
            if compose_result.returncode == 0:
                log("SUCCESS", f"Docker Compose V1 installed: {compose_result.stdout.strip()}")
            else:
                log("ERROR", "Docker Compose not found or not working properly")
                return False
    except FileNotFoundError:
        log("ERROR", "Docker Compose not found")
        return False
    
    # Check required Python packages
    required_packages = ["requests", "websocket-client", "pyyaml"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        log("WARN", f"Missing Python packages: {', '.join(missing_packages)}")
        log("INFO", "Attempting to install missing packages...")
        
        for package in missing_packages:
            try:
                run_command([sys.executable, "-m", "pip", "install", package])
                log("SUCCESS", f"Installed {package}")
            except subprocess.SubprocessError:
                log("ERROR", f"Failed to install {package}")
                return False
    else:
        log("SUCCESS", "All required Python packages are installed")
    
    return True

def setup_test_environment():
    """PRF-P05, P06: Set up the test environment."""
    log("STEP", "Setting up test environment...")
    
    # Create test directories
    TEST_DATA_DIR.mkdir(exist_ok=True)
    TEST_SOURCE_DIR.mkdir(exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Create a test file
    test_content = f"Test file created at {datetime.now().isoformat()}\nThis is a test file for Supagrok Snapshot Service."
    TEST_FILE_PATH.write_text(test_content)
    
    log("SUCCESS", f"Created test file at {TEST_FILE_PATH}")
    
    # Check if docker-compose.yml exists
    if not COMPOSE_FILE_PATH.exists():
        log("ERROR", f"Docker Compose file not found at {COMPOSE_FILE_PATH}")
        return False
    
    # Check if master launcher exists
    if not MASTER_LAUNCHER_PATH.exists():
        log("ERROR", f"Master launcher script not found at {MASTER_LAUNCHER_PATH}")
        return False
    
    return True

def test_service_startup():
    """PRF-P03, P13: Test that the service can start up properly."""
    log("STEP", "Testing service startup...")
    
    # Check if port is in use
    if is_port_in_use(SERVICE_PORT):
        log("INFO", f"Port {SERVICE_PORT} is already in use. Checking if it's our service...")
        
        # Check if the container is already running
        container_check = run_command(["sudo", "docker", "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"], check=False)
        
        if container_check and container_check.stdout and CONTAINER_NAME in container_check.stdout:
            log("INFO", "Service is already running. Testing health endpoint...")
            if wait_for_service(HEALTH_ENDPOINT):
                log("SUCCESS", "Service is already running and health endpoint is responding")
                return True
            else:
                log("WARN", "Service is running but health endpoint is not responding. Restarting...")
        else:
            log("WARN", f"Port {SERVICE_PORT} is in use but container '{CONTAINER_NAME}' not found. Attempting to free port...")
            # Run port guard to free the port
            port_guard_result = run_command(["sudo", "python3", "supagrok_port_guard.py"], check=False)
            if port_guard_result and port_guard_result.returncode != 0:
                log("ERROR", "Port guard failed to free the port")
                if port_guard_result.stderr:
                    log("ERROR", f"Port guard stderr: {port_guard_result.stderr}")
                return False
    else:
        log("INFO", f"Port {SERVICE_PORT} is not in use. Proceeding with service startup.")
    
    # Start the service using docker-compose
    log("INFO", "Starting service using docker-compose...")
    compose_result = run_command(["sudo", "docker-compose", "up", "-d", "--build"], check=False)
    
    if compose_result is None or compose_result.returncode != 0:
        log("ERROR", "Docker Compose failed to start the service")
        if compose_result and compose_result.stderr:
            log("ERROR", f"Docker Compose stderr: {compose_result.stderr}")
        return False
    
    # Give the service a moment to start
    time.sleep(5)
    
    # Check if the container is running
    container_check = run_command(["sudo", "docker", "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"], check=False)
    
    if not container_check or not container_check.stdout or CONTAINER_NAME not in container_check.stdout:
        log("ERROR", f"Service container '{CONTAINER_NAME}' is not running after docker-compose execution")
        # Get container logs
        log("INFO", "Checking container logs...")
        run_command(["sudo", "docker-compose", "logs"], check=False, capture_output=False)
        # Also check container status
        log("INFO", "Checking container status...")
        run_command(["sudo", "docker", "ps", "-a"], check=False, capture_output=False)
        return False
    
    # Wait for the service to become available via HTTP
    if not wait_for_service(HEALTH_ENDPOINT):
        log("ERROR", "Service started but health endpoint is not responding")
        # Get container logs
        log("INFO", "Checking container logs...")
        run_command(["sudo", "docker-compose", "logs"], check=False, capture_output=False)
        return False
    
    log("SUCCESS", "Service started successfully and health endpoint is responding")
    return True

def test_health_endpoint():
    """PRF-P14: Test the health endpoint."""
    log("STEP", "Testing health endpoint...")
    
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=TEST_TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            log("SUCCESS", f"Health endpoint returned: {result}")
            
            # Check for required fields
            if "status" not in result or "timestamp" not in result:
                log("ERROR", "Health endpoint response missing required fields")
                return False
            
            if result["status"] != "healthy":
                log("ERROR", f"Health endpoint reported non-healthy status: {result['status']}")
                return False
            
            return True
        else:
            log("ERROR", f"Health endpoint returned status code {response.status_code}")
            log("ERROR", f"Response: {response.text}")
            return False
    except requests.RequestException as e:
        log("ERROR", f"Failed to connect to health endpoint: {e}")
        return False

def test_snapshot_endpoint():
    """PRF-P14: Test the snapshot endpoint."""
    log("STEP", "Testing snapshot endpoint...")
    
    # Prepare test data
    test_data = {
        "source_path": str(TEST_FILE_PATH),
        "output_path": str(TEST_OUTPUT_DIR / "snapshot_output.txt"),
        "snapshot_type": "text",
        "metadata": {
            "test_id": "automated_test",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    try:
        response = requests.post(
            SNAPSHOT_ENDPOINT,
            json=test_data,
            timeout=TEST_TIMEOUT
        )
        
        # Accept both 200 OK and 202 Accepted as valid responses
        if response.status_code in [200, 202]:
            result = response.json()
            log("SUCCESS", f"Snapshot endpoint returned: {result}")
            
            # Wait for snapshot processing to complete
            log("INFO", f"Waiting {SNAPSHOT_WAIT_TIME} seconds for snapshot processing...")
            time.sleep(SNAPSHOT_WAIT_TIME)
            
            # Verify the output file exists
            output_path = Path(test_data["output_path"])
            if output_path.exists():
                log("SUCCESS", f"Output file created at {output_path}")
                log("INFO", f"Output content: {output_path.read_text()[:100]}...")
                return True
            else:
                log("ERROR", f"Output file was not created at {output_path}")
                return False
        else:
            log("ERROR", f"Snapshot endpoint returned status code {response.status_code}")
            log("ERROR", f"Response: {response.text}")
            return False
    except requests.RequestException as e:
        log("ERROR", f"Failed to connect to snapshot endpoint: {e}")
        return False

def test_websocket_connection():
    """PRF-P14: Test the WebSocket connection."""
    log("STEP", "Testing WebSocket connection...")
    
    message_received = False
    
    def on_message(ws, message):
        nonlocal message_received
        log("SUCCESS", f"Received WebSocket message: {message}")
        message_received = True
        ws.close()
    
    def on_error(ws, error):
        log("ERROR", f"WebSocket error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        log("INFO", f"WebSocket connection closed: {close_status_code} - {close_msg}")
    
    def on_open(ws):
        log("SUCCESS", "WebSocket connection established")
        test_message = json.dumps({
            "action": "ping",
            "data": {
                "timestamp": datetime.now().isoformat()
            }
        })
        log("INFO", f"Sending test message: {test_message}")
        ws.send(test_message)
    
    # Connect to WebSocket
    try:
        ws = websocket.WebSocketApp(
            WEBSOCKET_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Run the WebSocket connection in a separate thread with a timeout
        with ThreadPoolExecutor() as executor:
            future = executor.submit(ws.run_forever)
            try:
                future.result(timeout=TEST_TIMEOUT)
            except TimeoutError:
                log("WARN", "WebSocket test timed out")
                ws.close()
        
        return message_received
    except Exception as e:
        log("ERROR", f"Failed to test WebSocket connection: {e}")
        return False

def test_docker_compose_file():
    """PRF-P12: Test the docker-compose.yml file for correctness."""
    log("STEP", "Testing docker-compose.yml file...")
    
    try:
        # Check if file exists
        if not COMPOSE_FILE_PATH.exists():
            log("ERROR", f"Docker Compose file not found at {COMPOSE_FILE_PATH}")
            return False
        
        # Parse YAML
        with open(COMPOSE_FILE_PATH, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        # Check for required service
        if 'services' not in compose_data:
            log("ERROR", "No services defined in docker-compose.yml")
            return False
        
        if SERVICE_NAME not in compose_data['services']:
            log("ERROR", f"Service '{SERVICE_NAME}' not found in docker-compose.yml")
            return False
        
        service = compose_data['services'][SERVICE_NAME]
        
        # Check for required properties
        required_props = ['image', 'ports', 'volumes', 'environment']
        missing_props = [prop for prop in required_props if prop not in service]
        
        if missing_props:
            log("ERROR", f"Missing required properties in service: {', '.join(missing_props)}")
            return False
        
        # Check port mapping
        ports = service['ports']
        port_mapping = None
        for port in ports:
            if isinstance(port, str) and str(SERVICE_PORT) in port:
                port_mapping = port
                break
        
        if not port_mapping:
            log("ERROR", f"Port {SERVICE_PORT} not mapped in docker-compose.yml")
            return False
        
        # Check environment variables
        env = service['environment']
        required_env = ['GPG_KEY_ID', 'GPG_PASSPHRASE']
        
        if isinstance(env, list):
            env_dict = {}
            for item in env:
                if '=' in item:
                    key, value = item.split('=', 1)
                    env_dict[key] = value
            env = env_dict
        
        missing_env = [var for var in required_env if var not in env]
        
        if missing_env:
            log("ERROR", f"Missing required environment variables: {', '.join(missing_env)}")
            return False
        
        log("SUCCESS", "docker-compose.yml file is valid")
        return True
    except Exception as e:
        log("ERROR", f"Failed to test docker-compose.yml: {e}")
        return False

def test_orphan_container_cleanup():
    """PRF-P15: Test that orphan containers are properly cleaned up."""
    log("STEP", "Testing orphan container cleanup...")
    
    # Stop any running containers first
    log("INFO", "Stopping any running containers...")
    run_command(["docker", "compose", "down"], check=False)
    time.sleep(2)  # Give it time to stop
    
    # Start the service
    log("INFO", "Starting service...")
    run_command(["docker", "compose", "up", "-d"], check=False)
    time.sleep(5)  # Give it time to start
    
    # Check if service is running
    if not wait_for_service(HEALTH_ENDPOINT, timeout=10):
        log("ERROR", "Service failed to start for orphan container test")
        return False
    
    # Get list of running containers
    log("INFO", "Getting list of running containers...")
    containers_before = run_command(["docker", "ps", "--format", "{{.Names}}"], check=False)
    if not containers_before or not containers_before.stdout:
        log("ERROR", "Failed to get list of running containers")
        return False
    
    # Stop the service with --remove-orphans flag
    log("INFO", "Stopping service with --remove-orphans flag...")
    run_command(["docker", "compose", "down", "--remove-orphans"], check=False)
    time.sleep(2)  # Give it time to stop
    
    # Get list of running containers after cleanup
    log("INFO", "Getting list of running containers after cleanup...")
    containers_after = run_command(["docker", "ps", "--format", "{{.Names}}"], check=False)
    if not containers_after:
        log("ERROR", "Failed to get list of running containers after cleanup")
        return False
    
    # Check if all containers were removed
    if containers_after.stdout.strip():
        log("ERROR", "Not all containers were removed. Orphaned containers may still exist.")
        log("ERROR", f"Remaining containers: {containers_after.stdout}")
        
        # Force remove any remaining containers
        for container in containers_after.stdout.strip().split('\n'):
            if container:
                run_command(["docker", "rm", "-f", container], check=False)
        
        return False
    
    log("SUCCESS", "All containers were properly removed")
    return True

def run_tests():
    """PRF-P22: Run all tests and generate a report."""
    log("STEP", "Starting Supagrok Snapshot Service test suite...")
    
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Run tests
    test_results["tests"]["dependencies"] = {
        "status": "PASS" if test_dependencies() else "FAIL",
        "timestamp": datetime.now().isoformat()
    }
    
    test_results["tests"]["setup"] = {
        "status": "PASS" if setup_test_environment() else "FAIL",
        "timestamp": datetime.now().isoformat()
    }
    
    test_results["tests"]["docker_compose"] = {
        "status": "PASS" if test_docker_compose_file() else "FAIL",
        "timestamp": datetime.now().isoformat()
    }
    
    test_results["tests"]["service_startup"] = {
        "status": "PASS" if test_service_startup() else "FAIL",
        "timestamp": datetime.now().isoformat()
    }
    
    test_results["tests"]["health_endpoint"] = {
        "status": "PASS" if test_health_endpoint() else "FAIL",
        "timestamp": datetime.now().isoformat()
    }
    
    test_results["tests"]["snapshot_endpoint"] = {
        "status": "PASS" if test_snapshot_endpoint() else "FAIL",
        "timestamp": datetime.now().isoformat()
    }
    
    test_results["tests"]["websocket"] = {
        "status": "PASS" if test_websocket_connection() else "FAIL",
        "timestamp": datetime.now().isoformat()
    }
    
    test_results["tests"]["orphan_cleanup"] = {
        "status": "PASS" if test_orphan_container_cleanup() else "FAIL",
        "timestamp": datetime.now().isoformat()
    }
    
    # Calculate overall status
    passed_tests = sum(1 for test in test_results["tests"].values() if test["status"] == "PASS")
    total_tests = len(test_results["tests"])
    test_results["overall_status"] = "PASS" if passed_tests == total_tests else "FAIL"
    test_results["passed_tests"] = passed_tests
    test_results["total_tests"] = total_tests
    
    # Generate report
    log("STEP", "Generating test report...")
    report_filename = f"supagrok_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    log("SUCCESS", f"Test report generated at {report_filename}")
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"TEST SUMMARY: {passed_tests}/{total_tests} tests passed")
    print("=" * 50)
    for test_name, test_result in test_results["tests"].items():
        print(f"{test_result['status']} - {test_name}")
    print("=" * 50)
    print(f"OVERALL STATUS: {test_results['overall_status']}")
    print()
    
    # Print recommendations if any tests failed
    if test_results["overall_status"] == "FAIL":
        print("Recommendations:")
        if test_results["tests"]["snapshot_endpoint"]["status"] == "FAIL":
            print("- Check the snapshot endpoint implementation and error handling.")
        if test_results["tests"]["orphan_cleanup"]["status"] == "FAIL":
            print("- Ensure the --remove-orphans flag is used in docker-compose commands.")
        if test_results["tests"]["service_startup"]["status"] == "FAIL":
            print("- Check the Docker Compose configuration and container logs.")
        print("=" * 50)
        print()
    
    return passed_tests == total_tests

def cleanup_test_environment():
    """PRF-P05: Clean up the test environment."""
    log("STEP", "Cleaning up test environment...")
    
    # Stop any running containers
    run_command(["docker", "compose", "down", "--remove-orphans"], check=False)
    run_command(["docker-compose", "down", "--remove-orphans"], check=False)
    run_command(["sudo", "docker", "compose", "down", "--remove-orphans"], check=False)
    run_command(["sudo", "docker-compose", "down", "--remove-orphans"], check=False)
    
    # Remove test files
    if TEST_FILE_PATH.exists():
        TEST_FILE_PATH.unlink()
    
    # Remove test directories
    if TEST_SOURCE_DIR.exists():
        for file in TEST_SOURCE_DIR.glob("*"):
            file.unlink()
        TEST_SOURCE_DIR.rmdir()
    
    if TEST_OUTPUT_DIR.exists():
        for file in TEST_OUTPUT_DIR.glob("*"):
            file.unlink()
        TEST_OUTPUT_DIR.rmdir()
    
    if TEST_DATA_DIR.exists():
        TEST_DATA_DIR.rmdir()
    
    log("SUCCESS", "Test environment cleaned up")

if __name__ == "__main__":
    try:
        success = run_tests()
        
        # Ask if user wants to clean up
        cleanup = input("\nClean up test environment? (y/n): ").lower()
        if cleanup == 'y':
            cleanup_test_environment()
        
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log("INFO", "Test suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        log("ERROR", f"Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
