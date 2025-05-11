#!/usr/bin/env python3
# PRF-D3-LOGS-TSV-REFLECTOR
# Reads latest rotated logs and writes top entries to logs_index.tsv for D3 viewer

import os
import glob
import time

LOG_DIR = "./logs"
OUTPUT_FILE = "logs_index.tsv"
ENTRIES_PER_LOG = 5  # How many entries to extract per log file
MAX_LINES = 50       # Cap total entries

def extract_latest_entries():
    all_lines = []
    for log_file in sorted(glob.glob(os.path.join(LOG_DIR, "*.log")), reverse=True):
        with open(log_file, "r") as f:
            lines = f.readlines()[-ENTRIES_PER_LOG:]
            all_lines.extend(lines)
        if len(all_lines) >= MAX_LINES:
            break
    all_lines = sorted(set(all_lines))[-MAX_LINES:]
    return ["timestamp\tmagnitude\n"] + all_lines

def main():
    print("📤 Updating logs_index.tsv from latest EEG logs...")
    lines = extract_latest_entries()
    with open(OUTPUT_FILE, "w") as f:
        f.writelines(lines)
    print(f"✅ {len(lines)-1} entries written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
