#!/usr/bin/env python3
# eye_tracker_connector.py - Connect actual eye tracker to WebSocket server
# This script connects to your eye tracking hardware and sends data to the WebSocket server

import asyncio
import websockets
import json
import signal
import sys
import time
import random
from datetime import datetime

# === CONFIG ===
WS_URL = "ws://localhost:8765"
SAMPLE_RATE = 60  # Hz (frames per second)
FRAME_TIME = 1.0 / SAMPLE_RATE
running = True

# === UTIL ===
def log(msg):
    print(f"[{datetime.now().isoformat()}] {msg}")

# === SIGNAL HANDLERS ===
def handle_shutdown(sig=None, frame=None):
    """Handle shutdown signals gracefully"""
    global running
    log("🛑 Shutdown initiated")
    running = False
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_shutdown)  # Termination signal

# === EYE TRACKER INTERFACE ===
class EyeTracker:
    """Interface to the eye tracking hardware"""
    
    def __init__(self):
        self.connected = False
        self.screen_width = 1920  # Default screen width
        self.screen_height = 1080  # Default screen height
        self.last_blink_time = 0
        self.blink_cooldown = 1.0  # Minimum time between blinks (seconds)
        
        # Try to get actual screen dimensions
        try:
            import tkinter as tk
            root = tk.Tk()
            self.screen_width = root.winfo_screenwidth()
            self.screen_height = root.winfo_screenheight()
            root.destroy()
        except:
            pass
    
    def connect(self):
        """Connect to the eye tracker hardware"""
        # In a real implementation, this would connect to your actual eye tracker
        # For this test, we'll simulate a connection
        log("🔌 Connecting to eye tracker...")
        time.sleep(1)  # Simulate connection time
        self.connected = True
        log("✅ Connected to eye tracker")
        return self.connected
    
    def disconnect(self):
        """Disconnect from the eye tracker hardware"""
        if self.connected:
            log("🔌 Disconnecting from eye tracker...")
            # In a real implementation, this would disconnect from your actual eye tracker
            self.connected = False
            log("✅ Disconnected from eye tracker")
    
    def get_gaze_data(self):
        """Get current gaze data from the eye tracker"""
        if not self.connected:
            return None
        
        # In a real implementation, this would get actual data from your eye tracker
        # For this test, we'll simulate gaze data
        
        # Simulate natural eye movement with some randomness
        now = time.time()
        
        # Base position (center of screen with some drift)
        center_x = self.screen_width / 2
        center_y = self.screen_height / 2
        
        # Add some random movement
        drift_x = random.gauss(0, 50)  # Standard deviation of 50 pixels
        drift_y = random.gauss(0, 30)  # Standard deviation of 30 pixels
        
        # Calculate final position
        x = max(0, min(self.screen_width, center_x + drift_x))
        y = max(0, min(self.screen_height, center_y + drift_y))
        
        # Determine if blinking
        blink = False
        if now - self.last_blink_time > self.blink_cooldown:
            # Random chance of blinking (about once every 5 seconds)
            if random.random() < 0.01:  # 1% chance per frame at 60fps = ~once per 1.7 seconds
                blink = True
                self.last_blink_time = now
        
        # Return gaze data
        return {
            "x": x,
            "y": y,
            "blink": blink,
            "confidence": random.uniform(0.8, 1.0)  # Simulate confidence level
        }

# === WEBSOCKET CLIENT ===
async def connect_websocket():
    """Connect to the WebSocket server and send gaze data"""
    global running
    
    # Create eye tracker
    eye_tracker = EyeTracker()
    
    # Connect to eye tracker
    if not eye_tracker.connect():
        log("❌ Failed to connect to eye tracker")
        return
    
    try:
        # Connect to WebSocket server
        log(f"🔌 Connecting to WebSocket server at {WS_URL}")
        async with websockets.connect(WS_URL) as websocket:
            log("✅ Connected to WebSocket server")
            
            # Main loop
            while running:
                # Get gaze data
                gaze_data = eye_tracker.get_gaze_data()
                
                if gaze_data:
                    # Send gaze data
                    await websocket.send(json.dumps(gaze_data))
                    
                    # Log blinks
                    if gaze_data["blink"]:
                        log(f"👁️ Blink detected")
                
                # Wait for next frame
                await asyncio.sleep(FRAME_TIME)
    
    except websockets.ConnectionClosed:
        log("🔌 WebSocket connection closed")
    except Exception as e:
        log(f"❌ Error: {e}")
    finally:
        # Disconnect from eye tracker
        eye_tracker.disconnect()

# === MAIN ===
if __name__ == "__main__":
    log("🚀 Starting Eye Tracker Connector")
    
    try:
        # Run the WebSocket client
        asyncio.run(connect_websocket())
    except KeyboardInterrupt:
        handle_shutdown()
    except Exception as e:
        log(f"❌ Error: {e}")
        sys.exit(1)
