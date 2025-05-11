#!/usr/bin/env python3
# ✅ PRF-P13, P25 — Fallback GHCR → local dev image
import subprocess
import os

def log(m): print(f"🔁 {m}")

def build_local_image():
    log("Building local fallback image: supagrok/snapshot:dev")
    subprocess.run(["sudo", "docker", "build", "-t", "supagrok/snapshot:dev", "."], check=True)

def update_compose_image():
    path = "docker-compose.yml"
    if not os.path.exists(path):
        log("❌ docker-compose.yml not found")
        return
    with open(path, "r") as f:
        content = f.read()
    new_content = content.replace("ghcr.io/supagrok/snapshot-service:latest", "supagrok/snapshot:dev")
    with open(path, "w") as f:
        f.write(new_content)
    log("✅ Compose image updated to local fallback")

if __name__ == "__main__":
    build_local_image()
    update_compose_image()
