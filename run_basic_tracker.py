#!/usr/bin/env python3
# run_basic_tracker.py — PRF‑WEBCAM‑RUN‑2025‑05‑02
# Description: Run the basic eye tracker
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import subprocess
import time
import signal
from datetime import datetime

# === Metadata ===
print("🚀 Starting Basic Eye Tracker Runner")

# === Make script executable ===
try:
    script_path = "basic_eye_tracker.py"
    subprocess.run(["chmod", "+x", script_path], check=True)
    print(f"✅ Made script executable: {script_path}")
except Exception as e:
    print(f"⚠️ Could not make script executable: {e}")

# === Run the eye tracker ===
print("👁️ Running eye tracker...")
try:
    subprocess.run([sys.executable, "basic_eye_tracker.py"], check=True)
    print("✅ Eye tracker completed successfully")
except KeyboardInterrupt:
    print("🛑 Interrupted by user")
except Exception as e:
    print(f"❌ Error running eye tracker: {e}")

# === Clean up ===
print("🧹 Cleaning up...")
try:
    subprocess.run("pkill -f 'python3 basic_eye_tracker.py' || true", shell=True)
    print("✅ Cleaned up processes")
except Exception as e:
    print(f"⚠️ Error during cleanup: {e}")

print("👋 Done")
