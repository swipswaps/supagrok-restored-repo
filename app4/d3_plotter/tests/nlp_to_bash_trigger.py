#!/usr/bin/env python3
# PRF‑SUPAGROK‑V3‑NLP‑TO‑BASH‑TRIGGER
# UUID: 9de246f8-93c7-4e17-b311-d304c82b462e
# PURPOSE: Translate LLM/NLP prompts into trusted Bash commands and execute them

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

TRIGGER_LOG = Path("logs/nlp_triggers.jsonl")
ALLOWED_COMMANDS = {
    "check router": "./tests/test_ddwrt_latency_monitor.py",
    "reboot router": "curl -s 'http://192.168.1.1/apply.cgi?submit_button=Reboot' -u root:admin",
    "check uptime": "uptime",
    "test ping": "ping -c 3 8.8.8.8"
}

def trigger_command(prompt: str) -> dict:
    """
    Takes a natural language prompt and runs the mapped shell command.
    Logs input, matched command, and result.
    """
    if prompt not in ALLOWED_COMMANDS:
        return {"error": "Prompt not recognized or unsafe."}

    command = ALLOWED_COMMANDS[prompt]
    print(f"💬 Matched NLP Prompt: '{prompt}' → Running: {command}")
    start = datetime.now()
    result = subprocess.getoutput(command)
    elapsed = (datetime.now() - start).total_seconds()

    log_entry = {
        "prompt": prompt,
        "command": command,
        "output": result[:400],  # Truncate long results
        "elapsed_sec": round(elapsed, 2),
        "timestamp": datetime.now().isoformat()
    }
    TRIGGER_LOG.parent.mkdir(parents=True, exist_ok=True)
    with TRIGGER_LOG.open("a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return log_entry

if __name__ == '__main__':
    prompt = input("🧠 Enter NLP Prompt: ").strip()
    output = trigger_command(prompt)
    print(json.dumps(output, indent=2))
