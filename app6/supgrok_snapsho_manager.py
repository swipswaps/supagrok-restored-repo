#!/usr/bin/env python3
# PRF-SUPAGROK-V3-SNAPSHOT-MANAGER
# UUID: 57f4eabc-a63c-4377-b7a1-9dd99fd5c2e4
# PURPOSE: Full-featured GUI, compression, GPG-sign, hash-verify, and retention snapshot tool

import os, json, uuid, shutil, tarfile, hashlib, subprocess
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

SNAPSHOT_DIR = Path.cwd()
SNAPSHOT_FILE = SNAPSHOT_DIR / "supagrok_repo_snapshot.txt"
SNAPSHOT_ARCHIVE = SNAPSHOT_FILE.with_suffix(".tar.gz")
RETENTION_LIMIT = 5  # configurable

# 🧮 HASH TOOL

def sha256sum(file: Path):
    with file.open("rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

# 📦 COMPRESSION

def compress_snapshot():
    with tarfile.open(SNAPSHOT_ARCHIVE, "w:gz") as tar:
        tar.add(SNAPSHOT_FILE, arcname=SNAPSHOT_FILE.name)
    print(f"📦 Compressed to {SNAPSHOT_ARCHIVE}")

# 🔐 GPG SIGN

def gpg_sign_snapshot():
    signed_path = SNAPSHOT_FILE.with_suffix(".signed.txt")
    subprocess.run(["gpg", "--output", str(signed_path), "--sign", str(SNAPSHOT_FILE)], check=True)
    print(f"🔐 Signed snapshot: {signed_path}")

# 🧹 RETENTION

def prune_old_snapshots():
    archives = sorted(SNAPSHOT_DIR.glob("supagrok_repo_snapshot*.tar.gz"), key=os.path.getmtime)
    while len(archives) > RETENTION_LIMIT:
        old = archives.pop(0)
        old.unlink()
        print(f"🧹 Deleted old snapshot: {old}")

# 📁 PACKER

def pack_directory_gui():
    target = filedialog.askdirectory(title="Select directory to pack")
    if not target:
        return
    base = Path(target)
    repo_data = []
    for path in base.rglob("*"):
        if path.is_file():
            rel = path.relative_to(base)
            mode = oct(path.stat().st_mode & 0o777)
            hashval = sha256sum(path)
            repo_data.append({
                "path": str(rel),
                "mode": mode,
                "hash": hashval,
                "content": path.read_text(encoding="utf-8", errors="ignore")
            })

    metadata = {
        "prf": "PRF-SUPAGROK-V3-SNAPSHOT",
        "uuid": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source_dir": str(base),
        "repo": repo_data
    }

    with SNAPSHOT_FILE.open("w", encoding="utf-8") as f:
        f.write(f"# PRF-SUPAGROK-V3-SNAPSHOT\n")
        f.write(f"# UUID: {metadata['uuid']}\n")
        f.write(f"# Timestamp: {metadata['timestamp']}\n\n")
        json.dump(metadata, f, indent=2)

    compress_snapshot()
    gpg_sign_snapshot()
    prune_old_snapshots()
    messagebox.showinfo("Snapshot", "✅ Snapshot complete.")

# 🔁 UNPACKER

def unpack_snapshot_gui():
    file = filedialog.askopenfilename(title="Select snapshot file", filetypes=[("Snapshot", "*.txt")])
    if not file:
        return
    with open(file, "r", encoding="utf-8") as f:
        data = json.loads("".join(line for line in f if not line.startswith("#")))
    for file in data["repo"]:
        path = Path(file["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file["content"], encoding="utf-8")
        os.chmod(path, int(file["mode"], 8))
    messagebox.showinfo("Unpack", f"✅ Restored {len(data['repo'])} files.")

# 🎛️ GUI

def launch_gui():
    root = tk.Tk()
    root.title("Supagrok Snapshot Manager")
    root.geometry("320x180")

    tk.Button(root, text="📦 Pack Snapshot", width=30, command=pack_directory_gui).pack(pady=10)
    tk.Button(root, text="📂 Unpack Snapshot", width=30, command=unpack_snapshot_gui).pack(pady=10)
    tk.Button(root, text="🛑 Quit", width=30, command=root.quit).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    launch_gui()
