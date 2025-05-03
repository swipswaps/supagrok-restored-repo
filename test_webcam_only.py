#!/usr/bin/env python3
# test_webcam_only.py - Test just the webcam eye tracking visualization

import sys
import subprocess
import time

def check_dependencies():
    """Check and install required dependencies"""
    print("🔍 Checking dependencies...")
    
    try:
        # Check for OpenCV
        import cv2
        print("✅ OpenCV is installed")
    except ImportError:
        print("❌ OpenCV is not installed, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python"])
    
    try:
        # Check for NumPy
        import numpy
        print("✅ NumPy is installed")
    except ImportError:
        print("❌ NumPy is not installed, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])

def main():
    """Main function"""
    print("🚀 Starting webcam eye tracking test")
    
    # Check dependencies
    check_dependencies()
    
    # Import after dependencies are installed
    import cv2
    import numpy as np
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Failed to open webcam")
        return
    
    # Load face and eye cascade classifiers
    cv_path = cv2.__path__[0]
    face_cascade = cv2.CascadeClassifier(f'{cv_path}/data/haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(f'{cv_path}/data/haarcascade_eye.xml')
    
    if face_cascade.empty() or eye_cascade.empty():
        print("❌ Failed to load cascade classifiers")
        return
    
    # Create window
    cv2.namedWindow("Eye Tracking Test", cv2.WINDOW_NORMAL)
    
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
            
            # Extract face ROI
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = display_frame[y:y+h, x:x+w]
            
            # Detect eyes
            eyes = eye_cascade.detectMultiScale(roi_gray)
            
            # Process detected eyes
            for (ex, ey, ew, eh) in eyes:
                # Draw orange rectangle around eye
                cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 165, 255), 2)
                
                # Draw points around the eye
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
        cv2.putText(display_frame, "Press ESC to exit", (10, display_frame.shape[0] - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Show the frame
        cv2.imshow("Eye Tracking Test", display_frame)
        
        # Exit if ESC is pressed
        if cv2.waitKey(1) == 27:
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    print("👋 Test completed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
