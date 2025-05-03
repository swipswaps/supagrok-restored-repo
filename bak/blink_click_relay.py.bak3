#!/usr/bin/env python3
# ✅ PRF‑EXPORT‑2025‑04‑29‑BLINK‑GAZE‑CURSOR
# 📂 Path: ./supagrok_restored_repo/blink_click_relay.py
# 📜 Directive: PRF‑REPAIR‑2025‑04‑29‑ADD‑VISUAL‑CUES‑AND‑MOUSE‑TRACK

import os, shutil, subprocess, sys, time

def run(cmd):
    print(f"▶ {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def ensure_requirements():
    if not shutil.which("xdotool"):
        if shutil.which("apt"):
            run("sudo apt update && sudo apt install -y xdotool")
        elif shutil.which("dnf"):
            run("sudo dnf install -y xdotool")
        elif shutil.which("pacman"):
            run("sudo pacman -Sy xdotool")
        else:
            print("❌ Cannot auto-install xdotool")
            sys.exit(1)

    try:
        import cv2, dlib, scipy, pyautogui
    except ImportError:
        run("pip install opencv-python dlib scipy pyautogui")

    model_path = "/usr/share/dlib/shape_predictor_68_face_landmarks.dat"
    if not os.path.exists(model_path):
        run("sudo mkdir -p /usr/share/dlib")
        run("wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
        run("bzip2 -d shape_predictor_68_face_landmarks.dat.bz2")
        run(f"sudo mv shape_predictor_68_face_landmarks.dat {model_path}")
    return model_path

# ✔ Auto-dependency setup
model_path = ensure_requirements()

# ✔ Runtime imports after install
import cv2
import dlib
import pyautogui
from scipy.spatial import distance

def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

LEFT_EYE = list(range(36, 42))
RIGHT_EYE = list(range(42, 48))
BLINK_THRESHOLD = 0.21
BLINK_MIN_FRAMES = 3
cooldown_time = 1.5

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(model_path)

cap = cv2.VideoCapture(0)
blink_frames = 0
last_blink = time.time()

print("🧠 Blink relay + gaze display active")

while True:
    ret, frame = cap.read()
    if not ret: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:
        shape = predictor(gray, face)
        shape = [(shape.part(i).x, shape.part(i).y) for i in range(68)]

        left = [shape[i] for i in LEFT_EYE]
        right = [shape[i] for i in RIGHT_EYE]
        ear = (eye_aspect_ratio(left) + eye_aspect_ratio(right)) / 2.0

        # Draw eye contours
        for (x, y) in left + right:
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

        # Estimate eye center (basic average)
        eye_center_x = int(sum(p[0] for p in left + right) / len(left + right))
        eye_center_y = int(sum(p[1] for p in left + right) / len(left + right))
        cv2.circle(frame, (eye_center_x, eye_center_y), 6, (255, 0, 0), 2)
        cv2.putText(frame, f"Gaze", (eye_center_x + 10, eye_center_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

        # Move mouse toward gaze center (scaled)
        screen_w, screen_h = pyautogui.size()
        scale_x = screen_w / frame.shape[1]
        scale_y = screen_h / frame.shape[0]
        mouse_x = int(eye_center_x * scale_x)
        mouse_y = int(eye_center_y * scale_y)
        pyautogui.moveTo(mouse_x, mouse_y, duration=0.1)

        if ear < BLINK_THRESHOLD:
            blink_frames += 1
        else:
            if blink_frames >= BLINK_MIN_FRAMES:
                now = time.time()
                if now - last_blink > cooldown_time:
                    print("🖱 Blink click triggered!")
                    subprocess.run("xdotool click 1", shell=True)
                    last_blink = now
            blink_frames = 0

    cv2.imshow("Supagrok Eye Tracking", frame)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()
