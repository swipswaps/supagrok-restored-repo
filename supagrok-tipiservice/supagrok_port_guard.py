#!/usr/bin/env python3
# PRF-SUPAGROK-PORT-GUARD-V1.3
# UUID: 7e9a2d5f-8b3c-4e1d-9c7a-f5d8e6b7a9c0
# Path: /home/owner/supagrok-tipiservice/supagrok_port_guard.py
# Purpose: Detect and resolve port conflicts for the Supagrok Tipi Service
# PRF Relevance: PRF5, PRF7, PRF12, PRF15, PRF21, PRF28

import os
import subprocess
import sys
import time
import socket
import signal
import re
from datetime import datetime

# Configuration
PORT = 8000
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds (reduced from 5)

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

def is_port_in_use(port):
    """PRF12: Check if the specified port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(('localhost', port)) == 0
        if result:
            log("WARN", f"Port {port} is in use")
        else:
            log("INFO", f"Port {port} is not in use")
        return result

def find_process_using_port(port):
    """PRF21: Find process using the port, handling missing tools gracefully."""
    log("STEP", f"Finding process using port {port}...")
    
    # Try lsof first
    if os.system("which lsof > /dev/null 2>&1") == 0:
        try:
            log("INFO", f"Using lsof to find process on port {port}")
            output = subprocess.check_output(["lsof", "-i", f":{port}"], text=True)
            log("DEBUG", f"lsof output: {output}")
            lines = output.strip().split('\n')
            if len(lines) > 1:  # Header + at least one process
                process_info = lines[1].split()
                if len(process_info) > 1:
                    pid = int(process_info[1])  # PID is in the second column
                    log("SUCCESS", f"Found process {pid} using port {port}")
                    return pid
        except subprocess.CalledProcessError:
            log("INFO", "No process found using lsof")
    
    # Try ss as an alternative
    if os.system("which ss > /dev/null 2>&1") == 0:
        try:
            log("INFO", f"Using ss to find process on port {port}")
            output = subprocess.check_output(["ss", "-tulpn", f"sport = :{port}"], text=True)
            log("DEBUG", f"ss output: {output}")
            for line in output.strip().split('\n'):
                if f":{port}" in line and "pid=" in line:
                    pid_match = re.search(r'pid=(\d+)', line)
                    if pid_match:
                        pid = int(pid_match.group(1))
                        log("SUCCESS", f"Found process {pid} using port {port}")
                        return pid
        except subprocess.CalledProcessError:
            log("INFO", "No process found using ss")
    
    # Try netstat as a last resort
    if os.system("which netstat > /dev/null 2>&1") == 0:
        try:
            log("INFO", f"Using netstat to find process on port {port}")
            output = subprocess.check_output(["netstat", "-tulpn"], text=True)
            log("DEBUG", f"netstat output: {output}")
            for line in output.strip().split('\n'):
                if f":{port}" in line and "LISTEN" in line:
                    pid_match = re.search(r'(\d+)/', line)
                    if pid_match:
                        pid = int(pid_match.group(1))
                        log("SUCCESS", f"Found process {pid} using port {port}")
                        return pid
        except subprocess.CalledProcessError:
            log("INFO", "No process found using netstat")
    
    log("WARN", f"Could not find any process using port {port}")
    return None

def kill_process(pid):
    """PRF15: Attempt to kill a process with increasing force if needed."""
    log("WARN", f"Attempting to terminate process {pid} using port {PORT}...")
    
    # Try SIGTERM first (graceful)
    try:
        log("INFO", f"Sending SIGTERM to process {pid}")
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)  # Give it time to terminate (reduced from 2)
        if not is_port_in_use(PORT):
            log("SUCCESS", f"Process {pid} terminated gracefully.")
            return True
    except OSError as e:
        log("ERROR", f"Failed to send SIGTERM to process {pid}: {e}")
    
    # Try SIGKILL if SIGTERM didn't work
    try:
        log("WARN", f"Process {pid} did not terminate gracefully. Attempting force kill...")
        os.kill(pid, signal.SIGKILL)
        time.sleep(1)
        if not is_port_in_use(PORT):
            log("SUCCESS", f"Process {pid} force killed.")
            return True
    except OSError as e:
        log("ERROR", f"Failed to kill process {pid}: {e}")
        return False
    
    return False

def free_port():
    """PRF15: Free the port with retry logic."""
    log("STEP", f"Checking if port {PORT} is in use...")
    
    if not is_port_in_use(PORT):
        log("SUCCESS", f"Port {PORT} is available.")
        return True
    
    for attempt in range(1, MAX_RETRIES + 1):
        log("WARN", f"Port {PORT} is in use. Attempt {attempt}/{MAX_RETRIES} to free it...")
        
        pid = find_process_using_port(PORT)
        if pid:
            log("INFO", f"Found process {pid} using port {PORT}.")
            if kill_process(pid):
                if not is_port_in_use(PORT):
                    log("SUCCESS", f"Port {PORT} is now available.")
                    return True
        else:
            log("WARN", f"Could not identify the process using port {PORT}.")
            
            # Try using sudo with lsof as a last resort
            try:
                log("INFO", "Trying sudo lsof as a last resort")
                output = subprocess.check_output(["sudo", "lsof", "-i", f":{PORT}"], text=True)
                log("DEBUG", f"sudo lsof output: {output}")
                lines = output.strip().split('\n')
                if len(lines) > 1:  # Header + at least one process
                    process_info = lines[1].split()
                    if len(process_info) > 1:
                        pid = int(process_info[1])  # PID is in the second column
                        log("SUCCESS", f"Found process {pid} using port {PORT} with sudo")
                        # Kill with sudo
                        subprocess.check_call(["sudo", "kill", "-9", str(pid)])
                        time.sleep(1)
                        if not is_port_in_use(PORT):
                            log("SUCCESS", f"Port {PORT} is now available after sudo kill.")
                            return True
            except (subprocess.CalledProcessError, ValueError, OSError) as e:
                log("ERROR", f"Failed to use sudo to find/kill process: {e}")
        
        if attempt < MAX_RETRIES:
            log("INFO", f"Waiting {RETRY_DELAY} seconds before next attempt...")
            time.sleep(RETRY_DELAY)
    
    log("ERROR", f"Failed to free port {PORT} after {MAX_RETRIES} attempts.")
    return False

if __name__ == "__main__":
    log("INFO", f"Port Guard: Ensuring port {PORT} is available...")
    success = free_port()
    sys.exit(0 if success else 1)
