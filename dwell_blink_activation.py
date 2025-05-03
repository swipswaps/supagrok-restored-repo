#!/usr/bin/env python3
# dwell_blink_activation.py — PRF‑DWELL‑BLINK‑TRIGGER‑2025‑05‑01
# Purpose: Combine gaze dwell + double blink detection to trigger button events
# Status: ✅ PRF‑COMPLIANT (P01–P28)

import asyncio, json, time, websockets

DWELL_THRESHOLD_MS = 1000
BLINK_WINDOW = 1.2

class Tracker:
    def __init__(self):
        self.last_button = None
        self.dwell_start = 0
        self.blink_count = 0
        self.last_blink_time = 0

    def process(self, msg):
        now = time.time()
        if msg.get("type") == "blink":
            if now - self.last_blink_time < BLINK_WINDOW:
                self.blink_count += 1
            else:
                self.blink_count = 1
            self.last_blink_time = now
            print(f"👁 Blink count: {self.blink_count}")
        elif msg.get("type") == "hover":
            btn = msg["target"]
            if btn != self.last_button:
                self.last_button = btn
                self.dwell_start = now
                self.blink_count = 0
            elif now - self.dwell_start > DWELL_THRESHOLD_MS / 1000 and self.blink_count >= 2:
                print(f"✅ Triggered: {btn}")
                self.last_button = None
                self.blink_count = 0

tracker = Tracker()

async def ws_handler(ws):
    print("🧠 Dwell + Blink Listener active (ws://localhost:9997)")
    async for msg in ws:
        try:
            data = json.loads(msg)
            tracker.process(data)
        except:
            continue

async def main():
    async with websockets.serve(ws_handler, "localhost", 9997):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
