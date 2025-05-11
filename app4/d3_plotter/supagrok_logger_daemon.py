#!/usr/bin/env python3
# PRF-SUPAGROK-ROTATING-LOGGER-SAFE
# EEG-style rotating log daemon with lockfile protection and signal-safe exit

import os
import time
import datetime
import signal
import sys

LOG_DIR = "./logs"
LOCKFILE = "/tmp/supagrok_logger.lock"
ROTATE_INTERVAL = 300  # seconds
ENTRIES_PER_ROTATION = 60  # EEG ticks per rotation interval

# Ensure output directory is writable
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except PermissionError as e:
    print(f"❌ Cannot create or write to {LOG_DIR}: {e}")
    sys.exit(1)

# Signal handler for graceful shutdown
def cleanup_and_exit(signum, frame):
    print("🛑 Caught signal, exiting cleanly...")
    try:
        if os.path.exists(LOCKFILE):
            os.remove(LOCKFILE)
            print(f"🧹 Lockfile removed: {LOCKFILE}")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")
    sys.exit(0)

# Register signal traps
signal.signal(signal.SIGINT, cleanup_and_exit)
signal.signal(signal.SIGTERM, cleanup_and_exit)

# Check for existing instance
if os.path.exists(LOCKFILE):
    print("⛔ Logger already running. Exiting.")
    sys.exit(1)

# Create lockfile
with open(LOCKFILE, "w") as f:
    f.write(str(os.getpid()))

print("🧠 Supagrok Logger Daemon — Running...")

try:
    while True:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(LOG_DIR, f"eeglog_{timestamp}.log")
        with open(log_path, "w") as f:
            for _ in range(ENTRIES_PER_ROTATION):
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                val = round(2.5 + (os.urandom(1)[0] % 40) / 10, 2)
                f.write(f"{ts}\t{val}\n")
                print(f"📈 Logged: {ts}\t{val}")
                time.sleep(1)
        print(f"📁 Rotated log: {log_path}")
except Exception as e:
    print(f"❌ Fatal error: {e}")
finally:
    cleanup_and_exit(None, None)
