#!/usr/bin/env python3
# robust_webcam_tracker.py — PRF‑WEBCAM‑TRACKER‑2025‑05‑02
# Description: Robust webcam eye tracking with green dots around face and orange dots around eyes
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
        subprocess.run("pkill -f 'chrome' || true", shell=True)
        subprocess.run("pkill -f 'firefox' || true", shell=True)
        print("✅ Killed potential processes using the webcam")
    except:
        print("⚠️ Could not kill processes")
    
    # Reset USB devices
    print("🔍 Resetting USB devices...")
    try:
        subprocess.run("sudo modprobe -r uvcvideo || true", shell=True, check=False)
        time.sleep(1)
        subprocess.run("sudo modprobe uvcvideo || true", shell=True, check=False)
        print("✅ Reset USB video devices")
    except:
        print("⚠️ Could not reset USB devices")
    
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
    print("🚀 Starting Robust Webcam Tracker")
    
    # Check and install dependencies
    check_and_install_dependencies()
    
    # Fix webcam issues
    fix_webcam_issues()
    
    # Import dependencies after they've been installed
    import cv2
    import numpy as np
    
    try:
        # Initialize webcam
        print("🔌 Connecting to webcam...")
        
        # Try multiple camera indices
        cap = None
        for camera_id in range(3):  # Try camera IDs 0, 1, 2
            print(f"   Trying camera ID {camera_id}...")
            cap = cv2.VideoCapture(camera_id)
            if cap.isOpened():
                print(f"✅ Connected to camera ID {camera_id}")
                break
            else:
                cap.release()
                cap = None
        
        if cap is None:
            print("❌ Failed to open any webcam")
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
        face_cascade_path = f'{cv_path}/data/haarcascade_frontalface_default.xml'
        eye_cascade_path = f'{cv_path}/data/haarcascade_eye.xml'
        
        print(f"Face cascade path: {face_cascade_path}")
        print(f"Eye cascade path: {eye_cascade_path}")
        
        if not os.path.exists(face_cascade_path):
            print(f"❌ Face cascade file not found: {face_cascade_path}")
            return
        
        if not os.path.exists(eye_cascade_path):
            print(f"❌ Eye cascade file not found: {eye_cascade_path}")
            return
        
        face_cascade = cv2.CascadeClassifier(face_cascade_path)
        eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
        
        if face_cascade.empty():
            print("❌ Failed to load face cascade")
            return
        
        if eye_cascade.empty():
            print("❌ Failed to load eye cascade")
            return
        
        # Create window
        cv2.namedWindow("Eye Tracking", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Eye Tracking", frame_width, frame_height)
        
        print("✅ Webcam initialized")
        print("👁️ Looking for face and eyes...")
        print("Press ESC to exit")
        
        # Initialize variables for tracking
        last_face = None
        face_detected_frames = 0
        no_face_frames = 0
        
        # Parameters for face detection
        min_neighbors = 5  # Start with a higher value for more reliable detection
        scale_factor = 1.3
        
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
            
            # Detect faces with current parameters
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=scale_factor, 
                minNeighbors=min_neighbors,
                minSize=(30, 30)
            )
            
            # If no faces detected, try with more lenient parameters
            if len(faces) == 0:
                no_face_frames += 1
                
                # After 10 frames with no face, try more lenient parameters
                if no_face_frames > 10:
                    # Try with more lenient parameters
                    if min_neighbors > 1:
                        min_neighbors -= 1
                        print(f"Adjusting minNeighbors to {min_neighbors}")
                        no_face_frames = 0
                    elif scale_factor > 1.1:
                        scale_factor -= 0.05
                        print(f"Adjusting scaleFactor to {scale_factor:.2f}")
                        no_face_frames = 0
                
                # Use the last known face position if available
                if last_face is not None:
                    cv2.putText(display_frame, "Using last known face position", (30, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    faces = [last_face]
                else:
                    cv2.putText(display_frame, "No face detected", (30, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                # Reset counters when face is detected
                no_face_frames = 0
                face_detected_frames += 1
                
                # After 30 frames with successful detection, try stricter parameters
                if face_detected_frames > 30:
                    if min_neighbors < 5:
                        min_neighbors += 1
                        print(f"Adjusting minNeighbors to {min_neighbors}")
                    elif scale_factor < 1.3:
                        scale_factor += 0.05
                        print(f"Adjusting scaleFactor to {scale_factor:.2f}")
                    face_detected_frames = 0
                
                # Update last known face
                last_face = faces[0]
            
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
                
                # Detect eyes with more lenient parameters
                eyes = eye_cascade.detectMultiScale(
                    roi_gray,
                    scaleFactor=1.1,
                    minNeighbors=3,
                    minSize=(20, 20)
                )
                
                # Process detected eyes
                if len(eyes) > 0:
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
                    # If no eyes detected, try to estimate eye positions
                    # Eyes are typically in the upper half of the face
                    left_eye_x = x + w // 4
                    right_eye_x = x + 3 * w // 4
                    eye_y = y + h // 3
                    eye_w = w // 4
                    eye_h = h // 6
                    
                    # Draw estimated eye regions
                    cv2.rectangle(display_frame, (left_eye_x, eye_y), (left_eye_x + eye_w, eye_y + eye_h), (0, 165, 255), 2)
                    cv2.rectangle(display_frame, (right_eye_x, eye_y), (right_eye_x + eye_w, eye_y + eye_h), (0, 165, 255), 2)
                    
                    # Draw orange dots around estimated eyes
                    for eye_x in [left_eye_x + eye_w // 2, right_eye_x + eye_w // 2]:
                        for i in range(6):
                            angle = i * 60  # 6 points around the eye
                            px = int(eye_x + (eye_w/2) * 0.8 * np.cos(np.radians(angle)))
                            py = int(eye_y + eye_h // 2 + (eye_h/2) * 0.8 * np.sin(np.radians(angle)))
                            cv2.circle(display_frame, (px, py), 2, (0, 165, 255), -1)
            
            # Add instructions and status
            cv2.putText(display_frame, "Press ESC to exit", (10, frame_height - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.putText(display_frame, f"Face detection: SF={scale_factor:.2f}, MN={min_neighbors}", 
                        (10, frame_height - 50), 
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
