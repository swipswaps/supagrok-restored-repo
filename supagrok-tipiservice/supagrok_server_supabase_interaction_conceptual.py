#!/usr/bin/env python3

import os
import uuid
from datetime import datetime, timezone
from supabase import create_client, Client
import time # for simulating work

# Conceptual script demonstrating how Supagrok server-side logic
# (e.g., within supagrok_snapshot_worker.py) might interact with Supabase.

# PRF Compliance: PRF-GEN-009, PRF-API (backend for API_DESIGN.md)

# --- Configuration (Ideally from environment variables or a config file) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL") # e.g., "https://<your-project-ref>.supabase.co"
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") # Use the service_role key for backend operations

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

SNAPSHOTS_TABLE = "snapshots" # Name of your table in Supabase
STORAGE_BUCKET_NAME = "snapshot-artifacts" # Name of your Supabase Storage bucket

def log_message(job_id, message, level="INFO"):
    """Conceptual: Appends a log message to the snapshot's log array in Supabase."""
    print(f"LOG [{level}] (Job: {job_id}): {message}")
    try:
        # Fetch current logs
        response = supabase.table(SNAPSHOTS_TABLE).select("logs").eq("job_id", job_id).single().execute()
        current_logs = response.data.get("logs", []) if response.data else []
        
        # Append new log
        current_logs.append(f"{datetime.now(timezone.utc).isoformat()} [{level}] - {message}")
        
        # Update logs in Supabase
        supabase.table(SNAPSHOTS_TABLE).update({"logs": current_logs, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("job_id", job_id).execute()
    except Exception as e:
        print(f"Error logging to Supabase for job {job_id}: {e}")

def create_snapshot_record_in_supabase(source_path: str, description: str = None, gpg_key_id_override: str = None) -> str:
    """Creates an initial snapshot record in Supabase and returns the job_id."""
    job_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    
    snapshot_data = {
        "job_id": job_id,
        "status": "pending",
        "source_path": source_path,
        "description": description,
        "gpg_key_id_override": gpg_key_id_override,
        "created_at": now_iso,
        "updated_at": now_iso,
        "logs": [f"{now_iso} [INFO] - Job created for source: {source_path}"]
    }
    
    response = supabase.table(SNAPSHOTS_TABLE).insert(snapshot_data).execute()
    if response.data:
        print(f"Snapshot record created in Supabase with job_id: {job_id}")
        return job_id
    else:
        # Supabase client typically raises an exception on error, but good to check
        print(f"Error creating snapshot record in Supabase: {response.error}")
        raise Exception(f"Could not create snapshot record: {response.error}")

def update_snapshot_status_in_supabase(job_id: str, status: str, error_message: str = None, artifact_identifier: str = None, size_bytes: int = None):
    """Updates the status and other details of a snapshot record in Supabase."""
    update_data = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if error_message:
        update_data["error_message"] = error_message
        log_message(job_id, f"Error: {error_message}", level="ERROR")
    if artifact_identifier:
        update_data["output_artifact_identifier"] = artifact_identifier
    if size_bytes is not None:
        update_data["size_bytes"] = size_bytes
        
    response = supabase.table(SNAPSHOTS_TABLE).update(update_data).eq("job_id", job_id).execute()
    if not response.data and response.error: # Check if update failed
         print(f"Error updating snapshot {job_id} to status {status}: {response.error}")
    else:
        print(f"Snapshot {job_id} updated to status: {status}")

def upload_artifact_to_supabase_storage(job_id: str, local_file_path: str, artifact_name: str) -> str:
    """Uploads a file to Supabase Storage and returns the storage path."""
    storage_path = f"{job_id}/{artifact_name}" # Example: <job_id>/snapshot.tar.gz.gpg
    with open(local_file_path, 'rb') as f:
        # The supabase-py client's storage methods might require 'file_options' for content type if not inferred.
        # For encrypted binary files, 'application/octet-stream' is often appropriate.
        response = supabase.storage.from_(STORAGE_BUCKET_NAME).upload(
            path=storage_path,
            file=f,
            file_options={"content-type": "application/octet-stream"}
        )
    # The response object structure for storage upload might vary. Check supabase-py docs.
    # Typically, a successful upload doesn't return extensive data, but errors are raised.
    print(f"Artifact {artifact_name} for job {job_id} uploaded to Supabase Storage at path: {storage_path}")
    return storage_path # Or a full URL if preferred/available

def process_snapshot_job(job_id: str, source_path: str):
    """Simulates the actual snapshot processing work."""
    log_message(job_id, f"Starting processing for source: {source_path}")
    update_snapshot_status_in_supabase(job_id, "running")
    
    # 1. Simulate data gathering, GPG encryption, etc.
    time.sleep(5) # Simulate work
    local_artifact_path = f"/tmp/{job_id}_snapshot.tar.gz.gpg" # Dummy local path
    with open(local_artifact_path, "w") as f: # Create a dummy file
        f.write("This is a dummy encrypted snapshot.")
    artifact_size = os.path.getsize(local_artifact_path)
    log_message(job_id, "Snapshot artifact created locally.")

    # 2. Upload to Supabase Storage
    storage_identifier = upload_artifact_to_supabase_storage(job_id, local_artifact_path, "snapshot.tar.gz.gpg")
    log_message(job_id, f"Artifact uploaded to Supabase Storage: {storage_identifier}")

    # 3. Update final status in Supabase
    update_snapshot_status_in_supabase(job_id, "completed", artifact_identifier=storage_identifier, size_bytes=artifact_size)
    log_message(job_id, "Job completed successfully.")
    os.remove(local_artifact_path) # Clean up dummy file

if __name__ == "__main__":
    print("--- Conceptual Supagrok Server with Supabase Interaction ---")
    # This would typically be triggered by an API call
    test_job_id = create_snapshot_record_in_supabase(source_path="project_alpha/data_files", description="Daily backup of Project Alpha")
    
    if test_job_id:
        try:
            process_snapshot_job(test_job_id, "project_alpha/data_files")
        except Exception as e:
            print(f"Processing failed for job {test_job_id}: {e}")
            update_snapshot_status_in_supabase(test_job_id, "failed", error_message=str(e))