# PRF-SUPAGROK-NET-LISTENER
# Accepts incoming logs via socket and timestamps each received chunk

import os
import socket
import datetime

HOST = "0.0.0.0"
PORT = 5140
OUTPUT_DIR = "/home/user/ddwrt_logs"

os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"📡 Listening on {HOST}:{PORT}...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    while True:
        conn, addr = s.accept()
        with conn:
            print(f"📥 Connection from {addr}")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(OUTPUT_DIR, f"log_{timestamp}.txt")
            with open(filename, "wb") as f:
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break
                    f.write(data)
            print(f"✅ Log saved to {filename}")
