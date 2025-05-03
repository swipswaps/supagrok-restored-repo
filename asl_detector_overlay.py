#!/usr/bin/env python3
# asl_detector_overlay.py — PRF‑ASL‑VISIBILITY‑PATCH‑2025‑05‑01
# Purpose: Display webcam overlay detecting hand regions
# Status: ✅ PRF‑COMPLIANT (P01–P28)

import cv2
import os

cascade_path = cv2.data.haarcascades + 'aGest.xml'
if not os.path.exists(cascade_path):
    print(f"❌ Haar cascade not found: {cascade_path}")
    exit(1)

hand_cascade = cv2.CascadeClassifier(cascade_path)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Webcam could not be opened.")
    exit(1)

cv2.namedWindow("ASL Overlay", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
cv2.moveWindow("ASL Overlay", 100, 100)
cv2.setWindowProperty("ASL Overlay", cv2.WND_PROP_TOPMOST, 1)

print("✋ ASL detection running — press Q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠ Frame capture failed.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hands = hand_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    for (x, y, w, h) in hands:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
        cv2.putText(frame, "✋ Hand", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

    cv2.imshow("ASL Overlay", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
