#!/usr/bin/env python3
# mouse_override.py — PRF‑MOUSE‑GAZE‑2025‑05‑01

import asyncio, json, pyautogui, websockets
from pynput.mouse import Controller

class Kalman:
    def __init__(self): self.A, self.H, self.Q, self.R, self.P, self.x = 1, 1, 0.01, 1, 1, 0
    def filter(self, z):
        self.x = self.A * self.x
        self.P = self.A * self.P * self.A + self.Q
        K = self.P * self.H / (self.H * self.P * self.H + self.R)
        self.x = self.x + K * (z - self.H * self.x)
        self.P = (1 - K * self.H) * self.P
        return self.x

mouse = Controller()
kalman_x, kalman_y = Kalman(), Kalman()
screen_width, screen_height = pyautogui.size()

async def handler(ws):
    print("🖱 Gaze-to-Mouse active")
    async for msg in ws:
        try:
            data = json.loads(msg)
            if "x" in data and "y" in data:
                x = kalman_x.filter(data["x"])
                y = kalman_y.filter(data["y"])
                mouse.position = (int(x), int(y))
        except: pass

async def main():
    async with websockets.serve(handler, "localhost", 9998):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
