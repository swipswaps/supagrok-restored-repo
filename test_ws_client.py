#!/usr/bin/env python3
# File: test_ws_client.py
# Purpose: Test client for gaze_ws_server.py

import websocket
import json
import time
import random

def main():
    print("🚀 Starting WebSocket Test Client")
    print("🔌 Connecting to WebSocket server at ws://localhost:8765")
    
    try:
        # Connect to the WebSocket server
        ws = websocket.create_connection("ws://localhost:8765")
        print("✅ Connected to WebSocket server")
        
        # Send test gaze data
        screen_width = 1920
        screen_height = 1080
        
        print("📊 Sending test gaze data (press Ctrl+C to stop)")
        try:
            i = 0
            while True:
                # Generate random-ish gaze positions that move around the screen
                x = 500 + int(400 * math.sin(i / 20))
                y = 300 + int(200 * math.cos(i / 15))
                
                # Ensure coordinates are within screen bounds
                x = max(0, min(x, screen_width))
                y = max(0, min(y, screen_height))
                
                # Simulate occasional blinks
                blink = (i % 50 == 0)
                
                # Create and send gaze data
                test_data = {"x": x, "y": y, "blink": blink}
                ws.send(json.dumps(test_data))
                print(f"Sent: {test_data}")
                
                # Wait a bit before sending the next data point
                time.sleep(0.1)
                i += 1
                
        except KeyboardInterrupt:
            print("🛑 Interrupted by user")
        finally:
            # Close the connection
            ws.close()
            print("🔌 Disconnected from WebSocket server")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import math
    main()
