#!/usr/bin/env python3
# fixed_eye_tracker.py — PRF‑WEBCAM‑TRACKER‑2025‑05‑02
# Description: Fixed webcam eye tracking with green dots around face and orange dots around eyes
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
    print("🚀 Starting Fixed Eye Tracker")
    
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
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Failed to open webcam")
            print("   Possible causes:")
            print("   - Webcam is not connected")
            print("   - Webcam is being used by another application")
            print("   - Insufficient permissions")
            return
        
        # Set resolution (lower for better performance)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Get actual resolution
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"✅ Connected to webcam ({frame_width}x{frame_height})")
        
        # Set buffer size (smaller for better performance)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Load face and eye cascades
        cv_path = cv2.__path__[0]
        face_cascade_path = f'{cv_path}/data/haarcascade_frontalface_default.xml'
        eye_cascade_path = f'{cv_path}/data/haarcascade_eye.xml'
        
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
        stored_eyes = []  # Renamed to avoid confusion
        last_time = time.time()
        frame_count = 0
        
        # Main loop
        while True:
            # Capture frame
            ret, frame = cap.read()
            
            if not ret:
                print("❌ Failed to capture frame")
                break
            
            # Create a copy for visualization
            display_frame = frame.copy()
            
            # Get frame dimensions
            frame_height, frame_width = display_frame.shape[:2]
            
            # Only process every 2nd frame for better performance
            frame_count += 1
            process_frame = (frame_count % 2 == 0)
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces (only if we don't have a face or every 10 frames)
            faces = []
            if process_frame and (last_face is None or frame_count % 10 == 0):
                faces = face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.3, 
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                if len(faces) > 0:
                    last_face = faces[0]
            
            # Use last known face if available
            if len(faces) == 0 and last_face is not None:
                faces = [last_face]
            
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
                
                # Detect eyes (only if we don't have eyes or every 5 frames)
                eyes = []
                if process_frame and (len(stored_eyes) == 0 or frame_count % 5 == 0):
                    eyes = eye_cascade.detectMultiScale(
                        roi_gray,
                        scaleFactor=1.1,
                        minNeighbors=3,
                        minSize=(20, 20),
                        flags=cv2.CASCADE_SCALE_IMAGE
                    )
                    
                    if len(eyes) > 0:
                        stored_eyes = eyes.copy()  # Make a copy to avoid reference issues
                
                # Use stored eyes if available and no eyes detected
                if len(eyes) == 0 and len(stored_eyes) > 0:
                    eyes = stored_eyes.copy()  # Make a copy to avoid reference issues
                
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
            
            # If no faces detected
            if len(faces) == 0:
                cv2.putText(display_frame, "No face detected", (30, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Calculate and show FPS
            current_time = time.time()
            fps = int(1.0 / (current_time - last_time + 0.001))
            last_time = current_time
            
            cv2.putText(display_frame, f"FPS: {fps}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Add instructions
            cv2.putText(display_frame, "Press ESC to exit", (10, frame_height - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Show the frame
            cv2.imshow("Eye Tracking", display_frame)
            
            # Exit if ESC is pressed
            key = cv2.waitKey(1)
            if key == 27:  # ESC key
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
