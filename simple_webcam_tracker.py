#!/usr/bin/env python3
# simple_webcam_tracker.py — PRF‑WEBCAM‑TRACKER‑2025‑05‑02
# Description: Simple webcam eye tracking with green dots around face and orange dots around eyes
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import subprocess
import time
import signal
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

# === Main Function ===
def main():
    """Main function"""
    print("🚀 Starting Simple Webcam Tracker")
    
    # Check and install dependencies
    check_and_install_dependencies()
    
    # Import dependencies after they've been installed
    import cv2
    import numpy as np
    
    try:
        # Initialize webcam
        print("🔌 Connecting to webcam...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Failed to open webcam")
            print("   Possible causes:")
            print("   - Webcam is not connected")
            print("   - Webcam is being used by another application")
            print("   - Insufficient permissions")
            return
        
        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Get actual resolution
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"✅ Connected to webcam ({frame_width}x{frame_height})")
        
        # Load face and eye cascades
        cv_path = cv2.__path__[0]
        face_cascade = cv2.CascadeClassifier(f'{cv_path}/data/haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(f'{cv_path}/data/haarcascade_eye.xml')
        
        if face_cascade.empty() or eye_cascade.empty():
            print("❌ Failed to load cascade classifiers")
            print("   Possible causes:")
            print("   - OpenCV installation is incomplete")
            print("   - Cascade files are missing")
            return
        
        # Create window
        cv2.namedWindow("Eye Tracking", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Eye Tracking", frame_width, frame_height)
        
        print("✅ Webcam initialized")
        print("👁️ Looking for face and eyes...")
        print("Press ESC to exit")
        
        while True:
            # Capture frame
            ret, frame = cap.read()
            
            if not ret:
                print("❌ Failed to capture frame")
                break
            
            # Create a copy for visualization
            display_frame = frame.copy()
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # If no faces detected
            if len(faces) == 0:
                cv2.putText(display_frame, "No face detected", (30, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Process detected faces
            for (x, y, w, h) in faces:
                # Draw green rectangle around face
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(display_frame, "Face", (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Draw green dots around face (8 points)
                for i in range(8):
                    angle = i * 45  # 8 points around the face
                    px = int(x + w/2 + (w/2) * 0.9 * np.cos(np.radians(angle)))
                    py = int(y + h/2 + (h/2) * 0.9 * np.sin(np.radians(angle)))
                    cv2.circle(display_frame, (px, py), 3, (0, 255, 0), -1)
                
                # Extract face ROI
                roi_gray = gray[y:y+h, x:x+w]
                roi_color = display_frame[y:y+h, x:x+w]
                
                # Detect eyes
                eyes = eye_cascade.detectMultiScale(roi_gray)
                
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
            
            # Add instructions
            cv2.putText(display_frame, "Press ESC to exit", (10, frame_height - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Show the frame
            cv2.imshow("Eye Tracking", display_frame)
            
            # Exit if ESC is pressed
            if cv2.waitKey(1) == 27:
                break
        
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        print("👋 Eye tracking completed")
    
    except KeyboardInterrupt:
        print("🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
    finally:
        # Clean up
        try:
            cap.release()
            cv2.destroyAllWindows()
        except:
            pass

if __name__ == "__main__":
    main()
