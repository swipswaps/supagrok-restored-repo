--- a/home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca/app/supagrok_restored_repo/supagrok-tipiservice/supagrok_network_verifier.py
+++ b/home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca/app/supagrok_restored_repo/supagrok-tipiservice/supagrok_network_verifier.py
@@ -6,14 +6,14 @@
 
 import sys
 import time
-import urllib request
+import urllib.request
 import socket
 import json
 import argparse
 import subprocess
 import os
-import websocket # changed to see if you can see this
 import tempfile
+import signal # Added for signal handling
 from datetime import datetime
 from pathlib import Path
 import threading # For WebSocket timeout
@@ -32,7 +32,7 @@
 SCRIPT_UUID = "5e4d3c2b-1a9f-8b7e-6d5c-4f3e2d1c0b9a-fixed-v1"
 
 # --- Logging ---
-def log(level, msg):
+def log(level: str, msg: str):
     """PRF-P07, P13: Centralized logging with clear indicators."""
     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
     icon = {"INFO": "🌀", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅", "STEP": "🛠️", "DEBUG": "🔍", "REPORT": "📊"}
@@ -40,14 +40,14 @@
 
 def ensure_websocket_client_installed():
     """PRF-P04: Ensure websocket-client is installed."""
+    global websocket # Declare websocket as global before assigning
     try:
         import websocket
-        globals()["websocket"] = websocket # Make it globally available
         return True
     except ImportError:
         log("INFO", "WebSocket client not found. Attempting to install websocket-client...")
         try:
-            subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"])
+            subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
             import websocket
             globals()["websocket"] = websocket # Make it globally available
             log("SUCCESS", "Successfully installed websocket-client.")
@@ -262,7 +262,7 @@
     fix_script_content = """#!/bin/bash
 # PRF-SUPAGROK-V3-QUICK-FIX-V1.2
 # Purpose: Quick fix for network connectivity issues, focusing on firewall and service state.
-set -e
+set -euo pipefail
 
 TARGET_PORT="{port}"
 SERVICE_NAME="{SERVICE_NAME_IN_COMPOSE}"
@@ -451,7 +451,7 @@
 def main():
     """PRF-P22: Main execution flow."""
     parser = argparse.ArgumentParser(
-        description=f"Supagrok Network Verifier v{VERSION}. Verifies and optionally fixes network connectivity to a Supagrok service.",
+        description=f"Supagrok Network Verifier v{VERSION} (UUID: {SCRIPT_UUID}). Verifies and optionally fixes network connectivity to a Supagrok service.",
         formatter_class=argparse.RawTextHelpFormatter
     )
     parser.add_argument("server_ip", help="IP address of the Supagrok server")
@@ -520,8 +510,9 @@
         log("ERROR", "Service is not accessible. Run with --fix to attempt automatic correction.")
         sys.exit(1)
     else:
+        log("SUCCESS", f"Service is accessible and healthy at http://{args.server_ip}:{args.port}/health and ws://{args.server_ip}:{args.port}/ws/snapshot")
         log("SUCCESS", "Supagrok Network Verifier finished.")
         sys.exit(0)
 
 if __name__ == "__main__":
-    # Handle SIGINT for graceful shutdown (though less critical for a verifier)
+    # PRF-P17: Handle SIGINT for graceful shutdown
     signal.signal(signal.SIGINT, lambda sig, frame: (log("INFO", "Verifier interrupted."), sys.exit(1)))
     main()

