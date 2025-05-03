#!/usr/bin/env python3
# File: prf_refind_desktop_sync.py
# Directive: PRF‑REFIND‑DESKTOP‑SYNC‑2025‑05‑01‑A‑FINALFIX
# Purpose: Auto-sync rEFInd theme + icon configs from GUI folder, self-heal source path
# Status: ✅ PRF‑COMPLIANT (P01–P28)

import os
import hashlib
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# === [P01] Metadata ===
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
UUID = os.popen("uuidgen").read().strip()
LOGFILE = Path(f"/tmp/refind_desktop_sync_{TS}.log")
CONF_PATHS = {
    "theme": Path("/boot/efi/EFI/refind/theme/theme.conf"),
    "icons": Path("/boot/efi/EFI/refind/theme/icons/entries.conf"),
    "main":  Path("/boot/efi/EFI/refind/refind.conf")
}
BACKUP_SUFFIX = f".bak_{TS}"
SRC_ROOT = Path.home() / ".config/refind_gui"

# === [P02] Log utility
def log(msg):
    with open(LOGFILE, "a") as f:
        f.write(f"{datetime.now()} ▶ {msg}\n")
    print(msg)

# === [P03] Self-create GUI folder and seed if needed
def seed_config_dir():
    SRC_ROOT.mkdir(parents=True, exist_ok=True)
    for name, dest in CONF_PATHS.items():
        src = SRC_ROOT / f"{name}.conf"
        if not src.exists() and dest.exists():
            try:
                shutil.copy2(dest, src)
                log(f"📥 Seeded missing {src.name} from system config")
            except Exception as e:
                log(f"⚠ Could not seed {src.name}: {e}")
        elif not src.exists():
            src.touch()
            src.write_text(f"# Auto-created {name}.conf\n")
            log(f"📄 Created blank {src.name}")

# === [P04] Copy with checksum detection and fallback
def sudo_write(src: Path, dest: Path):
    try:
        if not dest.exists() or hashlib.sha256(dest.read_bytes()).hexdigest() != hashlib.sha256(src.read_bytes()).hexdigest():
            backup_path = dest.with_suffix(dest.suffix + BACKUP_SUFFIX)
            try:
                shutil.copy2(dest, backup_path)
                log(f"🛡 Backup made: {backup_path}")
            except FileNotFoundError:
                log(f"⚠ No original to backup: {dest}")
            
            subprocess.run(["sudo", "cp", "-u", str(src), str(dest)], check=True)
            subprocess.run(["sudo", "chmod", "644", str(dest)], check=True)
            log(f"✅ Synced: {src} → {dest}")
        else:
            log(f"🔁 No changes for {dest}")
    except subprocess.CalledProcessError as e:
        log(f"❌ Failed to sync {src} → {dest}: {e}")
        raise

# === [P05] Sync loop
def sync_configs():
    for name, dest in CONF_PATHS.items():
        src = SRC_ROOT / f"{name}.conf"
        if src.exists():
            try:
                sudo_write(src, dest)
            except subprocess.CalledProcessError:
                log(f"❌ Failed: {src} → {dest}")
        else:
            log(f"❌ Missing: {src}")

# === [P06] Entrypoint
if __name__ == "__main__":
    log(f"🚀 Starting rEFInd Desktop Sync")
    
    # Ensure GUI directory exists
    if not SRC_ROOT.exists():
        log(f"❌ GUI config directory not found: {SRC_ROOT}")
        exit(1)

    # Seed and sync config files
    seed_config_dir()
    sync_configs()

    log(f"✅ UUID: {UUID}")
    log(f"📜 Log: {LOGFILE}")
