#!/usr/bin/env python3
# ✅ PRF-P04, P12, P13, P14, P22 — Self-healing snapshot launcher

import os
import subprocess
import shutil
import sys

def log(msg): print(f"🌀 {msg}")

def fix_permissions():
    user = os.getenv("USER") or os.getenv("LOGNAME")
    log(f"Ensuring user '{user}' is in docker group...")
    subprocess.run(["sudo", "usermod", "-aG", "docker", user], check=False)
    subprocess.run(["sudo", "systemctl", "enable", "--now", "docker"], check=False)

def check_compose_method():
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    try:
        subprocess.run(["docker", "compose", "version"], check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ["docker", "compose"]
    except Exception:
        return None

def launch_compose():
    fix_permissions()
    compose_cmd = check_compose_method()
    if not compose_cmd:
        log("❌ Docker Compose is not installed.")
        sys.exit(1)

    cmd = ["sudo"] + compose_cmd + ["up", "-d", "--build"]
    log(f"🚀 Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        log("✅ Snapshot container launched.")
    except subprocess.CalledProcessError as e:
        if "denied" in str(e):
            log("❌ GHCR denied access. Verify the image is public or login.")
        else:
            log(f"⚠️ Unknown error: {e}")

if __name__ == "__main__":
    launch_compose()
