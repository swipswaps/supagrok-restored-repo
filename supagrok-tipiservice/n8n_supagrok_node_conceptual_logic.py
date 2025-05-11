#!/usr/bin/env python3

import requests
import time
import json

# This script provides conceptual Python logic for what might go into
# the 'execute' method of n8n nodes for Supagrok.
# It's for illustration and not a runnable n8n node itself.
# n8n nodes are typically written in Node.js/TypeScript.

# PRF Compliance: PRF-N8N-001, PRF-N8N-004, PRF-N8N-005 (conceptual)

class SupagrokN8NHelper:
    def __init__(self, server_url, api_key=None):
        self.base_url = f"{server_url.rstrip('/')}/api/v1"
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key # Example API key header

    def _request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # In n8n, you'd throw an error that n8n can catch and display
            error_data = {"error": str(e)}
            if e.response is not None:
                try:
                    error_data["response_body"] = e.response.json()
                except json.JSONDecodeError:
                    error_data["response_body"] = e.response.text
            print(f"API Error: {json.dumps(error_data)}") # Simulate n8n error logging
            raise # Re-raise for conceptual script flow
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise

    def create_snapshot(self, source_path, description=None, gpg_key_id_override=None,
                        await_completion=False, poll_interval=30, timeout=300):
        print(f"[N8N CONCEPT] Creating snapshot for: {source_path}")
        payload = {"source_path": source_path}
        if description:
            payload["description"] = description
        if gpg_key_id_override:
            payload["gpg_key_id_override"] = gpg_key_id_override

        initial_response = self._request("POST", "snapshots", json=payload)
        job_id = initial_response.get("job_id")

        if not await_completion or not job_id:
            return initial_response

        print(f"[N8N CONCEPT] Awaiting completion for job: {job_id}")
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Snapshot job {job_id} timed out after {timeout} seconds.")

            status_response = self.get_snapshot_status(job_id)
            current_status = status_response.get("status")
            print(f"[N8N CONCEPT] Job {job_id} status: {current_status}")

            if current_status in ["completed", "failed"]:
                return status_response

            time.sleep(poll_interval)

    def get_snapshot_status(self, job_id):
        print(f"[N8N CONCEPT] Getting status for job: {job_id}")
        return self._request("GET", f"snapshots/{job_id}")

if __name__ == "__main__":
    print("--- Conceptual n8n Supagrok Node Logic ---")
    # Example Usage (requires a running Supagrok service with the new API)
    # Replace with your Supagrok server URL
    helper = SupagrokN8NHelper(server_url="http://localhost:8000")

    try:
        # Simulate "Create Snapshot" node without awaiting completion
        print("\nScenario 1: Create snapshot (don't await)")
        job_info = helper.create_snapshot(source_path="n8n_test_data/scenario1", description="n8n test 1")
        print(f"Job created: {job_info}")
        job_id_1 = job_info.get("job_id")

        if job_id_1:
            # Simulate "Get Snapshot Status" node
            print(f"\nScenario 2: Get status for job {job_id_1}")
            status_info = helper.get_snapshot_status(job_id_1)
            print(f"Status received: {status_info}")

        # Simulate "Create Snapshot" node with awaiting completion
        print("\nScenario 3: Create snapshot (await completion)")
        completed_job_info = helper.create_snapshot(source_path="n8n_test_data/scenario3", description="n8n test 3 - await", await_completion=True, poll_interval=5, timeout=60)
        print(f"Awaited job completed: {completed_job_info}")

    except Exception as e:
        print(f"\nAn error occurred during conceptual execution: {e}")