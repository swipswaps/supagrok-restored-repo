#!/usr/bin/env python3
# run_eye_tracker.py — PRF‑WEBCAM‑RUN‑2025‑05‑02
# Description: Run the smooth eye tracker
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import subprocess
import time
import signal
from datetime import datetime
from pathlib import Path

# === [P01] Metadata ===
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
UUID = os.popen("uuidgen").read().strip()
LOGFILE = Path(f"/tmp/eye_tracker_run_{TS}.log")

# === [P02] Logging ===
def log(msg):
    """Log message to file and console"""
    timestamp = datetime.now().isoformat()
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    
    with open(LOGFILE, "a") as f:
        f.write(log_msg + "\n")

# === [P03] Signal Handlers ===
def handle_signal(sig, frame):
    """Handle signals for clean shutdown"""
    log(f"🛑 Received signal {sig}, shutting down...")
    cleanup()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_signal)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_signal)  # Termination signal

# === [P04] Process Management ===
def cleanup():
    """Clean up processes"""
    log("🧹 Cleaning up...")
    try:
        subprocess.run("pkill -f 'python3 smooth_eye_tracker.py' || true", shell=True)
        log("✅ Cleaned up processes")
    except Exception as e:
        log(f"⚠️ Error during cleanup: {e}")

# Register cleanup on exit
import atexit
atexit.register(cleanup)

# === [P05] Dependency Management ===
def check_and_install_dependencies():
    """Check and install required dependencies"""
    log("🔍 Checking dependencies...")
    
    # Required packages
    required_packages = [
        "opencv-python",
        "numpy"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == "opencv-python":
                __import__("cv2")
            else:
                __import__(package.replace("-", "_"))
            log(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            log(f"❌ {package} is not installed")
    
    if missing_packages:
        log(f"📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            log("✅ All dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            log(f"❌ Failed to install dependencies: {e}")
            sys.exit(1)

# === [P06] Main Function ===
def main():
    """Main function"""
    log("🚀 Starting Eye Tracker Runner")
    log(f"✅ UUID: {UUID}")
    log(f"📜 Log file: {LOGFILE}")
    
    # Check if script exists
    script_path = Path("smooth_eye_tracker.py")
    if not script_path.exists():
        log(f"❌ Script not found: {script_path}")
        sys.exit(1)
    
    # Make script executable
    try:
        script_path.chmod(0o755)
        log(f"✅ Made script executable: {script_path}")
    except Exception as e:
        log(f"⚠️ Could not make script executable: {e}")
    
    # Check and install dependencies
    check_and_install_dependencies()
    
    # Run the eye tracker
    log("👁️ Running eye tracker...")
    try:
        subprocess.run([sys.executable, str(script_path)], check=True)
        log("✅ Eye tracker completed successfully")
    except subprocess.CalledProcessError as e:
        log(f"❌ Eye tracker exited with error: {e}")
    except KeyboardInterrupt:
        log("🛑 Interrupted by user")
    except Exception as e:
        log(f"❌ Error running eye tracker: {e}")
    finally:
        cleanup()

# === [P07] Entry Point ===
if __name__ == "__main__":
    main()

# === PRF Compliance Table ===
# PRF ID | Assertion Description                | Code or Verbatim Line Snippet                | Block Location      | Met? | Explanation
# -------|--------------------------------------|----------------------------------------------|---------------------|------|------------
# P01    | Metadata                             | TS = datetime.now().strftime(...)           | [P01] Metadata      | ✅   | Includes timestamp, UUID, and log file
# P02    | Logging                              | def log(msg):                               | [P02] Logging       | ✅   | Logs to both console and file with timestamps
# P03    | Signal Handlers                      | def handle_signal(sig, frame):              | [P03] Signals       | ✅   | Handles SIGINT and SIGTERM for clean shutdown
# P04    | Process Management                   | def cleanup():                              | [P04] Process Mgmt  | ✅   | Cleans up processes on exit
# P05    | Dependency Management                | def check_and_install_dependencies():       | [P05] Dependencies  | ✅   | Automatically checks and installs required packages
# P06    | Main Function                        | def main():                                 | [P06] Main          | ✅   | Orchestrates the components and main loop
# P07    | Entry Point                          | if __name__ == "__main__":                  | [P07] Entry Point   | ✅   | Standard entry point pattern
