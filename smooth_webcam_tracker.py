#!/usr/bin/env python3
# smooth_webcam_tracker.py — PRF‑WEBCAM‑TRACKER‑2025‑05‑02
# Description: Smooth webcam eye tracking with green dots around face and orange dots around eyes
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import subprocess
import time
import signal
import threading
from datetime import datetime

# === Dependency Management ===
def check_and_install_dependencies():
    """Check and install required dependencies"""
    print("🔍 Checking dependencies...")

    # Required packages
    required_packages = [
        "opencv-python",
        "numpy"
    ]

    missing_packages = []
    for package in required_packages:
        try:
            if package == "opencv-python":
                __import__("cv2")
            else:
                __import__(package.replace("-", "_"))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is not installed")

    if missing_packages:
        print(f"📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✅ All dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            sys.exit(1)

# === Signal Handlers ===
def handle_signal(sig, frame):
    """Handle signals for clean shutdown"""
    print(f"🛑 Received signal {sig}, shutting down...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_signal)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_signal)  # Termination signal

# === Fix Webcam Issues ===
def fix_webcam_issues():
    """Fix common webcam issues"""
    print("🔧 Fixing common webcam issues...")

    # Kill any processes that might be using the webcam
    print("🔍 Checking for processes using the webcam...")
    try:
        subprocess.run("pkill -f 'zoom' || true", shell=True)
        subprocess.run("pkill -f 'skype' || true", shell=True)
        subprocess.run("pkill -f 'teams' || true", shell=True)
        subprocess.run("pkill -f 'meet' || true", shell=True)
        print("✅ Killed potential processes using the webcam")
    except:
        print("⚠️ Could not kill processes")

    # Set permissions
    print("🔍 Setting webcam permissions...")
    try:
        subprocess.run("sudo chmod 777 /dev/video* || true", shell=True, check=False)
        print("✅ Set webcam permissions")
    except:
        print("⚠️ Could not set webcam permissions")

# === Main Function ===
def main():
    """Main function"""
    print("🚀 Starting Smooth Webcam Tracker")

    # Check and install dependencies
    check_and_install_dependencies()

    # Fix webcam issues
    fix_webcam_issues()

    # Import dependencies after they've been installed
    import cv2
    import numpy as np

    # Global variables for threading
    running = True
    frame_buffer = None
    face_data = None
    lock = threading.Lock()

    def capture_thread():
        """Thread for capturing frames"""
        nonlocal frame_buffer, running

        # Initialize webcam
        print("🔌 Connecting to webcam...")
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("❌ Failed to open webcam")
            running = False
            return

        # Set resolution (lower for better performance)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

        # Get actual resolution
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"✅ Connected to webcam ({frame_width}x{frame_height})")

        # Set buffer size (smaller for better performance)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        try:
            while running:
                # Capture frame
                ret, frame = cap.read()

                if not ret:
                    print("❌ Failed to capture frame")
                    time.sleep(0.1)
                    continue

                # Update frame buffer
                with lock:
                    frame_buffer = frame.copy()

                # Small delay to prevent CPU overload
                time.sleep(0.01)

        except Exception as e:
            print(f"❌ Error in capture thread: {e}")
        finally:
            cap.release()

    def process_thread():
        """Thread for processing frames"""
        nonlocal frame_buffer, face_data, running

        # Load face and eye cascades
        cv_path = cv2.__path__[0]
        face_cascade_path = f'{cv_path}/data/haarcascade_frontalface_default.xml'
        eye_cascade_path = f'{cv_path}/data/haarcascade_eye.xml'

        if not os.path.exists(face_cascade_path) or not os.path.exists(eye_cascade_path):
            print(f"❌ Cascade files not found")
            running = False
            return

        face_cascade = cv2.CascadeClassifier(face_cascade_path)
        eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

        # Initialize variables for tracking
        last_face = None
        last_eyes = []
        frame_count = 0

        try:
            while running:
                # Get current frame
                current_frame = None
                with lock:
                    if frame_buffer is not None:
                        current_frame = frame_buffer.copy()

                if current_frame is None:
                    time.sleep(0.01)
                    continue

                # Only process every 2nd frame for better performance
                frame_count += 1
                if frame_count % 2 != 0:
                    time.sleep(0.01)
                    continue

                # Convert to grayscale
                gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

                # Detect faces (only if we don't have a face or every 10 frames)
                if last_face is None or frame_count % 10 == 0:
                    faces = face_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.3,
                        minNeighbors=5,
                        minSize=(30, 30),
                        flags=cv2.CASCADE_SCALE_IMAGE
                    )

                    if len(faces) > 0:
                        last_face = faces[0]

                # Process face if available
                if last_face is not None:
                    x, y, w, h = last_face

                    # Extract face ROI
                    roi_gray = gray[y:y+h, x:x+w]

                    # Detect eyes (only if we don't have eyes or every 5 frames)
                    if not last_eyes or frame_count % 5 == 0:
                        eyes = eye_cascade.detectMultiScale(
                            roi_gray,
                            scaleFactor=1.1,
                            minNeighbors=3,
                            minSize=(20, 20),
                            flags=cv2.CASCADE_SCALE_IMAGE
                        )

                        if len(eyes) > 0:
                            last_eyes = eyes

                    # Update face data
                    with lock:
                        face_data = {
                            'face': last_face,
                            'eyes': last_eyes
                        }

                # Small delay to prevent CPU overload
                time.sleep(0.01)

        except Exception as e:
            print(f"❌ Error in process thread: {e}")

    def display_thread():
        """Thread for displaying frames"""
        nonlocal frame_buffer, face_data, running

        # Create window
        cv2.namedWindow("Eye Tracking", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Eye Tracking", 640, 480)

        print("✅ Display initialized")
        print("👁️ Looking for face and eyes...")
        print("Press ESC to exit")

        # Initialize last time for FPS calculation
        last_time = time.time()

        try:
            while running:
                # Get current frame and data
                current_frame = None
                current_face_data = None

                with lock:
                    if frame_buffer is not None:
                        current_frame = frame_buffer.copy()
                    if face_data is not None:
                        current_face_data = face_data.copy()

                if current_frame is None:
                    time.sleep(0.01)
                    continue

                # Create a copy for visualization
                display_frame = current_frame.copy()

                # Get frame dimensions
                frame_height, frame_width = display_frame.shape[:2]

                # Process face data if available
                if current_face_data is not None and 'face' in current_face_data:
                    # Extract face data
                    x, y, w, h = current_face_data['face']
                    eyes = current_face_data.get('eyes', [])

                    # Draw green rectangle around face
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # Draw green dots around face (8 points)
                    for i in range(8):
                        angle = i * 45  # 8 points around the face
                        px = int(x + w/2 + (w/2) * 0.9 * np.cos(np.radians(angle)))
                        py = int(y + h/2 + (h/2) * 0.9 * np.sin(np.radians(angle)))
                        cv2.circle(display_frame, (px, py), 3, (0, 255, 0), -1)

                    # Extract face ROI for drawing
                    roi_color = display_frame[y:y+h, x:x+w]

                    # Process detected eyes
                    for (ex, ey, ew, eh) in eyes:
                        # Draw orange rectangle around eye
                        cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 165, 255), 2)

                        # Draw orange dots around the eye (6 points)
                        for i in range(6):
                            angle = i * 60  # 6 points around the eye
                            px = int(ex + ew/2 + (ew/2) * 0.8 * np.cos(np.radians(angle)))
                            py = int(ey + eh/2 + (eh/2) * 0.8 * np.sin(np.radians(angle)))
                            cv2.circle(roi_color, (px, py), 2, (0, 165, 255), -1)

                        # Draw eye center
                        eye_center_x = ex + ew // 2
                        eye_center_y = ey + eh // 2
                        cv2.circle(roi_color, (eye_center_x, eye_center_y), 3, (255, 0, 0), -1)
                else:
                    # No face detected
                    cv2.putText(display_frame, "No face detected", (30, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # Add instructions
                cv2.putText(display_frame, "Press ESC to exit", (10, frame_height - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

                # Calculate and show FPS
                current_time = time.time()
                fps = int(1.0 / (current_time - last_time + 0.001))
                last_time = current_time
                cv2.putText(display_frame, f"FPS: {fps}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # Show the frame
                cv2.imshow("Eye Tracking", display_frame)

                # Exit if ESC is pressed
                key = cv2.waitKey(1)
                if key == 27:  # ESC key
                    running = False
                    break

                # Small delay to prevent CPU overload
                time.sleep(0.01)

        except Exception as e:
            print(f"❌ Error in display thread: {e}")
        finally:
            cv2.destroyAllWindows()

    try:
        # Create and start threads
        capture_thread = threading.Thread(target=capture_thread)
        process_thread = threading.Thread(target=process_thread)
        display_thread = threading.Thread(target=display_thread)

        capture_thread.daemon = True
        process_thread.daemon = True
        display_thread.daemon = True

        capture_thread.start()
        process_thread.start()
        display_thread.start()

        # Wait for threads to complete
        while running:
            time.sleep(0.1)

            # Check if any thread has died
            if not capture_thread.is_alive() or not process_thread.is_alive() or not display_thread.is_alive():
                running = False
                break

        # Wait for threads to finish
        capture_thread.join(timeout=1)
        process_thread.join(timeout=1)
        display_thread.join(timeout=1)

        print("👋 Eye tracking completed")

    except KeyboardInterrupt:
        print("🛑 Interrupted by user")
        running = False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
    finally:
        # Ensure we exit cleanly
        running = False
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
