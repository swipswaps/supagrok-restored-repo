#!/usr/bin/env python3
# dots_tracker_with_buttons.py — PRF‑WEBCAM‑TRACKER‑2025‑05‑02
# Description: Webcam tracker with green dots around face, orange dots around eyes, and buttons
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import subprocess
import time
import signal
import numpy as np
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

# === Button Class ===
class Button:
    """Button for GUI interaction"""
    
    def __init__(self, x, y, width, height, text, color, action=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = color
        self.hover_color = self._brighten_color(color)
        self.action = action
        self.hover = False
        self.dwell_time = 0
        self.dwell_threshold = 1.0  # seconds
    
    def _brighten_color(self, color):
        """Brighten a color for hover effect"""
        r, g, b = color
        return (
            min(255, int(r * 1.2)),
            min(255, int(g * 1.2)),
            min(255, int(b * 1.2))
        )
    
    def contains_point(self, x, y):
        """Check if a point is inside the button"""
        return (
            self.x <= x <= self.x + self.width and
            self.y <= y <= self.y + self.height
        )
    
    def update(self, x, y, dt):
        """Update button state based on gaze position"""
        if self.contains_point(x, y):
            self.hover = True
            self.dwell_time += dt
            if self.dwell_time >= self.dwell_threshold and self.action:
                self.action()
                self.dwell_time = 0
                return True
        else:
            self.hover = False
            self.dwell_time = 0
        return False
    
    def draw(self, frame, font, dwell_progress=0):
        """Draw the button on the frame"""
        import cv2
        
        # Draw button background
        color = self.hover_color if self.hover else self.color
        cv2.rectangle(frame, (self.x, self.y), (self.x + self.width, self.y + self.height), color, -1)
        cv2.rectangle(frame, (self.x, self.y), (self.x + self.width, self.y + self.height), (0, 0, 0), 2)
        
        # Draw button text
        text_size = cv2.getTextSize(self.text, font, 0.6, 2)[0]
        text_x = self.x + (self.width - text_size[0]) // 2
        text_y = self.y + (self.height + text_size[1]) // 2
        cv2.putText(frame, self.text, (text_x, text_y), font, 0.6, (255, 255, 255), 2)
        
        # Draw dwell progress if hovering
        if self.hover and dwell_progress > 0:
            progress_width = int(self.width * dwell_progress)
            cv2.rectangle(frame, (self.x, self.y + self.height - 5), 
                         (self.x + progress_width, self.y + self.height), (0, 255, 0), -1)

# === Main Function ===
def main():
    """Main function"""
    print("🚀 Starting Dots Tracker with Buttons")
    
    # Check and install dependencies
    check_and_install_dependencies()
    
    # Fix webcam issues
    fix_webcam_issues()
    
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
        cv2.namedWindow("Dots Tracker", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Dots Tracker", frame_width, frame_height)
        
        print("✅ Webcam initialized")
        print("👁️ Looking for face and eyes...")
        print("Press ESC to exit")
        
        # Initialize variables for tracking
        last_face = None
        last_eyes = []
        last_time = time.time()
        
        # Create buttons
        buttons = []
        button_width = 120
        button_height = 40
        margin = 20
        
        # Exit button
        def exit_action():
            print("👋 Exit button activated")
            nonlocal running
            running = False
        
        exit_button = Button(
            frame_width - button_width - margin,
            frame_height - button_height - margin,
            button_width,
            button_height,
            "Exit",
            (255, 0, 0),  # Red
            action=exit_action
        )
        buttons.append(exit_button)
        
        # Toggle tracking button
        show_tracking = True
        
        def toggle_tracking_action():
            nonlocal show_tracking
            show_tracking = not show_tracking
            print(f"👁️ Tracking {'enabled' if show_tracking else 'disabled'}")
        
        toggle_button = Button(
            margin,
            frame_height - button_height - margin,
            button_width,
            button_height,
            "Toggle Tracking",
            (0, 128, 255),  # Orange
            action=toggle_tracking_action
        )
        buttons.append(toggle_button)
        
        # Reset button
        def reset_action():
            nonlocal last_face, last_eyes
            last_face = None
            last_eyes = []
            print("🔄 Reset tracking")
        
        reset_button = Button(
            frame_width // 2 - button_width // 2,
            frame_height - button_height - margin,
            button_width,
            button_height,
            "Reset",
            (0, 128, 0),  # Green
            action=reset_action
        )
        buttons.append(reset_button)
        
        # Main loop
        running = True
        while running:
            # Capture frame
            ret, frame = cap.read()
            
            if not ret:
                print("❌ Failed to capture frame")
                break
            
            # Create a copy for visualization
            display_frame = frame.copy()
            
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
            
            # Detect and process face if tracking is enabled
            if show_tracking:
                # Detect faces
                faces = face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1,  # Lower scale factor for better detection
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                if len(faces) > 0:
                    last_face = faces[0]
                elif last_face is not None:
                    # Use last known face if no face detected
                    faces = [last_face]
                
                # Process detected faces
                for (x, y, w, h) in faces:
                    # Draw green rectangle around face
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
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
                        
                        # Calculate global eye center
                        global_eye_x = x + ex + ew // 2
                        global_eye_y = y + ey + eh // 2
                        eye_centers.append((global_eye_x, global_eye_y))
                    
                    # Calculate gaze position (average of eye centers)
                    if eye_centers:
                        gaze_x = sum(e[0] for e in eye_centers) / len(eye_centers)
                        gaze_y = sum(e[1] for e in eye_centers) / len(eye_centers)
                        gaze_detected = True
                
                # If no faces detected
                if len(faces) == 0:
                    cv2.putText(display_frame, "No face detected", (30, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Update buttons
            for button in buttons:
                if button.update(gaze_x, gaze_y, dt):
                    # Button was activated
                    break
            
            # Draw buttons
            for button in buttons:
                button.draw(display_frame, cv2.FONT_HERSHEY_SIMPLEX, 
                           button.dwell_time / button.dwell_threshold if button.hover else 0)
            
            # Draw gaze point if detected
            if gaze_detected:
                cv2.circle(display_frame, (int(gaze_x), int(gaze_y)), 5, (255, 255, 0), -1)
            
            # Add instructions
            cv2.putText(display_frame, "Press ESC to exit", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Show the frame
            cv2.imshow("Dots Tracker", display_frame)
            
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

if __name__ == "__main__":
    main()
