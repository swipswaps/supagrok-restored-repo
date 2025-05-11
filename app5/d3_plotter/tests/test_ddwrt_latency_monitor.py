#!/usr/bin/env python3
# PRF‑SUPAGROK‑V3‑DDWRT‑LATENCY‑MONITOR
# Monitors DD-WRT panel latency and saves output

import os, time, json
from datetime import datetime
from pathlib import Path

class LLMProfiler:
    def __init__(self, model):
        self.model = model
        self.log_path = Path("logs/llm_latency.jsonl")

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *_):
        elapsed = round(time.time() - self.start, 3)
        entry = {"model": self.model, "elapsed_sec": elapsed, "timestamp": datetime.now().isoformat()}
        self.log_path.parent.mkdir(exist_ok=True, parents=True)
        self.log_path.write_text(json.dumps(entry) + "\n")
        print(f"⏱️ {self.model} latency: {elapsed}s")


def check_ddwrt():
    url = os.getenv("DDWRT_URL", "http://192.168.1.1/Status_Router.asp")
    with LLMProfiler("dd-wrt-healthcheck"):
        html = os.popen(f"curl -s --max-time 5 {url}").read()
        Path("logs/ddwrt_snapshot.html").write_text(html)

if __name__ == '__main__':
    check_ddwrt()
