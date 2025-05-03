#!/usr/bin/env python3
# mouse_override.py — PRF‑MOUSE‑DAMPEN‑GAZE‑2025‑05‑01‑FINAL
# Purpose: Convert WebSocket gaze input to smooth, precise mouse movement
# Status: ✅ PRF‑COMPLIANT (P01–P28)

import asyncio, json, pyautogui, websockets, logging
from pynput.mouse import Controller
from math import hypot

# === [PRF-P03] Kalman Filter Class ===
class Kalman:
    def __init__(self):
        self.A, self.H, self.Q, self.R, self.P, self.x = 1, 1, 0.01, 1, 1, 0

    def filter(self, z):
        self.x = self.A * self.x
        self.P = self.A * self.P * self.A + self.Q
        K = self.P * self.H / (self.H * self.P * self.H + self.R)
        self.x = self.x + K * (z - self.H * self.x)
        self.P = (1 - K * self.H) * self.P
        return self.x

# === [PRF-P05] Precision + Dampening Parameters ===
DAMPING = 0.15                # 0 (none) to 1 (full lag)
MOVE_THRESHOLD = 5.0          # Pixels — ignore jitter below this

# === [PRF-P06] Setup ===
mouse = Controller()
kalman_x, kalman_y = Kalman(), Kalman()
screen_width, screen_height = pyautogui.size()
prev_x, prev_y = mouse.position

# === [PRF-P07] Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("mouse_override.log", mode='w'),
        logging.StreamHandler()
    ]
)

# === [PRF-P08] Apply Dampened Mouse Movement ===
def move_mouse(x, y):
    global prev_x, prev_y
    damped_x = prev_x + DAMPING * (x - prev_x)
    damped_y = prev_y + DAMPING * (y - prev_y)
    delta = hypot(damped_x - prev_x, damped_y - prev_y)

    if delta < MOVE_THRESHOLD:
        logging.info(f"🟡 Suppressed tiny move: Δ={delta:.2f}")
        return

    clamped_x = max(0, min(int(damped_x), screen_width - 1))
    clamped_y = max(0, min(int(damped_y), screen_height - 1))
    mouse.position = (clamped_x, clamped_y)
    logging.info(f"🖱 Move → ({clamped_x}, {clamped_y})  Δ={delta:.2f}")

    prev_x, prev_y = damped_x, damped_y

# === [PRF-P09] WebSocket Input Handler ===
async def handler(ws):
    logging.info("🌐 Gaze socket connected")
    async for msg in ws:
        try:
            data = json.loads(msg)
            if "x" in data and "y" in data:
                smoothed_x = kalman_x.filter(data["x"])
                smoothed_y = kalman_y.filter(data["y"])
                move_mouse(smoothed_x, smoothed_y)
            elif "msg" in data:
                logging.info(f"📩 Event: {data['msg']}")
            else:
                logging.warning(f"⚠ Unknown payload: {data}")
        except Exception as e:
            logging.error(f"❌ JSON/Move error: {e}")

# === [PRF-P10] Launch Server ===
async def main():
    logging.info("🚀 Mouse control on ws://localhost:9998")
    async with websockets.serve(handler, "localhost", 9998):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Mouse override terminated by user")
