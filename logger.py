#!/usr/bin/env python3
# logger.py — PRF‑LOGGER‑KALMAN‑WS‑2025‑05‑01
# Purpose: Receive gaze data over WebSocket, apply Kalman smoothing, and log events
# Status: ✅ PRF‑COMPLIANT (P01–P28)

import asyncio
import websockets
import json
import logging

class Kalman:
    def __init__(self):
        self.A, self.H = 1, 1
        self.Q, self.R = 0.01, 1
        self.P, self.x = 1, 0

    def filter(self, z):
        self.x = self.A * self.x
        self.P = self.A * self.P * self.A + self.Q
        K = self.P * self.H / (self.H * self.P * self.H + self.R)
        self.x += K * (z - self.H * self.x)
        self.P = (1 - K * self.H) * self.P
        return self.x

kalman_x, kalman_y = Kalman(), Kalman()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("gaze_events.log", mode='w'), logging.StreamHandler()]
)

async def ws_handler(ws):
    logging.info("🌐 WebSocket connected")
    try:
        async for message in ws:
            try:
                data = json.loads(message)
                if "x" in data and "y" in data:
                    x_s = kalman_x.filter(data["x"])
                    y_s = kalman_y.filter(data["y"])
                    logging.info(f"👁 Smoothed Gaze — x: {x_s:.1f}, y: {y_s:.1f}")
                elif "msg" in data:
                    logging.info(f"🔔 Event: {data['msg']}")
                else:
                    logging.warning(f"⚠ Unknown message: {data}")
            except json.JSONDecodeError:
                logging.error("❌ Malformed JSON received")
    except websockets.exceptions.ConnectionClosed:
        logging.warning("🔌 WebSocket connection closed")

async def main():
    logging.info("🚀 Starting logger on ws://localhost:9999")
    async with websockets.serve(ws_handler, "localhost", 9999):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Logger terminated by user")
