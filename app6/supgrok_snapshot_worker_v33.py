#!/usr/bin/env python3
# File: supagrok_snapshot_worker.py
# PRF‑SNAPSHOT‑WORKER‑2025‑05‑06‑FINAL

"""
Supagrok Snapshot Worker
Encapsulates snapshot creation using GPG encryption and tar compression.
Designed to run as a containerized Tipi app, callable via FastAPI REST or websocket.
"""

import os
import subprocess
import uuid
import datetime
import json
import shutil
from pathlib import Path
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# === Config ===
SNAPSHOT_DIR = Path("/data/snapshots")
TMP_DIR = Path("/tmp/supagrok")
GPG_KEY_ID = os.getenv("SUPAGROK_GPG_KEY_ID", "")
GPG_PASSPHRASE = os.getenv("GPG_PASSPHRASE", "")

# === FastAPI Setup ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SnapshotRequest(BaseModel):
    name: str
    target_path: str  # folder to snapshot

# === Snapshot Logic ===
def create_snapshot(name: str, target_path: str) -> dict:
    uid = str(uuid.uuid4())
    now = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_base = f"supagrok_{name}_{now}_{uid}"
    archive_path = TMP_DIR / f"{output_base}.tar"
    encrypted_path = SNAPSHOT_DIR / f"{output_base}.tar.gpg"
    meta_path = SNAPSHOT_DIR / f"{output_base}.meta.json"

    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    # Step 1: Create tarball
    try:
        subprocess.run(["tar", "-cvf", str(archive_path), target_path], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Tar failed: {e}")

    # Step 2: Encrypt with GPG
    try:
        subprocess.run([
            "gpg", "--batch", "--yes", "--pinentry-mode", "loopback",
            "--passphrase", GPG_PASSPHRASE,
            "-o", str(encrypted_path),
            "-r", GPG_KEY_ID, "--encrypt", str(archive_path)
        ], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"GPG encryption failed: {e}")

    # Step 3: Create metadata
    meta = {
        "uuid": uid,
        "timestamp": now,
        "name": name,
        "input_path": target_path,
        "archive_path": str(encrypted_path),
        "meta_path": str(meta_path)
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    # Step 4: Clean up temp
    shutil.rmtree(TMP_DIR)
    return meta

# === REST Endpoint ===
@app.post("/snapshot")
def snapshot_post(req: SnapshotRequest):
    try:
        result = create_snapshot(req.name, req.target_path)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === WebSocket Status Endpoint ===
@app.websocket("/ws/snapshot")
async def snapshot_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        meta = create_snapshot(data['name'], data['target_path'])
        await websocket.send_json({"status": "done", "meta": meta})
    except Exception as e:
        await websocket.send_json({"status": "error", "error": str(e)})
    finally:
        await websocket.close()

# === Main Entrypoint ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("supagrok_snapshot_worker:app", host="0.0.0.0", port=8069, reload=False)
