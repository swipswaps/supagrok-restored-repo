#!/usr/bin/env python3
# PRF-SUPAGROK-V3.2-SNAPSHOT-MANAGER
# UUID: 31f77d91-6cd2-4b4e-b3fe-c8dbe2de69b9
# PURPOSE: Add timestamp-based naming and GPG signing logic

import os, json, uuid, tarfile, hashlib, subprocess
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

RETENTION_LIMIT = 5
SNAPSHOT_DIR = Path.cwd()

def current_timestamp():
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

def generate_snapshot_name():
    ts = current_timestamp()
    base = f"supagrok_repo_snapshot_{ts}"
    return {
        "base": base,
        "txt": SNAPSHOT_DIR / f"{base}.txt",
        "tar": SNAPSHOT_DIR / f"{base}.tar.gz",
        "signed": SNAPSHOT_DIR / f"{base}.signed.txt"
    }

def sha256sum(file: Path):
    with file.open("rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def compress_snapshot(snapshot_paths):
    with tarfile.open(snapshot_paths["tar"], "w:gz") as tar:
        tar.add(snapshot_paths["txt"], arcname=snapshot_paths["txt"].name)
    print(f"📦 Compressed to {snapshot_paths['tar']}")

def gpg_sign_snapshot(snapshot_paths):
    try:
        subprocess.run([
            "gpg", "--output", str(snapshot_paths["signed"]),
            "--sign", str(snapshot_paths["txt"])
        ], check=True)
        print(f"🔐 GPG signed: {snapshot_paths['signed']}")
    except subprocess.CalledProcessError:
        print("❌ GPG signing failed (missing key?)")

def prune_old_snapshots():
    all_archives = sorted(SNAPSHOT_DIR.glob("supagrok_repo_snapshot_*.tar.gz"), key=os.path.getmtime)
    while len(all_archives) > RETENTION_LIMIT:
        victim = all_archives.pop(0)
        print(f"🧹 Removing old: {victim}")
        victim.unlink()

def pack_directory_gui():
    folder = filedialog.askdirectory(title="Select directory to snapshot")
    if not folder:
        return

    base = Path(folder)
    snapshot_paths = generate_snapshot_name()

    repo = []
    for path in base.rglob("*"):
        if path.is_file():
            rel = path.relative_to(base)
            mode = oct(path.stat().st_mode & 0o777)
            hval = sha256sum(path)
            repo.append({
                "path": str(rel),
                "mode": mode,
                "hash": hval,
                "content": path.read_text(encoding="utf-8", errors="ignore")
            })

    metadata = {
        "prf": "PRF‑SUPAGROK‑V3.2‑SNAPSHOT",
        "uuid": str(uuid.uuid4()),
        "timestamp": current_timestamp(),
        "source_dir": str(base),
        "repo": repo
    }

    with snapshot_paths["txt"].open("w", encoding="utf-8") as f:
        f.write(f"# PRF-SUPAGROK-V3.2-SNAPSHOT\n")
        f.write(f"# UUID: {metadata['uuid']}\n")
        f.write(f"# Timestamp: {metadata['timestamp']}\n\n")
        json.dump(metadata, f, indent=2)

    compress_snapshot(snapshot_paths)
    gpg_sign_snapshot(snapshot_paths)
    prune_old_snapshots()

    messagebox.showinfo("Snapshot", f"✅ Created snapshot:\n{snapshot_paths['txt'].name}")

def unpack_snapshot_gui():
    file = filedialog.askopenfilename(title="Select snapshot to restore", filetypes=[("Snapshot", "*.txt")])
    if not file:
        return
    with open(file, "r", encoding="utf-8") as f:
        data = json.loads("".join(line for line in f if not line.startswith("#")))
    for entry in data["repo"]:
        p = Path(entry["path"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(entry["content"], encoding="utf-8")
        os.chmod(p, int(entry["mode"], 8))
    messagebox.showinfo("Restore", f"✅ Restored {len(data['repo'])} files.")

def launch_gui():
    root = tk.Tk()
    root.title("Supagrok Snapshot Manager")
    root.geometry("350x200")

    tk.Button(root, text="📦 Create Timestamped Snapshot", width=35, command=pack_directory_gui).pack(pady=10)
    tk.Button(root, text="📂 Unpack Snapshot", width=35, command=unpack_snapshot_gui).pack(pady=10)
    tk.Button(root, text="🛑 Quit", width=35, command=root.quit).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    launch_gui()
