#!/usr/bin/env python3
# PRF‑SUPAGROK‑PACKER‑V1.0
# UUID: aef8e17c-6025-421b-b94c-4e33c219b0c9
# PURPOSE: Recursively pack any directory into a structured, metadata-rich PRF snapshot for compliant restoration

import os
import json
import uuid
from datetime import datetime
from pathlib import Path

# 🌐 Default snapshot output filename
SNAPSHOT_FILENAME = "supagrok_repo_snapshot.txt"

def gather_files(base_dir: Path):
    repo = []
    for path in base_dir.rglob("*"):
        if path.is_file():
            rel_path = path.relative_to(base_dir)
            mode = oct(path.stat().st_mode & 0o777)
            content = path.read_text(encoding="utf-8", errors="ignore")
            repo.append({
                "path": str(rel_path),
                "mode": mode,
                "content": content
            })
    return repo

def pack_directory(target_dir):
    target_path = Path(target_dir).resolve()
    if not target_path.exists() or not target_path.is_dir():
        raise ValueError(f"❌ Directory does not exist: {target_path}")

    repo_data = gather_files(target_path)
    metadata = {
        "prf": "PRF‑SUPAGROK‑V3‑SNAPSHOT",
        "uuid": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source_dir": str(target_path),
        "repo": repo_data
    }

    with open(SNAPSHOT_FILENAME, "w", encoding="utf-8") as f:
        # 🧾 Emit header comments
        f.write(f"# PRF‑SUPAGROK‑V3‑SNAPSHOT\n")
        f.write(f"# UUID: {metadata['uuid']}\n")
        f.write(f"# Timestamp: {metadata['timestamp']}\n\n")
        json.dump(metadata, f, indent=2)

    print(f"📦 Packed {len(repo_data)} files into {SNAPSHOT_FILENAME}")
    print(f"🔐 UUID: {metadata['uuid']}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("🧰 Usage:\n  ./json_packer.py <target_directory_to_pack>")
        exit(1)

    try:
        pack_directory(sys.argv[1])
    except Exception as e:
        print(f"❌ Error: {e}")
