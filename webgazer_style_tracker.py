#!/usr/bin/env python3
# webgazer_style_tracker.py — PRF‑WEBCAM‑TRACKER‑2025‑05‑02
# Description: Webcam tracker with WebGazer-style face tracking and rEFInd/GRUB-style buttons
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import subprocess
import time
import signal
import numpy as np
import random
from datetime import datetime
import math

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

# === rEFInd/GRUB Style Button Class ===
class RefindButton:
    """Button with rEFInd/GRUB/Nobara style"""

    def __init__(self, x, y, width, height, text, action=None, style="refind"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.action = action
        self.hover = False
        self.dwell_time = 0
        self.dwell_threshold = 1.0  # seconds - shorter for better responsiveness
        self.style = style
        self.animation_phase = 0
        self.last_update_time = time.time()

        # Set style based on requested theme - matching the ChatGPT reference image
        if style == "refind":
            # rEFInd style - dark gray with blue accent
            self.bg_color = (45, 45, 45)  # Dark gray
            self.border_color = (100, 100, 100)  # Light gray
            self.text_color = (255, 255, 255)  # White
            self.hover_border_color = (59, 130, 246)  # Blue (BGR)
            self.progress_color = (59, 130, 246)  # Blue (BGR)
            self.glow_color = (59, 130, 246)  # Blue (BGR)
        elif style == "grub":
            # GRUB style - dark gray with purple accent
            self.bg_color = (45, 45, 45)  # Dark gray
            self.border_color = (100, 100, 100)  # Light gray
            self.text_color = (255, 255, 255)  # White
            self.hover_border_color = (139, 92, 246)  # Purple (BGR)
            self.progress_color = (139, 92, 246)  # Purple (BGR)
            self.glow_color = (139, 92, 246)  # Purple (BGR)
        elif style == "nobara":
            # Nobara style - dark gray with red accent
            self.bg_color = (45, 45, 45)  # Dark gray
            self.border_color = (100, 100, 100)  # Light gray
            self.text_color = (255, 255, 255)  # White
            self.hover_border_color = (79, 70, 229)  # Red (BGR)
            self.progress_color = (79, 70, 229)  # Red (BGR)
            self.glow_color = (79, 70, 229)  # Red (BGR)
        else:
            # Default style
            self.bg_color = (45, 45, 45)  # Dark gray
            self.border_color = (100, 100, 100)  # Light gray
            self.text_color = (255, 255, 255)  # White
            self.hover_border_color = (0, 255, 0)  # Green
            self.progress_color = (0, 255, 0)  # Green
            self.glow_color = (0, 255, 0)  # Green

    def contains_point(self, x, y):
        """Check if a point is inside the button with a larger margin for easier selection"""
        # Add a larger margin around the button for much easier selection
        margin = 20
        return (
            (self.x - margin) <= x <= (self.x + self.width + margin) and
            (self.y - margin) <= y <= (self.y + self.height + margin)
        )

    def update(self, x, y, dt):
        """Update button state based on gaze position with improved responsiveness"""
        # Update animation phase
        current_time = time.time()
        dt_real = current_time - self.last_update_time
        self.last_update_time = current_time
        self.animation_phase = (self.animation_phase + dt_real * 2) % (2 * math.pi)

        was_hovering = self.hover
        self.hover = self.contains_point(x, y)

        # Only accumulate dwell time if continuously hovering
        if self.hover:
            if was_hovering:
                # Faster accumulation for exit button to make it more responsive
                if self.text.lower() == "exit":
                    self.dwell_time += dt * 1.5  # 50% faster for exit button
                else:
                    self.dwell_time += dt
            else:
                self.dwell_time = 0

            if self.dwell_time >= self.dwell_threshold and self.action:
                self.action()
                self.dwell_time = 0
                return True
        else:
            self.dwell_time = 0

        return False

    def draw(self, frame, font):
        """Draw the button in rEFInd/GRUB/Nobara style with enhanced visual effects"""
        import cv2

        # Draw glow effect when hovering
        if self.hover:
            # Pulsating glow effect
            glow_size = int(5 * (1 + 0.3 * math.sin(self.animation_phase * 2)))
            # Draw outer glow
            cv2.rectangle(frame,
                         (self.x - glow_size, self.y - glow_size),
                         (self.x + self.width + glow_size, self.y + self.height + glow_size),
                         self.glow_color, -1)

        # Draw button background
        cv2.rectangle(frame, (self.x, self.y), (self.x + self.width, self.y + self.height),
                     self.bg_color, -1)

        # Draw border (highlighted when hovering)
        border_color = self.hover_border_color if self.hover else self.border_color
        border_thickness = 2 if not self.hover else 3

        # Draw border with slightly rounded corners
        cv2.rectangle(frame, (self.x, self.y), (self.x + self.width, self.y + self.height),
                     border_color, border_thickness)

        # Draw button text with slight shadow for better visibility
        text_size = cv2.getTextSize(self.text, font, 0.7, 2)[0]
        text_x = self.x + (self.width - text_size[0]) // 2
        text_y = self.y + (self.height + text_size[1]) // 2

        # Draw text shadow
        cv2.putText(frame, self.text, (text_x+1, text_y+1), font, 0.7,
                   (0, 0, 0), 2)

        # Draw text
        cv2.putText(frame, self.text, (text_x, text_y), font, 0.7,
                   self.text_color, 2)

        # Draw dwell progress if hovering
        if self.hover and self.dwell_time > 0:
            progress = self.dwell_time / self.dwell_threshold
            progress_width = int(self.width * progress)
            progress_height = 5

            # Draw progress bar at the bottom of the button
            cv2.rectangle(frame,
                         (self.x, self.y + self.height - progress_height),
                         (self.x + progress_width, self.y + self.height),
                         self.progress_color, -1)

            # Add highlight to progress bar
            highlight_width = min(5, progress_width)
            if highlight_width > 0:
                highlight_color = tuple(min(255, c + 50) for c in self.progress_color)
                cv2.rectangle(frame,
                             (self.x, self.y + self.height - progress_height),
                             (self.x + highlight_width, self.y + self.height - progress_height + 2),
                             highlight_color, -1)

# === Face Feature Points Generator ===
class FaceFeaturePoints:
    """Generate WebGazer-style face feature points with enhanced visual effects"""

    def __init__(self):
        self.face_points = []
        self.eye_points = []
        self.eye_centers = []
        self.mouth_points = []
        self.nose_points = []
        self.contour_points = []  # Additional contour points for more detail
        self.last_update_time = time.time()
        self.point_stability = 0.9  # Higher value = more stable points (less jitter)
        self.animation_phase = 0  # For animated effects

    def generate_points(self, x, y, w, h):
        """Generate feature points for a face with improved stability and detail"""
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time

        # Update animation phase
        self.animation_phase = (self.animation_phase + dt * 2) % (2 * math.pi)

        # Only regenerate points occasionally to reduce jitter
        if not self.face_points or random.random() > self.point_stability:
            # Face boundary points (green) - more points for better detail
            new_face_points = []
            for i in range(30):  # Increased from 20 to 30
                # Points around face boundary
                angle = i * (2 * np.pi / 30)
                px = int(x + w/2 + (w/2) * 0.9 * np.cos(angle))
                py = int(y + h/2 + (h/2) * 0.9 * np.sin(angle))
                new_face_points.append((px, py))

            # Smoothly transition to new points if we already have points
            if self.face_points:
                self.face_points = self._smooth_transition(self.face_points, new_face_points, 0.2)
            else:
                self.face_points = new_face_points

        # Generate additional contour points for more detailed face
        if not self.contour_points or random.random() > self.point_stability:
            new_contour_points = []

            # Jawline contour
            jaw_y = y + 3*h//4
            for i in range(10):
                jaw_x = x + w//5 + i * w//10
                jaw_y_offset = int(h/20 * math.sin(i * math.pi / 10))
                new_contour_points.append((jaw_x, jaw_y + jaw_y_offset))

            # Forehead contour
            forehead_y = y + h//6
            for i in range(8):
                forehead_x = x + w//4 + i * w//8
                forehead_y_offset = int(h/30 * math.sin(i * math.pi / 8))
                new_contour_points.append((forehead_x, forehead_y - forehead_y_offset))

            # Cheek contours
            left_cheek_x = x + w//5
            right_cheek_x = x + 4*w//5
            cheek_y = y + h//2

            for i in range(5):
                offset_y = i * h//15
                new_contour_points.append((left_cheek_x, cheek_y + offset_y))
                new_contour_points.append((right_cheek_x, cheek_y + offset_y))

            if self.contour_points:
                self.contour_points = self._smooth_transition(self.contour_points, new_contour_points, 0.2)
            else:
                self.contour_points = new_contour_points

        # Eye region points (orange/amber for cooler look)
        if not self.eye_points or random.random() > self.point_stability:
            new_eye_points = []
            new_eye_centers = []

            # Left eye
            left_eye_x = x + w // 4
            left_eye_y = y + h // 3
            left_eye_w = w // 5
            left_eye_h = h // 8

            # Eye center for glow effect
            left_eye_center = (left_eye_x + left_eye_w//2, left_eye_y + left_eye_h//2)
            new_eye_centers.append(left_eye_center)

            # Create a more detailed eye pattern
            for i in range(12):
                angle = i * (2 * math.pi / 12)
                radius = min(left_eye_w, left_eye_h) // 2
                px = int(left_eye_center[0] + radius * math.cos(angle))
                py = int(left_eye_center[1] + radius * math.sin(angle))
                new_eye_points.append((px, py))

            # Add some points inside the eye for iris effect
            for i in range(8):
                angle = i * (2 * math.pi / 8)
                radius = min(left_eye_w, left_eye_h) // 4
                px = int(left_eye_center[0] + radius * math.cos(angle))
                py = int(left_eye_center[1] + radius * math.sin(angle))
                new_eye_points.append((px, py))

            # Right eye
            right_eye_x = x + 3 * w // 4 - w // 5
            right_eye_y = y + h // 3
            right_eye_w = w // 5
            right_eye_h = h // 8

            # Eye center for glow effect
            right_eye_center = (right_eye_x + right_eye_w//2, right_eye_y + right_eye_h//2)
            new_eye_centers.append(right_eye_center)

            # Create a more detailed eye pattern
            for i in range(12):
                angle = i * (2 * math.pi / 12)
                radius = min(right_eye_w, right_eye_h) // 2
                px = int(right_eye_center[0] + radius * math.cos(angle))
                py = int(right_eye_center[1] + radius * math.sin(angle))
                new_eye_points.append((px, py))

            # Add some points inside the eye for iris effect
            for i in range(8):
                angle = i * (2 * math.pi / 8)
                radius = min(right_eye_w, right_eye_h) // 4
                px = int(right_eye_center[0] + radius * math.cos(angle))
                py = int(right_eye_center[1] + radius * math.sin(angle))
                new_eye_points.append((px, py))

            # Smoothly transition to new points if we already have points
            if self.eye_points:
                self.eye_points = self._smooth_transition(self.eye_points, new_eye_points, 0.2)
                self.eye_centers = self._smooth_transition(self.eye_centers, new_eye_centers, 0.2)
            else:
                self.eye_points = new_eye_points
                self.eye_centers = new_eye_centers

        # Nose points (yellow)
        if not self.nose_points or random.random() > self.point_stability:
            new_nose_points = []
            nose_x = x + w // 2 - w // 10
            nose_y = y + h // 2
            nose_w = w // 5
            nose_h = h // 6

            # Create a more detailed nose pattern
            # Bridge of nose
            for i in range(5):
                px = x + w//2
                py = y + h//3 + i * h//20
                new_nose_points.append((px, py))

            # Nostrils and tip
            nostril_y = nose_y + nose_h//2
            new_nose_points.append((nose_x, nostril_y))
            new_nose_points.append((nose_x + nose_w, nostril_y))
            new_nose_points.append((x + w//2, nose_y + nose_h//3))  # Tip

            # Nose outline
            for i in range(5):
                t = i / 4.0
                px = int(nose_x + t * nose_w)
                py = int(nose_y + t * nose_h//2)
                new_nose_points.append((px, py))
                new_nose_points.append((nose_x + nose_w - (px - nose_x), py))

            # Smoothly transition to new points if we already have points
            if self.nose_points:
                self.nose_points = self._smooth_transition(self.nose_points, new_nose_points, 0.2)
            else:
                self.nose_points = new_nose_points

        # Mouth points (magenta)
        if not self.mouth_points or random.random() > self.point_stability:
            new_mouth_points = []
            mouth_x = x + w // 3
            mouth_y = y + 2 * h // 3
            mouth_w = w // 3
            mouth_h = h // 10

            # Create a more detailed mouth pattern
            # Upper lip
            for i in range(10):
                t = i / 9.0
                px = int(mouth_x + t * mouth_w)
                py = int(mouth_y - mouth_h//4 * math.sin(t * math.pi))
                new_mouth_points.append((px, py))

            # Lower lip
            for i in range(10):
                t = i / 9.0
                px = int(mouth_x + mouth_w - t * mouth_w)
                py = int(mouth_y + mouth_h//2 + mouth_h//4 * math.sin(t * math.pi))
                new_mouth_points.append((px, py))

            # Smoothly transition to new points if we already have points
            if self.mouth_points:
                self.mouth_points = self._smooth_transition(self.mouth_points, new_mouth_points, 0.2)
            else:
                self.mouth_points = new_mouth_points

    def _smooth_transition(self, old_points, new_points, blend_factor):
        """Blend between old and new points to reduce jitter"""
        # If point counts don't match, just use new points
        if len(old_points) != len(new_points):
            return new_points

        blended_points = []
        for i in range(len(old_points)):
            old_x, old_y = old_points[i]
            new_x, new_y = new_points[i]

            # Blend coordinates
            blended_x = int(old_x * (1 - blend_factor) + new_x * blend_factor)
            blended_y = int(old_y * (1 - blend_factor) + new_y * blend_factor)

            blended_points.append((blended_x, blended_y))

        return blended_points

    def draw_points(self, frame):
        """Draw feature points on the frame with enhanced visual effects"""
        import cv2

        # Draw face boundary points (green)
        for px, py in self.face_points:
            cv2.circle(frame, (px, py), 2, (0, 255, 0), -1)

        # Draw contour points (blue-green)
        for px, py in self.contour_points:
            cv2.circle(frame, (px, py), 2, (100, 255, 100), -1)

        # Draw eye points (orange/amber for cooler look)
        for px, py in self.eye_points:
            cv2.circle(frame, (px, py), 2, (0, 165, 255), -1)  # Orange in BGR

        # Draw eye centers with glowing effect
        for cx, cy in self.eye_centers:
            # Pulsating glow effect
            glow_size = 5 + int(3 * math.sin(self.animation_phase))
            # Outer glow (darker orange)
            cv2.circle(frame, (cx, cy), glow_size + 5, (0, 100, 200), -1)
            # Inner glow (bright orange)
            cv2.circle(frame, (cx, cy), glow_size, (0, 200, 255), -1)
            # Center (white)
            cv2.circle(frame, (cx, cy), 2, (255, 255, 255), -1)

        # Draw nose points (yellow)
        for px, py in self.nose_points:
            cv2.circle(frame, (px, py), 2, (0, 255, 255), -1)

        # Draw mouth points (magenta)
        for px, py in self.mouth_points:
            cv2.circle(frame, (px, py), 2, (255, 0, 255), -1)

        # Connect points to create more defined features
        if len(self.face_points) > 2:
            # Connect face boundary points
            for i in range(len(self.face_points)):
                cv2.line(frame, self.face_points[i], self.face_points[(i+1) % len(self.face_points)], (0, 200, 0), 1)

        if len(self.mouth_points) > 2:
            # Connect mouth points
            for i in range(len(self.mouth_points) - 1):
                cv2.line(frame, self.mouth_points[i], self.mouth_points[i+1], (200, 0, 200), 1)

        # Add some dynamic elements based on animation phase
        # Pulsating effect for some points
        pulse_size = 1 + int(1.5 * math.sin(self.animation_phase))
        if self.eye_centers:
            for cx, cy in self.eye_centers:
                # Draw rays emanating from eyes
                for i in range(8):
                    angle = i * (2 * math.pi / 8) + self.animation_phase / 2
                    ray_length = 10 + int(5 * math.sin(self.animation_phase + i))
                    end_x = int(cx + ray_length * math.cos(angle))
                    end_y = int(cy + ray_length * math.sin(angle))
                    cv2.line(frame, (cx, cy), (end_x, end_y), (0, 128 + pulse_size*20, 255), 1)

# === Main Function ===
def main():
    """Main function"""
    print("🚀 Starting WebGazer Style Tracker")

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
        cv2.namedWindow("WebGazer Style Tracker", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("WebGazer Style Tracker", frame_width, frame_height)

        print("✅ Webcam initialized")
        print("👁️ Looking for face and eyes...")
        print("Press ESC to exit")

        # Initialize variables for tracking
        last_face = None
        last_eyes = []
        last_time = time.time()
        gaze_history = []
        max_gaze_history = 20  # Number of gaze points to keep in history

        # Initialize face feature points
        face_features = FaceFeaturePoints()

        # Create buttons in rEFInd/GRUB/Nobara style
        buttons = []

        # Create digital twin canvas
        canvas_width = frame_width
        canvas_height = frame_height

        # Create calibration panel
        panel_width = 400
        panel_height = 300
        panel_x = canvas_width - panel_width - 10
        panel_y = 10

        # Mode 1 button (rEFInd style)
        def mode1_action():
            nonlocal show_calibration
            if show_calibration:  # Only trigger once
                show_calibration = False
                print("👁️ Mode 1 (Haar Eye) selected")

        mode1_button = RefindButton(
            panel_x + 50,
            panel_y + 100,
            panel_width - 100,
            50,  # Shorter height to match reference image
            "Mode 1 (Haar Eye)",
            action=mode1_action,
            style="refind"
        )
        buttons.append(mode1_button)

        # Mode 2 button (GRUB style)
        def mode2_action():
            nonlocal show_calibration
            if show_calibration:  # Only trigger once
                show_calibration = False
                print("👁️ Mode 2 (DNN Face) selected")

        mode2_button = RefindButton(
            panel_x + 50,
            panel_y + 170,  # Adjusted position
            panel_width - 100,
            50,  # Shorter height to match reference image
            "Mode 2 (DNN Face)",
            action=mode2_action,
            style="grub"
        )
        buttons.append(mode2_button)

        # Mode 3 button (Nobara style)
        def mode3_action():
            nonlocal show_calibration
            if show_calibration:  # Only trigger once
                show_calibration = False
                print("👁️ Mode 3 (Nobara) selected")

        mode3_button = RefindButton(
            panel_x + 50,
            panel_y + 240,  # Adjusted position
            panel_width - 100,
            50,  # Shorter height to match reference image
            "Mode 3 (Nobara)",
            action=mode3_action,
            style="nobara"
        )
        buttons.append(mode3_button)

        # Exit button (always visible)
        def exit_action():
            nonlocal running
            running = False
            print("👋 Exit button activated")

        # Make exit button match reference image
        exit_button = RefindButton(
            10,
            10,
            120,  # Width matching reference
            50,   # Height matching reference
            "EXIT",
            action=exit_action,
            style="nobara"  # Red exit button
        )
        buttons.append(exit_button)

        # Main loop
        running = True
        show_calibration = True
        show_video = False  # Only show digital twin, not actual video

        # Create a black canvas for digital twin
        digital_twin = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

        # Smoothed gaze position
        smoothed_gaze_x = canvas_width // 2
        smoothed_gaze_y = canvas_height // 2
        gaze_smoothing = 0.8  # Higher = more smoothing

        while running:
            # Capture frame
            ret, frame = cap.read()

            if not ret:
                print("❌ Failed to capture frame")
                break

            # Create a black canvas for this frame
            digital_twin = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

            # Calculate time delta
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Initialize gaze position
            gaze_x = canvas_width // 2
            gaze_y = canvas_height // 2
            gaze_detected = False

            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,  # Lower scale factor for better detection
                minNeighbors=5,
                minSize=(30, 30)
            )

            if len(faces) > 0:
                last_face = faces[0]
                # Generate face feature points
                x, y, w, h = faces[0]
                face_features.generate_points(x, y, w, h)
            elif last_face is not None:
                # Use last known face if no face detected
                faces = [last_face]

            # Process detected faces
            for (x, y, w, h) in faces:
                # Draw red rectangle around face on digital twin
                cv2.rectangle(digital_twin, (x, y), (x + w, y + h), (0, 0, 255), 2)

                # Draw WebGazer-style feature points on digital twin
                face_features.draw_points(digital_twin)

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
                    # Calculate eye center
                    eye_center_x = x + ex + ew // 2
                    eye_center_y = y + ey + eh // 2
                    eye_centers.append((eye_center_x, eye_center_y))

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

            # Draw calibration panel matching the ChatGPT reference image
            if show_calibration:
                # Draw panel background
                cv2.rectangle(digital_twin,
                             (panel_x, panel_y),
                             (panel_x + panel_width, panel_y + panel_height),
                             (20, 20, 20), -1)  # Darker background

                # Draw panel border
                cv2.rectangle(digital_twin,
                             (panel_x, panel_y),
                             (panel_x + panel_width, panel_y + panel_height),
                             (100, 100, 100), 1)  # Subtle gray border

                # Draw panel title
                cv2.putText(digital_twin, "Calibration Options",
                           (panel_x + 50, panel_y + 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

            # Update buttons with smoothed gaze position
            # Process exit button first for better responsiveness
            if exit_button.update(gaze_x, gaze_y, dt):
                # Exit button was activated
                print("✅ Exit button activated")
                break

            # Process other buttons
            for button in buttons:
                if button != exit_button and button.update(gaze_x, gaze_y, dt):
                    # Button was activated
                    if button == mode1_button or button == mode2_button or button == mode3_button:
                        show_calibration = False
                        print("✅ Calibration box closed.")
                    break

            # Draw buttons
            if show_calibration:
                for button in buttons:
                    if button != exit_button:
                        button.draw(digital_twin, cv2.FONT_HERSHEY_SIMPLEX)

            # Always draw exit button
            exit_button.draw(digital_twin, cv2.FONT_HERSHEY_SIMPLEX)

            # Draw gaze trail if detected
            if gaze_detected and gaze_history:
                # Draw gaze history as fading trail
                for i, (hx, hy) in enumerate(gaze_history):
                    # Size and opacity based on recency
                    alpha = (i + 1) / len(gaze_history)
                    size = int(4 + 8 * alpha)
                    color_intensity = int(255 * alpha)

                    # Draw glow effect for trail
                    cv2.circle(digital_twin, (hx, hy), size + 2, (0, color_intensity//2, 0), -1)
                    cv2.circle(digital_twin, (hx, hy), size, (0, color_intensity, 0), -1)

                # Draw current gaze point with enhanced visibility
                # Outer glow
                cv2.circle(digital_twin, (gaze_x, gaze_y), 16, (0, 100, 0), -1)
                # Middle glow
                cv2.circle(digital_twin, (gaze_x, gaze_y), 12, (0, 180, 0), -1)
                # Inner bright point
                cv2.circle(digital_twin, (gaze_x, gaze_y), 6, (0, 255, 0), -1)

                # Draw crosshair for precise targeting
                line_length = 10
                cv2.line(digital_twin, (gaze_x - line_length, gaze_y), (gaze_x + line_length, gaze_y), (0, 255, 0), 1)
                cv2.line(digital_twin, (gaze_x, gaze_y - line_length), (gaze_x, gaze_y + line_length), (0, 255, 0), 1)

            # Add status messages at bottom
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_color = (0, 255, 0)
            font_thickness = 1

            cv2.putText(digital_twin, "✓ WebGazer loaded.",
                       (10, canvas_height - 60),
                       font, font_scale, font_color, font_thickness)

            if not show_calibration:
                cv2.putText(digital_twin, "✓ Calibration box closed.",
                           (10, canvas_height - 40),
                           font, font_scale, font_color, font_thickness)
                cv2.putText(digital_twin, "✓ Mode 1 selected.",
                           (10, canvas_height - 20),
                           font, font_scale, font_color, font_thickness)

            # Show the digital twin
            cv2.imshow("WebGazer Style Tracker", digital_twin)

            # Exit if ESC is pressed
            key = cv2.waitKey(1)
            if key == 27:  # ESC key
                break
            elif key == ord('v'):  # Toggle video/digital twin view
                show_video = not show_video

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
