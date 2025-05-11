#!/usr/bin/env python3
# PRF-SUPAGROK-V3-SNAPSHOT-WORKER
# UUID: 1f0a7b3c-6e9d-4c8a-b5d2-7e6f0a3b9c8d-v2
# PURPOSE: FastAPI application for creating GPG-encrypted, tarballed snapshots
#          with WebSocket status updates.
# PRF Relevance: P01, P02, P03, P06, P07, P08, P10, P11, P14, P16, P19, P21, P28

from fastapi import FastAPI, WebSocket, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocketDisconnect
import os
import subprocess
import uuid
import asyncio 
from pathlib import Path
from datetime import datetime
import tarfile 
import json # For metadata

# --- Configuration & Globals ---
app = FastAPI()
active_websockets = [] 
SNAPSHOT_BASE_DIR = Path("/data") # Base directory for source and output within container
SNAPSHOT_OUTPUT_DIR = SNAPSHOT_BASE_DIR / "output"
SNAPSHOT_SOURCE_DIR_DEFAULT = SNAPSHOT_BASE_DIR / "source" # Default source if not specified in payload

# Ensure directories exist at startup (though volume mount should handle host side)
SNAPSHOT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_SOURCE_DIR_DEFAULT.mkdir(parents=True, exist_ok=True)


# --- WebSocket Handling ---
async def broadcast_message(message: str, job_id: str = None, level: str = "INFO"):
    """PRF-P07, P08: Broadcasts a message to all connected WebSocket clients."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    payload = {
        "timestamp": timestamp,
        "message": message,
        "level": level
    }
    if job_id:
        payload["job_id"] = job_id
    
    for websocket in active_websockets:
        try:
            await websocket.send_json(payload)
        except Exception as e:
            print(f"Error broadcasting to WebSocket: {e}")

@app.websocket("/ws/snapshot")
async def websocket_endpoint(websocket: WebSocket):
    """PRF-P08, P21: Manages WebSocket connections for status updates."""
    await websocket.accept()
    active_websockets.append(websocket)
    await broadcast_message("Client connected to snapshot status.", level="DEBUG")
    try:
        while True:
            await websocket.receive_text() 
    except WebSocketDisconnect:
        log_message = "Client disconnected."
        active_websockets.remove(websocket)
        await broadcast_message(log_message, level="DEBUG") 
    except Exception as e:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
        await broadcast_message(f"WebSocket error: {str(e)}. Client removed.", level="ERROR")


# --- Health Check ---
@app.get("/health")
def health_check():
    """PRF-P11: Simple health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# --- Snapshot Logic ---
async def run_snapshot_process_async(job_id: str, source_path_str: str, gpg_key_id: str, gpg_passphrase: str):
    """PRF-P03, P14, P15: Core snapshot creation logic, run asynchronously."""
    await broadcast_message(f"Starting snapshot for '{source_path_str}'.", job_id=job_id)

    source_path = Path(source_path_str)
    if not source_path.is_absolute(): # Ensure paths are absolute if coming from payload
        source_path = SNAPSHOT_BASE_DIR / source_path_str # Assume relative to /data if not absolute
        source_path = source_path.resolve() # Resolve to an absolute path

    if not source_path.exists() or not source_path.is_dir():
        err_msg = f"Source path '{source_path}' does not exist or is not a directory."
        await broadcast_message(err_msg, job_id=job_id, level="ERROR")
        # Note: This runs in a background task, can't directly raise HTTPException to client
        # Status is communicated via WebSocket and metadata file.
        snapshot_metadata = {
            "job_id": job_id, "status": "failed", "error": err_msg, 
            "timestamp_utc": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        }
        meta_path_on_fail = SNAPSHOT_OUTPUT_DIR / f"snapshot_{job_id}_{snapshot_metadata['timestamp_utc']}.meta.json"
        with open(meta_path_on_fail, "w") as f:
            json.dump(snapshot_metadata, f, indent=2)
        return

    timestamp_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    # Sanitize source_path.name for use in filename, replace slashes etc.
    sanitized_source_name = source_path.name.replace("/", "_").replace("\\", "_")
    archive_basename = f"snapshot_{sanitized_source_name}_{job_id}_{timestamp_str}"
    tar_path = SNAPSHOT_OUTPUT_DIR / f"{archive_basename}.tar.gz"
    gpg_path = SNAPSHOT_OUTPUT_DIR / f"{archive_basename}.tar.gz.gpg"
    meta_path = SNAPSHOT_OUTPUT_DIR / f"{archive_basename}.meta.json" 

    snapshot_metadata = { 
        "job_id": job_id,
        "timestamp_utc": timestamp_str,
        "source_path_in_container": str(source_path),
        "archive_filename_tar": str(tar_path.name),
        "archive_filename_gpg": str(gpg_path.name),
        "gpg_key_id": gpg_key_id,
        "status": "pending"
    }

    try:
        await broadcast_message(f"Creating archive '{tar_path.name}'...", job_id=job_id)
        with tarfile.open(tar_path, "w:gz") as tar:
            # Add the contents of source_path, not source_path itself as a top-level dir in tar
            tar.add(source_path, arcname=".") 
        snapshot_metadata["tar_size_bytes"] = tar_path.stat().st_size
        await broadcast_message(f"Archive created successfully. Size: {snapshot_metadata['tar_size_bytes']} bytes.", job_id=job_id)

        await broadcast_message(f"Encrypting archive with GPG Key ID '{gpg_key_id}'...", job_id=job_id)
        gpg_command = [
            "gpg", "--batch", "--yes", "--trust-model", "always",
            "--pinentry-mode", "loopback", 
            "--passphrase", gpg_passphrase,
            "-r", gpg_key_id,
            "--output", str(gpg_path),
            "--encrypt", str(tar_path)
        ]
        
        # Run GPG encryption
        process = await asyncio.create_subprocess_exec(
            *gpg_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            snapshot_metadata["gpg_size_bytes"] = gpg_path.stat().st_size
            snapshot_metadata["status"] = "completed"
            await broadcast_message(f"Encryption successful. GPG file size: {snapshot_metadata['gpg_size_bytes']} bytes.", job_id=job_id)
            
            # Clean up unencrypted tar file
            tar_path.unlink()
            await broadcast_message(f"Removed unencrypted tar file.", job_id=job_id, level="DEBUG")
        else:
            stderr_output = stderr.decode().strip() if stderr else "Unknown GPG error"
            err_msg = f"GPG encryption failed: {stderr_output}"
            await broadcast_message(err_msg, job_id=job_id, level="ERROR")
            snapshot_metadata["status"] = "failed"
            snapshot_metadata["error"] = err_msg
        
        await broadcast_message(f"Snapshot process finished with status: {snapshot_metadata['status']}.", job_id=job_id)

    except Exception as e:
        err_msg = f"An error occurred: {str(e)}"
        await broadcast_message(err_msg, job_id=job_id, level="ERROR")
        snapshot_metadata["status"] = "failed"
        snapshot_metadata["error"] = str(e)
        if tar_path.exists(): tar_path.unlink(missing_ok=True)
        if gpg_path.exists() and snapshot_metadata["status"] == "failed": gpg_path.unlink(missing_ok=True)
    finally:
        with open(meta_path, "w") as f:
            json.dump(snapshot_metadata, f, indent=2)
        await broadcast_message(f"Metadata written to '{meta_path.name}'.", job_id=job_id, level="DEBUG")


@app.post("/snapshot")
async def create_snapshot(request_data: dict):
    """Create a snapshot of the specified source path."""
    job_id = str(uuid.uuid4())
    
    # Extract parameters from request data
    source_path = request_data.get("source_path", "/data/source")
    output_path = request_data.get("output_path")
    gpg_key_id = os.getenv("GPG_KEY_ID", request_data.get("gpg_key_id"))
    gpg_passphrase = os.getenv("GPG_PASSPHRASE", request_data.get("passphrase"))
    
    # Start the snapshot process in the background
    asyncio.create_task(process_snapshot(source_path, output_path, gpg_key_id, gpg_passphrase, job_id))
    
    # Return 202 Accepted for asynchronous processing
    return JSONResponse(
        status_code=202,
        content={"status": "Snapshot process initiated.", "job_id": job_id}
    )

# PRF-P16: Uvicorn startup for direct execution (though Docker CMD is preferred)
if __name__ == "__main__":
    import uvicorn
    # Example defaults for local dev; in Docker, these come from docker-compose.yml
    os.environ.setdefault("GPG_KEY_ID", "your_gpg_key_id_for_local_dev") 
    os.environ.setdefault("GPG_PASSPHRASE", "your_gpg_passphrase_for_local_dev")
    print(f"Running Supagrok Snapshot Worker locally with GPG_KEY_ID: {os.getenv('GPG_KEY_ID')}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
