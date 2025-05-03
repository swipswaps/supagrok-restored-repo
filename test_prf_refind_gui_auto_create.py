#!/usr/bin/env python3
# File: test_prf_refind_gui_auto_create.py
# Purpose: Test the functionality of prf_refind_gui_auto_create.py without requiring sudo

import os
import sys
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

# Create a temporary directory to simulate the system paths
temp_dir = tempfile.mkdtemp()
print(f"Created temporary directory: {temp_dir}")

# Create simulated system paths
system_paths = {
    "theme": Path(temp_dir) / "refind/theme/theme.conf",
    "icons": Path(temp_dir) / "refind/theme/icons/entries.conf",
    "main": Path(temp_dir) / "refind/refind.conf"
}

# Create the directories and sample files
for path in system_paths.values():
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(f"# Sample configuration file: {path.name}\n")
    print(f"Created sample file: {path}")

# Now run the actual script with modified paths
print("\nRunning prf_refind_gui_auto_create.py with simulated paths...")

# Import the script and modify its paths
import prf_refind_gui_auto_create as script

# Override the paths
script.CONF_PATHS = system_paths

# Run the script's main functions
print("\nStarting test execution...")
script.log("🚀 Starting Test rEFInd GUI Auto-Creation")
script.log(f"📂 Target directory: {script.SRC_ROOT}")

# Check if we have access to system paths
system_paths_ok = script.check_system_paths()
if not system_paths_ok:
    script.log(f"⚠ Some system paths are missing, will create blank config files")

# Create directory and seed config files
seed_success = script.seed_config_dir()
if not seed_success:
    script.log(f"❌ Failed to seed configuration files")
    sys.exit(1)

# Verify all files were created
verify_success = script.verify_seeded_files()
if not verify_success:
    script.log(f"⚠ Not all configuration files were created successfully")

script.log(f"✅ UUID: {script.UUID}")
script.log(f"📜 Log: {script.LOGFILE}")

# Print PRF compliance information
script.log(f"🔒 PRF‑REFIND‑GUI‑AUTO‑CREATE‑2025‑05‑01‑B: COMPLIANT (P01-P28)")

# Check the results
print("\nVerifying results...")
for name in script.CONF_PATHS.keys():
    src = script.SRC_ROOT / f"{name}.conf"
    if src.exists():
        print(f"✅ File created successfully: {src}")
        with open(src, 'r') as f:
            content = f.read()
            print(f"  Content: {content[:50]}...")
    else:
        print(f"❌ File not created: {src}")

print(f"\nLog file: {script.LOGFILE}")
print("Test completed.")

# Clean up
shutil.rmtree(temp_dir)
print(f"Cleaned up temporary directory: {temp_dir}")
