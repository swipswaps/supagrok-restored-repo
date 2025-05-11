#!/usr/bin/env python3
# PRF‑SUPAGROK‑V3‑UNPACKER
# UUID: bfb3a62e-1d8a-4a8d-9243-df9f44afda35
# PURPOSE: Restore Supagrok repo from JSON-based snapshot

import json, os
from pathlib import Path

SNAPSHOT_FILE = "supagrok_repo_snapshot.txt"

def apply_permissions(path, mode_str):
    os.chmod(path, int(mode_str, 8))

def main():
    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        repo = json.load(f)

    for file in repo:
        path = Path(file["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file["content"], encoding="utf-8")
        apply_permissions(path, file.get("mode", "0644"))
        print(f"✅ Restored {path} with mode {file['mode']}")

if __name__ == "__main__":
    main()
