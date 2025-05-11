#!/usr/bin/env python3
# PRF‑SUPAGROK‑V3‑DDWRT‑LATENCY‑MONITOR
# UUID: f382e9e3-cf7d-4a9c-a117-62f33e8cbf1f
# VERSION: v2 — Uses --max-time to avoid stall, path-safe
# PURPOSE: Executes DD-WRT panel latency check using curl with timeout + logs HTML snapshot

import time, os, json
from pathlib import Path
from datetime import datetime

class LLMProfiler:
    def __init__(self, model_name):
        self.model = model_name
        self.log_path = Path("logs/llm_latency.jsonl")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start
        entry = {
            "model": self.model,
            "elapsed_sec": round(elapsed, 3),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with self.log_path.open("a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"🕒 [{self.model}] took {elapsed:.3f} sec")

def check_ddwrt_status():
    status_url = os.getenv("DDWRT_URL", "http://192.168.1.1/Status_Router.asp")
    print(f"🌐 Checking DD-WRT at {status_url} with timeout …")
    with LLMProfiler("dd-wrt-healthcheck"):
        response = os.popen(f"curl -s --max-time 5 {status_url}").read()
    snapshot_file = Path("logs/ddwrt_snapshot.html")
    snapshot_file.write_text(response)
    print(f"🧾 Snapshot saved: {snapshot_file}")

if __name__ == '__main__':
    check_ddwrt_status()
