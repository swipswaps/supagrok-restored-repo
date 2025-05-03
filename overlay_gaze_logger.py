#!/usr/bin/env python3
# overlay_gaze_logger.py — PRF‑COMPOSITE‑2025‑04‑30‑A (Real Gaze Overlay Logger)
# Replaces simulated gaze with real-time input from gaze_ws_server.py (WebSocket)
# PRF‑P01–P25 enforced

import sys
import subprocess
import time
import os
import threading
import queue
import numpy as np
import cv2
from gaze_ws_server import get_next_gaze  # ⬅️ real gaze listener bridge

# === CONFIG ===
WINDOW_NAME = "Calibration"
LOG_FILE = "gaze_overlay.log"
BLINK_FILE = "calib_blink_fallback.log"
BUFFER_MAX = 1000

# === STATE ===
gaze_queue = queue.Queue(maxsize=BUFFER_MAX)
main_thread_id = threading.get_ident()

# === UTILS ===
def log_event(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [log] {message}\n")

def log_blink_warning():
    with open(BLINK_FILE, "a") as f:
        f.write(f"[{time.time()}] [WARN] Blink skipped due to threading lock\n")

def safe_show(win_name, frame):
    if threading.current_thread().ident == main_thread_id:
        cv2.imshow(win_name, frame)
    else:
        print("[warn] Imshow skipped — not in main thread")

# === GAZE INGESTION FROM WS ===
def gaze_data_relayer():
    while True:
        event = get_next_gaze()
        if event:
            try:
                gaze_queue.put_nowait(event)
            except queue.Full:
                print("[warn] Gaze buffer full — dropping real event")
        time.sleep(0.01)

# === CALIBRATION LOOP ===
def calibration_overlay_loop():
    while True:
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        if not gaze_queue.empty():
            event = gaze_queue.get()
            x, y, blink = event["x"], event["y"], event.get("blink", False)
            log_event(f"Gaze @ ({x},{y}), blink={blink}")
            if blink and threading.current_thread().ident != main_thread_id:
                log_blink_warning()
            cv2.circle(frame, (int(x), int(y)), 10, (0, 255, 0), -1)

        safe_show(WINDOW_NAME, frame)
        if cv2.waitKey(1) == 27:
            break

    cv2.destroyAllWindows()

# === START ===
threading.Thread(target=gaze_data_relayer, daemon=True).start()
calibration_overlay_loop()
