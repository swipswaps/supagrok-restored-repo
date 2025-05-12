#!/usr/bin/env python3
# PRF‑SUPAGROK‑V3‑UNPACKER
# UUID: 2e8c435a-7cb4-40d2-9e0c-324218bca0c3
# PURPOSE: Restore repo from structured PRF snapshot with optional PRF comment headers

import json, os
from pathlib import Path

SNAPSHOT_FILE = "supagrok_repo_snapshot.txt"

def apply_permissions(path, mode_str):
    os.chmod(path, int(mode_str, 8))

def main():
    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        # ✅ Strip PRF header comments for compatibility
        lines = f.readlines()
        json_str = "".join(line for line in lines if not line.strip().startswith("#"))
        data = json.loads(json_str)

    uuid = data.get("uuid", "MISSING_UUID")
    print(f"🔐 PRF Snapshot UUID: {uuid}")

    repo = data.get("repo", [])
    for file in repo:
        path = Path(file["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file["content"], encoding="utf-8")
        apply_permissions(path, file.get("mode", "0644"))
        print(f"✅ Restored {path} with mode {file['mode']}")

if __name__ == "__main__":
    main()
