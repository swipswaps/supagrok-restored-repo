#!/usr/bin/env python3
# gaze_ws_server.py — PRF‑COMPOSITE‑2025‑04‑30‑Z1 (CPU-Optimized Gaze WebSocket Server)
# Description: Efficient, event-driven gaze bridge (no busy-wait)
# UUID: 6810e201-4d88-8008-b97b-e72dfdca3250
# Timestamp: 2025-04-30T20:57:36
# PRF-P01–P25 enforced
# PRF-CODEX: c7f7ef75ec408660344407c87f373a0c0444794aff7428037c4805dd0a996f9c

import asyncio
import websockets
import json
import signal
import sys
import os
from collections import deque
from datetime import datetime

# === CONFIG ===
PORT = 8765
BUFFER_MAX = 500
gaze_buffer = deque(maxlen=BUFFER_MAX)
connected_clients = set()
server = None

# === UTIL ===
def log_event(msg, level="INFO"):
    print(f"[{datetime.now().isoformat()}] [{level}] {msg}")

# === WEBSOCKET HANDLER ===
async def handler(websocket, path):
    # Add client to connected set
    connected_clients.add(websocket)
    client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    log_event(f"🔌 WebSocket connected from {client_info}")

    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "server_info",
            "message": "Connected to Gaze WebSocket Server",
            "timestamp": datetime.now().timestamp()
        }))

        # Process incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)

                # Add timestamp and client info
                data["timestamp"] = datetime.now().timestamp()
                data["client"] = client_info

                # Store in buffer
                gaze_buffer.append(data)

                # Broadcast to all other clients
                await broadcast_gaze(data, websocket)

                # Log (only if debug logging is enabled)
                if os.environ.get("GAZE_DEBUG") == "1":
                    log_event(f"📥 Gaze received: {data}", "DEBUG")

            except json.JSONDecodeError:
                log_event("❌ Invalid JSON received", "ERROR")
    except websockets.ConnectionClosed:
        log_event(f"🔌 WebSocket disconnected from {client_info}")
    except Exception as e:
        log_event(f"❌ WS Handler Error: {e}", "ERROR")
    finally:
        # Remove client from connected set
        connected_clients.remove(websocket)

# === BROADCAST FUNCTION ===
async def broadcast_gaze(data, sender=None):
    """Broadcast gaze data to all connected clients except sender"""
    if not connected_clients:
        return

    # Create message to broadcast
    message = json.dumps(data)

    # Send to all clients except the sender
    for client in connected_clients:
        if client != sender:  # Don't send back to sender
            try:
                await client.send(message)
            except websockets.ConnectionClosed:
                # Client disconnected, will be removed in handler
                pass
            except Exception as e:
                log_event(f"❌ Broadcast Error: {e}", "ERROR")

# === EXTERNAL ACCESSOR ===
def get_next_gaze():
    return gaze_buffer.popleft() if gaze_buffer else None

# === SIGNAL HANDLERS ===
def handle_shutdown(sig=None, frame=None):
    """Handle shutdown signals gracefully"""
    log_event("🛑 Server shutdown initiated", "WARN")

    # Close the server
    if server:
        server.close()

    # Exit
    sys.exit(0)

# === SERVER START ===
async def main():
    global server

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)   # Ctrl+C
    signal.signal(signal.SIGTERM, handle_shutdown)  # Termination signal

    # Start server
    log_event(f"🌐 Starting WebSocket server on ws://localhost:{PORT}")
    server = await websockets.serve(handler, "localhost", PORT)

    log_event(f"✅ Server started successfully")
    log_event(f"👁️ Ready to receive eye tracking data")

    # Run forever
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        handle_shutdown()
    except Exception as e:
        log_event(f"❌ Server Error: {e}", "ERROR")
        sys.exit(1)
