#!/usr/bin/env python3
# NLP → Bash trigger

import os, json, subprocess
from pathlib import Path
from datetime import datetime

TRIGGER_LOG = Path("logs/nlp_triggers.jsonl")

ALLOWED_COMMANDS = {
    "ping test": "ping -c 2 8.8.8.8",
    "check uptime": "uptime",
    "reboot router": "curl -s 'http://192.168.1.1/apply.cgi?submit_button=Reboot' -u root:admin"
}

def trigger(prompt):
    if prompt not in ALLOWED_COMMANDS:
        return {"error": "Unrecognized"}
    cmd = ALLOWED_COMMANDS[prompt]
    result = subprocess.getoutput(cmd)
    log = {
        "prompt": prompt,
        "command": cmd,
        "output": result[:300],
        "timestamp": datetime.now().isoformat()
    }
    TRIGGER_LOG.parent.mkdir(parents=True, exist_ok=True)
    with TRIGGER_LOG.open("a") as f:
        f.write(json.dumps(log) + "\n")
    return log

if __name__ == "__main__":
    prompt = input("Command? ").strip()
    print(json.dumps(trigger(prompt), indent=2))
