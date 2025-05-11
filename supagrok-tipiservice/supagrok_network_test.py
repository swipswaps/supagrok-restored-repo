#!/usr/bin/env python3
# PRF-SUPAGROK-V3-NETWORK-TEST-V1.0
# UUID: 9f8e7d6c-5b4a-3c2d-1e0f-9a8b7c6d5e4f
# Path: /home/supagrok/supagrok-tipiservice/supagrok_network_test.py
# Purpose: Comprehensive network test script for Supagrok Snapshot Tipi service,
#          validating connectivity, firewall rules, and service health.
# PRF Relevance: P01, P02, P03, P04, P05, P07, P11, P12, P13, P14, P15, P16, P17, P18, P19, P21, P22, P24, P25, P26, P27, P28, P29, P30

import os
import sys
import subprocess
import socket
import time
import json
import requests
from datetime import datetime
import urllib.request
from urllib.error import URLError, HTTPError
import ssl

# --- Configuration ---
APP_PORT = 8000
TIMEOUT_SECONDS = 5
TEST_EXTERNAL = True  # Set to True to test external connectivity

# --- Logging ---
def log(level, msg):
    """PRF-P07: Centralized logging with clear indicators."""
    icon = {"INFO": "🌀", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅", "STEP": "🛠️", "TEST": "🧪"}
    print(f"{icon.get(level.upper(), 'ℹ️')} [{level.upper()}] {msg}")

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
        context = ssl._create_unverified_context()
        response = urllib.request.urlopen("https://api.ipify.org", timeout=5, context=context)
        if response.status == 200:
            ip = response.read().decode('utf-8')
            log("SUCCESS", f"Detected server IP via external service: {ip}")
            return ip
    except Exception as e:
        log("WARN", f"Could not determine IP via external service: {e}")
    
    log("WARN", "Could not automatically determine server IP. Using localhost for testing.")
    return "localhost"

def check_port_listening(port):
    """PRF-P05, P12, P18: Check if a port is listening on the server."""
    log("TEST", f"Checking if port {port} is listening...")
    
    try:
        # Try using netstat if available
        netstat_cmd = ["netstat", "-tuln"]
        try:
            result = subprocess.run(netstat_cmd, check=True, capture_output=True, text=True)
            if f":{port}" in result.stdout:
                log("SUCCESS", f"Port {port} is listening according to netstat.")
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            log("INFO", "netstat command failed or not available. Trying ss...")
            
            # Try using ss if available
            ss_cmd = ["ss", "-tuln"]
            try:
                result = subprocess.run(ss_cmd, check=True, capture_output=True, text=True)
                if f":{port}" in result.stdout:
                    log("SUCCESS", f"Port {port} is listening according to ss.")
                    return True
            except (subprocess.SubprocessError, FileNotFoundError):
                log("INFO", "ss command failed or not available. Trying socket test...")
    except Exception as e:
        log("WARN", f"Error checking port with system tools: {e}")
    
    # Direct socket test as fallback
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result == 0:
            log("SUCCESS", f"Port {port} is listening according to socket test.")
            return True
        else:
            log("ERROR", f"Port {port} is NOT listening according to socket test.")
            return False
    except Exception as e:
        log("ERROR", f"Error checking port with socket: {e}")
        return False

def check_firewall_rules(port):
    """PRF-P05, P12, P18: Check if firewall allows traffic on the specified port."""
    log("TEST", f"Checking firewall rules for port {port}...")
    
    # Check UFW status if available
    try:
        ufw_cmd = ["sudo", "ufw", "status"]
        result = subprocess.run(ufw_cmd, check=True, capture_output=True, text=True)
        
        if "Status: inactive" in result.stdout:
            log("INFO", "UFW firewall is inactive.")
            return True
        
        log("INFO", "UFW firewall is active. Checking rules...")
        
        # Check if port is allowed
        if f"{port}/tcp" in result.stdout or f"{port}" in result.stdout:
            log("SUCCESS", f"Port {port} is allowed in UFW.")
            return True
        else:
            log("WARN", f"Port {port} does not appear to be explicitly allowed in UFW.")
            
            # Check for general allow rules
            if "allow from any to any" in result.stdout:
                log("INFO", "UFW has a general allow rule that might permit traffic.")
                return True
    except (subprocess.SubprocessError, FileNotFoundError):
        log("INFO", "UFW command failed or not available. Trying iptables...")
    
    # Check iptables if available
    try:
        iptables_cmd = ["sudo", "iptables", "-L", "-n"]
        result = subprocess.run(iptables_cmd, check=True, capture_output=True, text=True)
        
        # This is a very basic check and might not catch all rules
        if f"tcp dpt:{port}" in result.stdout or "ACCEPT" in result.stdout:
            log("INFO", "iptables appears to have rules that might allow traffic.")
            return True
    except (subprocess.SubprocessError, FileNotFoundError):
        log("INFO", "iptables command failed or not available.")
    
    log("WARN", "Could not definitively determine if firewall allows traffic on port {port}.")
    return None  # Unknown status

def check_docker_network_mode():
    """PRF-P05, P12, P18: Check if Docker container is using host network mode."""
    log("TEST", "Checking Docker container network mode...")
    
    try:
        # Get container ID for the supagrok service
        container_cmd = ["sudo", "docker", "ps", "--filter", "name=supagrok", "--format", "{{.ID}}"]
        container_result = subprocess.run(container_cmd, check=True, capture_output=True, text=True)
        container_id = container_result.stdout.strip()
        
        if not container_id:
            log("ERROR", "No supagrok container found running.")
            return False
        
        # Inspect container network settings
        inspect_cmd = ["sudo", "docker", "inspect", "--format", "{{.HostConfig.NetworkMode}}", container_id]
        inspect_result = subprocess.run(inspect_cmd, check=True, capture_output=True, text=True)
        network_mode = inspect_result.stdout.strip()
        
        if network_mode == "host":
            log("SUCCESS", "Docker container is using host network mode.")
            return True
        else:
            log("WARN", f"Docker container is using {network_mode} network mode, not host mode.")
            
            # Check port mappings if not using host mode
            port_cmd = ["sudo", "docker", "port", container_id]
            port_result = subprocess.run(port_cmd, check=True, capture_output=True, text=True)
            port_mappings = port_result.stdout.strip()
            
            if f"{APP_PORT}" in port_mappings:
                log("INFO", f"Container has port mapping for {APP_PORT}: {port_mappings}")
                return True
            else:
                log("ERROR", f"Container does not have port mapping for {APP_PORT}.")
                return False
    except Exception as e:
        log("ERROR", f"Error checking Docker network mode: {e}")
        return False

def test_local_health_endpoint(server_ip):
    """PRF-P05, P12, P18: Test if the health endpoint is accessible locally."""
    log("TEST", f"Testing local health endpoint at http://localhost:{APP_PORT}/health...")
    
    try:
        response = requests.get(f"http://localhost:{APP_PORT}/health", timeout=TIMEOUT_SECONDS)
        if response.status_code == 200:
            log("SUCCESS", f"Local health endpoint is accessible. Response: {response.text}")
            return True
        else:
            log("ERROR", f"Local health endpoint returned status code {response.status_code}.")
            return False
    except requests.exceptions.RequestException as e:
        log("ERROR", f"Error accessing local health endpoint: {e}")
        
        # Try with server IP instead of localhost
        try:
            log("INFO", f"Trying with server IP: http://{server_ip}:{APP_PORT}/health")
            response = requests.get(f"http://{server_ip}:{APP_PORT}/health", timeout=TIMEOUT_SECONDS)
            if response.status_code == 200:
                log("SUCCESS", f"Health endpoint is accessible via server IP. Response: {response.text}")
                return True
            else:
                log("ERROR", f"Health endpoint via server IP returned status code {response.status_code}.")
                return False
        except requests.exceptions.RequestException as e2:
            log("ERROR", f"Error accessing health endpoint via server IP: {e2}")
            return False

def test_external_health_endpoint(server_ip):
    """PRF-P05, P12, P18: Test if the health endpoint is accessible externally."""
    log("TEST", f"Testing external health endpoint at http://{server_ip}:{APP_PORT}/health...")
    log("INFO", "Note: This test may fail if run from the server itself due to firewall rules.")
    
    try:
        # Use urllib instead of requests to avoid potential proxy settings
        context = ssl._create_unverified_context()
        response = urllib.request.urlopen(f"http://{server_ip}:{APP_PORT}/health", timeout=TIMEOUT_SECONDS, context=context)
        
        if response.status == 200:
            data = response.read().decode('utf-8')
            log("SUCCESS", f"External health endpoint is accessible. Response: {data}")
            return True
        else:
            log("ERROR", f"External health endpoint returned status code {response.status}.")
            return False
    except (URLError, HTTPError) as e:
        log("ERROR", f"Error accessing external health endpoint: {e}")
        return False

def check_cloud_provider():
    """PRF-P05, P12, P18: Attempt to identify cloud provider and check for cloud-specific firewall rules."""
    log("TEST", "Checking for cloud provider...")
    
    # Check for common cloud provider metadata services
    cloud_providers = {
        "AWS": "http://169.254.169.254/latest/meta-data/",
        "GCP": "http://metadata.google.internal/computeMetadata/v1/",
        "Azure": "http://169.254.169.254/metadata/instance?api-version=2019-06-01",
        "DigitalOcean": "http://169.254.169.254/metadata/v1/",
        "Linode": "http://169.254.169.254/latest/meta-data/",
        "Vultr": "http://169.254.169.254/latest/meta-data/",
    }
    
    detected_provider = None
    
    for provider, url in cloud_providers.items():
        try:
            headers = {}
            if provider == "GCP":
                headers = {"Metadata-Flavor": "Google"}
            elif provider == "Azure":
                headers = {"Metadata": "true"}
            
            response = requests.get(url, headers=headers, timeout=1)
            if response.status_code == 200:
                detected_provider = provider
                log("INFO", f"Detected cloud provider: {provider}")
                break
        except:
            continue
    
    if not detected_provider:
        log("INFO", "Could not detect cloud provider or not running in cloud environment.")
        return None
    
    # Check for cloud-specific firewall rules
    if detected_provider == "AWS":
        try:
            # Check security groups
            aws_cmd = ["aws", "ec2", "describe-security-groups", "--query", "SecurityGroups[*].IpPermissions[*]"]
            result = subprocess.run(aws_cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0 and f"FromPort\": {APP_PORT}" in result.stdout:
                log("INFO", f"AWS security group appears to allow traffic on port {APP_PORT}.")
                return True
            else:
                log("WARN", f"AWS security group might not allow traffic on port {APP_PORT}.")
                return False
        except:
            log("INFO", "AWS CLI not available or not configured.")
    
    return None  # Unknown status

def run_comprehensive_test():
    """PRF-P05, P12, P18: Run a comprehensive network test."""
    log("STEP", "Starting comprehensive network test...")
    
    # Get server IP
    server_ip = get_server_ip()
    
    # Check if port is listening
    port_listening = check_port_listening(APP_PORT)
    
    # Check firewall rules
    firewall_status = check_firewall_rules(APP_PORT)
    
    # Check Docker network mode
    docker_network_mode = check_docker_network_mode()
    
    # Test local health endpoint
    local_health = test_local_health_endpoint(server_ip)
    
    # Test external health endpoint if requested
    external_health = None
    if TEST_EXTERNAL:
        external_health = test_external_health_endpoint(server_ip)
    
    # Check cloud provider
    cloud_provider = check_cloud_provider()
    
    # Print summary
    log("STEP", "Network Test Summary:")
    print("\n" + "=" * 50)
    print(f"Server IP: {server_ip}")
    print(f"Port {APP_PORT} Listening: {'✅ Yes' if port_listening else '❌ No'}")
    print(f"Firewall Status: {'✅ Allowing' if firewall_status else '❓ Unknown' if firewall_status is None else '❌ Blocking'}")
    print(f"Docker Network Mode: {'✅ Properly Configured' if docker_network_mode else '❌ Misconfigured'}")
    print(f"Local Health Endpoint: {'✅ Accessible' if local_health else '❌ Inaccessible'}")
    if TEST_EXTERNAL:
        print(f"External Health Endpoint: {'✅ Accessible' if external_health else '❌ Inaccessible'}")
    print(f"Cloud Provider: {cloud_provider if cloud_provider else 'Not detected or not in cloud'}")
    print("=" * 50)
    
    # Provide recommendations
    if not port_listening:
        print("\n❌ Issue: Port not listening")
        print("Recommendations:")
        print("1. Check if the Docker container is running: sudo docker ps")
        print("2. Check container logs: sudo docker logs supagrok_snapshot_service_container")
        print("3. Restart the container: sudo docker-compose down && sudo docker-compose up -d")
    
    if firewall_status is False:
        print("\n❌ Issue: Firewall might be blocking traffic")
        print("Recommendations:")
        print("1. Allow traffic on port 8000: sudo ufw allow 8000/tcp")
        print("2. Reload firewall rules: sudo ufw reload")
    
    if not docker_network_mode:
        print("\n❌ Issue: Docker network mode misconfigured")
        print("Recommendations:")
        print("1. Update docker-compose.yml to use host network mode")
        print("2. Restart the container: sudo docker-compose down && sudo docker-compose up -d")
    
    if not local_health:
        print("\n❌ Issue: Local health endpoint inaccessible")
        print("Recommendations:")
        print("1. Check if the application is running inside the container")
        print("2. Check container logs: sudo docker logs supagrok_snapshot_service_container")
    
    if TEST_EXTERNAL and not external_health:
        print("\n❌ Issue: External health endpoint inaccessible")
        print("Recommendations:")
        print("1. Check if the server has a public IP address")
        print("2. Check if the firewall allows external traffic")
        print("3. If using a cloud provider, check security groups/firewall rules")
        print("4. Try accessing from another machine: curl http://{server_ip}:{APP_PORT}/health")
    
    # Return overall status
    return port_listening and local_health and (not TEST_EXTERNAL or external_health)

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
