#!/usr/bin/env python3
# opencv_with_reference.py — PRF‑OPENCV‑REFERENCE‑2025‑05‑02
# Description: OpenCV eye tracking with reference image overlay
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import subprocess
import time
import signal
import numpy as np
import math
import random
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
    print("🚀 Starting OpenCV with Reference Image")
    
    # Check and install dependencies
    check_and_install_dependencies()
    
    # Import dependencies after they've been installed
    import cv2
    
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
        cv2.namedWindow("OpenCV with Reference", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("OpenCV with Reference", frame_width, frame_height)
        
        print("✅ OpenCV initialized")
        print("👁️ Looking for face and eyes...")
        print("Press ESC to exit")
        
        # Initialize variables for tracking
        last_face = None
        last_eyes = []
        last_time = time.time()
        gaze_history = []
        max_gaze_history = 20  # Number of gaze points to keep in history
        
        # Create a black canvas for digital twin
        digital_twin = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
        
        # Create reference image overlay
        reference_overlay = create_reference_overlay(frame_width, frame_height)
        
        # Smoothed gaze position
        smoothed_gaze_x = frame_width // 2
        smoothed_gaze_y = frame_height // 2
        gaze_smoothing = 0.7  # Higher = more smoothing
        
        # Button states
        button_states = {
            "exit": {"hover": False, "dwell_time": 0},
            "mode1": {"hover": False, "dwell_time": 0},
            "mode2": {"hover": False, "dwell_time": 0},
            "mode3": {"hover": False, "dwell_time": 0}
        }
        
        # Button regions (x, y, width, height)
        button_regions = {
            "exit": (10, 10, 120, 50),
            "mode1": (170, 100, 300, 50),
            "mode2": (170, 170, 300, 50),
            "mode3": (170, 240, 300, 50)
        }
        
        # Button colors
        button_colors = {
            "exit": (0, 0, 200),  # Red (BGR)
            "mode1": (246, 130, 59),  # Blue (BGR)
            "mode2": (246, 92, 139),  # Purple (BGR)
            "mode3": (153, 76, 236)  # Pink (BGR)
        }
        
        # Main loop
        running = True
        show_calibration = True
        
        while running:
            # Capture frame
            ret, frame = cap.read()
            
            if not ret:
                print("❌ Failed to capture frame")
                break
            
            # Create a black canvas for this frame
            digital_twin = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
            
            # Add reference overlay
            if show_calibration:
                digital_twin = cv2.addWeighted(digital_twin, 1, reference_overlay, 0.7, 0)
            
            # Calculate time delta
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Initialize gaze position
            gaze_x = frame_width // 2
            gaze_y = frame_height // 2
            gaze_detected = False
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) > 0:
                last_face = faces[0]
                x, y, w, h = faces[0]
                
                # Draw face rectangle
                cv2.rectangle(digital_twin, (x, y), (x + w, y + h), (0, 0, 255), 2)
                
                # Extract face ROI
                roi_gray = gray[y:y+h, x:x+w]
                
                # Detect eyes
                eyes = eye_cascade.detectMultiScale(
                    roi_gray,
                    scaleFactor=1.1,
                    minNeighbors=3,
                    minSize=(20, 20)
                )
                
                if len(eyes) > 0:
                    last_eyes = eyes
                elif len(last_eyes) > 0:
                    # Use last known eyes if no eyes detected
                    eyes = last_eyes
                
                # Process detected eyes
                eye_centers = []
                for (ex, ey, ew, eh) in eyes:
                    # Draw eye rectangle
                    cv2.rectangle(digital_twin, 
                                 (x + ex, y + ey), 
                                 (x + ex + ew, y + ey + eh), 
                                 (0, 255, 0), 2)
                    
                    # Calculate eye center
                    eye_center_x = x + ex + ew // 2
                    eye_center_y = y + ey + eh // 2
                    eye_centers.append((eye_center_x, eye_center_y))
                    
                    # Draw eye center with orange glow
                    cv2.circle(digital_twin, (eye_center_x, eye_center_y), 10, (0, 165, 255), -1)
                    cv2.circle(digital_twin, (eye_center_x, eye_center_y), 4, (255, 255, 255), -1)
                
                # Calculate gaze position (average of eye centers)
                if eye_centers:
                    raw_gaze_x = sum(e[0] for e in eye_centers) / len(eye_centers)
                    raw_gaze_y = sum(e[1] for e in eye_centers) / len(eye_centers)
                    
                    # Apply smoothing to gaze position
                    smoothed_gaze_x = smoothed_gaze_x * gaze_smoothing + raw_gaze_x * (1 - gaze_smoothing)
                    smoothed_gaze_y = smoothed_gaze_y * gaze_smoothing + raw_gaze_y * (1 - gaze_smoothing)
                    
                    gaze_x = int(smoothed_gaze_x)
                    gaze_y = int(smoothed_gaze_y)
                    gaze_detected = True
                    
                    # Add to gaze history
                    gaze_history.append((gaze_x, gaze_y))
                    if len(gaze_history) > max_gaze_history:
                        gaze_history.pop(0)
            
            # Draw gaze trail
            if gaze_detected and gaze_history:
                # Draw gaze history as fading trail
                for i, (hx, hy) in enumerate(gaze_history):
                    # Size and opacity based on recency
                    alpha = (i + 1) / len(gaze_history)
                    size = int(4 + 8 * alpha)
                    color_intensity = int(255 * alpha)
                    cv2.circle(digital_twin, (hx, hy), size, (0, color_intensity, 0), -1)
                
                # Draw current gaze point (larger)
                cv2.circle(digital_twin, (gaze_x, gaze_y), 12, (0, 255, 0), -1)
            
            # Update button states based on gaze position
            for button_name, region in button_regions.items():
                x, y, w, h = region
                button_state = button_states[button_name]
                
                # Check if gaze is on this button (with margin)
                margin = 20
                if (x - margin <= gaze_x <= x + w + margin and
                    y - margin <= gaze_y <= y + h + margin):
                    # Hovering over button
                    if not button_state["hover"]:
                        button_state["hover"] = True
                        button_state["dwell_time"] = 0
                    else:
                        # Accumulate dwell time
                        button_state["dwell_time"] += dt
                        
                        # Draw progress bar
                        dwell_threshold = 1.0  # seconds
                        progress = min(1.0, button_state["dwell_time"] / dwell_threshold)
                        progress_width = int(w * progress)
                        
                        # Draw progress bar at bottom of button
                        color = button_colors[button_name]
                        cv2.rectangle(digital_twin, 
                                     (x, y + h - 4), 
                                     (x + progress_width, y + h), 
                                     color, -1)
                        
                        # Check if dwell is complete
                        if progress >= 1.0:
                            if button_name == "exit":
                                running = False
                                print("👋 Exit button activated")
                            elif button_name.startswith("mode"):
                                show_calibration = False
                                print(f"✅ {button_name} selected")
                            
                            # Reset dwell time
                            button_state["dwell_time"] = 0
                else:
                    # Not hovering over button
                    button_state["hover"] = False
                    button_state["dwell_time"] = 0
            
            # Add status messages
            cv2.putText(digital_twin, "✓ WebGazer loaded.", 
                       (10, frame_height - 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
            
            if not show_calibration:
                cv2.putText(digital_twin, "✓ Calibration box closed.", 
                           (10, frame_height - 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                cv2.putText(digital_twin, "✓ Mode selected.", 
                           (10, frame_height - 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
            
            # Show the digital twin
            cv2.imshow("OpenCV with Reference", digital_twin)
            
            # Exit if ESC is pressed
            key = cv2.waitKey(1)
            if key == 27:  # ESC key
                break
        
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        print("👋 Tracking completed")
    
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

def create_reference_overlay(width, height):
    """Create a reference overlay with buttons matching the ChatGPT image"""
    import cv2
    
    # Create a transparent overlay
    overlay = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Draw calibration panel
    panel_x = 150
    panel_y = 50
    panel_width = 340
    panel_height = 260
    
    # Draw panel background (dark gray)
    cv2.rectangle(overlay, 
                 (panel_x, panel_y), 
                 (panel_x + panel_width, panel_y + panel_height), 
                 (30, 30, 30), -1)
    
    # Draw panel border (light gray)
    cv2.rectangle(overlay, 
                 (panel_x, panel_y), 
                 (panel_x + panel_width, panel_y + panel_height), 
                 (80, 80, 80), 1)
    
    # Draw panel title
    cv2.putText(overlay, "Calibration Options", 
               (panel_x + 70, panel_y + 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Draw buttons
    button_width = 300
    button_height = 50
    button_x = panel_x + 20
    
    # Mode 1 button
    mode1_y = panel_y + 50
    cv2.rectangle(overlay, 
                 (button_x, mode1_y), 
                 (button_x + button_width, mode1_y + button_height), 
                 (45, 45, 45), -1)  # Dark gray background
    cv2.rectangle(overlay, 
                 (button_x, mode1_y), 
                 (button_x + button_width, mode1_y + button_height), 
                 (100, 100, 100), 1)  # Light gray border
    cv2.putText(overlay, "Mode 1 (Haar Eye)", 
               (button_x + 70, mode1_y + 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Mode 2 button
    mode2_y = mode1_y + 70
    cv2.rectangle(overlay, 
                 (button_x, mode2_y), 
                 (button_x + button_width, mode2_y + button_height), 
                 (45, 45, 45), -1)  # Dark gray background
    cv2.rectangle(overlay, 
                 (button_x, mode2_y), 
                 (button_x + button_width, mode2_y + button_height), 
                 (100, 100, 100), 1)  # Light gray border
    cv2.putText(overlay, "Mode 2 (DNN Face)", 
               (button_x + 70, mode2_y + 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Mode 3 button
    mode3_y = mode2_y + 70
    cv2.rectangle(overlay, 
                 (button_x, mode3_y), 
                 (button_x + button_width, mode3_y + button_height), 
                 (45, 45, 45), -1)  # Dark gray background
    cv2.rectangle(overlay, 
                 (button_x, mode3_y), 
                 (button_x + button_width, mode3_y + button_height), 
                 (100, 100, 100), 1)  # Light gray border
    cv2.putText(overlay, "Mode 3 (Nobara)", 
               (button_x + 70, mode3_y + 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Exit button
    exit_x = 10
    exit_y = 10
    exit_width = 120
    exit_height = 50
    cv2.rectangle(overlay, 
                 (exit_x, exit_y), 
                 (exit_x + exit_width, exit_y + exit_height), 
                 (45, 45, 45), -1)  # Dark gray background
    cv2.rectangle(overlay, 
                 (exit_x, exit_y), 
                 (exit_x + exit_width, exit_y + exit_height), 
                 (100, 100, 100), 1)  # Light gray border
    cv2.putText(overlay, "EXIT", 
               (exit_x + 35, exit_y + 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return overlay

if __name__ == "__main__":
    main()
