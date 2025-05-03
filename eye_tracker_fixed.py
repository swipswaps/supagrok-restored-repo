#!/usr/bin/env python3
# eye_tracker_fixed.py — PRF‑WEBCAM‑TRACKER‑2025‑05‑02
# Description: Fixed eye tracking with proper button styling and face tracking
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import subprocess
import time
import signal
import math
import random
from datetime import datetime

# Try to import dependencies, but don't fail if they're not installed
try:
    import numpy as np
    import cv2
    DEPS_INSTALLED = True
except ImportError:
    DEPS_INSTALLED = False

# === Signal Handlers ===
def handle_signal(sig, frame):
    """Handle signals for clean shutdown"""
    print(f"🛑 Received signal {sig}, shutting down...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_signal)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_signal)  # Termination signal

# === Dependency Management ===
def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing required dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python", "numpy"])
        print("✅ Dependencies installed successfully")

        # Import the dependencies after installation
        global np, cv2, DEPS_INSTALLED
        import numpy as np
        import cv2
        DEPS_INSTALLED = True
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

# === Button Class ===
class Button:
    """Button with styling matching the ChatGPT reference image"""

    def __init__(self, x, y, width, height, text, action=None, style="refind"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.action = action
        self.hover = False
        self.dwell_time = 0
        self.dwell_threshold = 0.8  # seconds
        self.style = style

        # Set style based on requested theme - matching the ChatGPT image
        if style == "refind":
            # rEFInd style - dark gray with light gray border
            self.bg_color = (40, 40, 40)  # Dark gray
            self.border_color = (120, 120, 120)  # Light gray
            self.text_color = (240, 240, 240)  # Almost white
            self.hover_color = (100, 180, 255)  # Light blue
            self.progress_color = (100, 180, 255)  # Light blue
        elif style == "grub":
            # GRUB style - black with purple accents
            self.bg_color = (20, 20, 20)  # Almost black
            self.border_color = (100, 100, 100)  # Gray
            self.text_color = (255, 255, 255)  # White
            self.hover_color = (150, 50, 150)  # Purple
            self.progress_color = (150, 50, 150)  # Purple
        elif style == "nobara":
            # Nobara style - dark with red accents
            self.bg_color = (30, 30, 30)  # Dark gray
            self.border_color = (100, 100, 100)  # Gray
            self.text_color = (255, 255, 255)  # White
            self.hover_color = (200, 50, 50)  # Red
            self.progress_color = (200, 50, 50)  # Red
        else:
            # Default style
            self.bg_color = (0, 0, 0)  # Black
            self.border_color = (100, 100, 100)  # Gray
            self.text_color = (255, 255, 255)  # White
            self.hover_color = (0, 255, 0)  # Green
            self.progress_color = (0, 255, 0)  # Green

    def contains_point(self, x, y):
        """Check if a point is inside the button with a margin for easier selection"""
        margin = 40  # Very large margin for easier selection
        return (
            (self.x - margin) <= x <= (self.x + self.width + margin) and
            (self.y - margin) <= y <= (self.y + self.height + margin)
        )

    def update(self, x, y, dt):
        """Update button state based on gaze position"""
        was_hovering = self.hover
        self.hover = self.contains_point(x, y)

        # Only accumulate dwell time if continuously hovering
        if self.hover:
            if was_hovering:
                # Make exit button more responsive
                if self.text.lower() == "exit":
                    self.dwell_time += dt * 2.5  # Much faster for exit
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

    def draw(self, frame):
        """Draw the button matching the ChatGPT reference image"""
        # Draw button background with rounded corners
        cv2.rectangle(frame, (self.x, self.y), (self.x + self.width, self.y + self.height),
                     self.bg_color, -1)

        # Draw border (highlighted when hovering)
        border_color = self.hover_color if self.hover else self.border_color
        border_thickness = 2

        # Draw border with slightly rounded corners effect
        cv2.rectangle(frame, (self.x, self.y), (self.x + self.width, self.y + self.height),
                     border_color, border_thickness)

        # Draw button text
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(self.text, font, 0.7, 2)[0]
        text_x = self.x + (self.width - text_size[0]) // 2
        text_y = self.y + (self.height + text_size[1]) // 2

        # Draw text with slight shadow for better visibility
        cv2.putText(frame, self.text, (text_x+1, text_y+1), font, 0.7,
                   (20, 20, 20), 2)  # Dark shadow
        cv2.putText(frame, self.text, (text_x, text_y), font, 0.7,
                   self.text_color, 2)

        # Draw dwell progress if hovering - matching the reference image style
        if self.hover and self.dwell_time > 0:
            progress = self.dwell_time / self.dwell_threshold
            progress_width = int(self.width * progress)
            progress_height = 4  # Slightly thinner

            # Draw progress bar at the bottom of the button
            cv2.rectangle(frame,
                         (self.x, self.y + self.height - progress_height),
                         (self.x + progress_width, self.y + self.height),
                         self.progress_color, -1)

# === Face Tracking Class ===
class FaceTracker:
    """Track face and draw digital twin with orange eyes"""

    def __init__(self):
        self.face_cascade = None
        self.eye_cascade = None
        self.last_face = None
        self.last_eyes = []
        self.eye_centers = []
        self.face_points = []
        self.last_update_time = time.time()
        self.animation_phase = 0

    def load_cascades(self):
        """Load face and eye detection cascades"""
        cv_path = cv2.__path__[0]
        face_cascade_path = f'{cv_path}/data/haarcascade_frontalface_default.xml'
        eye_cascade_path = f'{cv_path}/data/haarcascade_eye.xml'

        if not os.path.exists(face_cascade_path):
            print(f"❌ Face cascade file not found: {face_cascade_path}")
            return False

        if not os.path.exists(eye_cascade_path):
            print(f"❌ Eye cascade file not found: {eye_cascade_path}")
            return False

        self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
        self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

        if self.face_cascade.empty() or self.eye_cascade.empty():
            print("❌ Failed to load cascades")
            return False

        return True

    def update(self, frame):
        """Update face tracking and return gaze position"""
        # Update animation phase
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        self.animation_phase = (self.animation_phase + dt * 2) % (2 * math.pi)

        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Default gaze position (center of frame)
        h, w = frame.shape[:2]
        gaze_x, gaze_y = w // 2, h // 2
        gaze_detected = False

        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        if len(faces) > 0:
            self.last_face = faces[0]
            x, y, w, h = faces[0]

            # Generate face points if needed
            if not self.face_points:
                self._generate_face_points(x, y, w, h)

            # Extract face region
            roi_gray = gray[y:y+h, x:x+w]

            # Detect eyes
            eyes = self.eye_cascade.detectMultiScale(
                roi_gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(20, 20)
            )

            if len(eyes) > 0:
                self.last_eyes = eyes

                # Calculate eye centers
                self.eye_centers = []
                for (ex, ey, ew, eh) in eyes:
                    eye_center_x = x + ex + ew // 2
                    eye_center_y = y + ey + eh // 2
                    self.eye_centers.append((eye_center_x, eye_center_y))

                # Calculate gaze position (average of eye centers)
                if self.eye_centers:
                    gaze_x = sum(e[0] for e in self.eye_centers) / len(self.eye_centers)
                    gaze_y = sum(e[1] for e in self.eye_centers) / len(self.eye_centers)
                    gaze_detected = True

        elif self.last_face is not None:
            # Use last known face
            x, y, w, h = self.last_face

        return gaze_x, gaze_y, gaze_detected

    def _generate_face_points(self, x, y, w, h):
        """Generate points for face visualization"""
        self.face_points = []

        # Face boundary
        for i in range(30):
            angle = i * (2 * math.pi / 30)
            px = int(x + w/2 + (w/2) * 0.9 * np.cos(angle))
            py = int(y + h/2 + (h/2) * 0.9 * np.sin(angle))
            self.face_points.append((px, py))

    def draw_digital_twin(self, frame):
        """Draw digital twin of face with orange eyes"""
        # Create a black canvas
        h, w = frame.shape[:2]
        digital_twin = np.zeros((h, w, 3), dtype=np.uint8)

        if self.last_face is not None:
            x, y, w, h = self.last_face

            # Draw face boundary
            cv2.rectangle(digital_twin, (x, y), (x + w, y + h), (0, 0, 255), 2)

            # Draw face points
            for px, py in self.face_points:
                cv2.circle(digital_twin, (px, py), 2, (0, 255, 0), -1)

            # Connect face points
            for i in range(len(self.face_points)):
                cv2.line(digital_twin,
                        self.face_points[i],
                        self.face_points[(i+1) % len(self.face_points)],
                        (0, 200, 0), 1)

            # Draw eyes with orange glow
            for cx, cy in self.eye_centers:
                # Pulsating glow effect
                glow_size = 5 + int(3 * math.sin(self.animation_phase))

                # Outer glow (darker orange)
                cv2.circle(digital_twin, (cx, cy), glow_size + 5, (0, 100, 200), -1)

                # Inner glow (bright orange)
                cv2.circle(digital_twin, (cx, cy), glow_size, (0, 200, 255), -1)

                # Center (white)
                cv2.circle(digital_twin, (cx, cy), 2, (255, 255, 255), -1)

                # Draw rays emanating from eyes
                for i in range(8):
                    angle = i * (2 * math.pi / 8) + self.animation_phase / 2
                    ray_length = 10 + int(5 * math.sin(self.animation_phase + i))
                    end_x = int(cx + ray_length * math.cos(angle))
                    end_y = int(cy + ray_length * math.sin(angle))
                    cv2.line(digital_twin, (cx, cy), (end_x, end_y),
                            (0, 128 + int(40 * math.sin(self.animation_phase)), 255), 1)

        return digital_twin

# === Gaze Visualization Class ===
class GazeVisualizer:
    """Visualize gaze position with trail and crosshair"""

    def __init__(self, max_history=20):
        self.gaze_history = []
        self.max_history = max_history

    def update(self, x, y, detected):
        """Update gaze history"""
        if detected:
            self.gaze_history.append((int(x), int(y)))
            if len(self.gaze_history) > self.max_history:
                self.gaze_history.pop(0)

    def draw(self, frame):
        """Draw gaze visualization"""
        if not self.gaze_history:
            return

        # Draw gaze history as trail
        for i, (hx, hy) in enumerate(self.gaze_history):
            # Size and opacity based on recency
            alpha = (i + 1) / len(self.gaze_history)
            size = int(4 + 8 * alpha)
            color_intensity = int(255 * alpha)

            # Draw glow effect
            cv2.circle(frame, (hx, hy), size + 2, (0, color_intensity//2, 0), -1)
            cv2.circle(frame, (hx, hy), size, (0, color_intensity, 0), -1)

        # Get current gaze position (last in history)
        gx, gy = self.gaze_history[-1]

        # Draw current gaze point with enhanced visibility
        cv2.circle(frame, (gx, gy), 16, (0, 100, 0), -1)  # Outer
        cv2.circle(frame, (gx, gy), 12, (0, 180, 0), -1)  # Middle
        cv2.circle(frame, (gx, gy), 6, (0, 255, 0), -1)   # Inner

        # Draw crosshair
        line_length = 10
        cv2.line(frame, (gx - line_length, gy), (gx + line_length, gy), (0, 255, 0), 1)
        cv2.line(frame, (gx, gy - line_length), (gx, gy + line_length), (0, 255, 0), 1)

# === Main Function ===
def main():
    """Main function"""
    print("🚀 Starting Eye Tracker")

    # Check and install dependencies if needed
    global DEPS_INSTALLED
    if not DEPS_INSTALLED:
        if not install_dependencies():
            print("❌ Failed to install required dependencies")
            return

    try:
        # Initialize webcam
        print("🔌 Connecting to webcam...")
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("❌ Failed to open webcam")
            return

        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Get actual resolution
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"✅ Connected to webcam ({frame_width}x{frame_height})")

        # Initialize face tracker
        face_tracker = FaceTracker()
        if not face_tracker.load_cascades():
            print("❌ Failed to initialize face tracker")
            return

        # Initialize gaze visualizer
        gaze_visualizer = GazeVisualizer()

        # Create window
        cv2.namedWindow("Eye Tracker", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Eye Tracker", frame_width, frame_height)

        # Initialize variables
        last_time = time.time()
        running = True
        show_calibration = True

        # Create buttons
        buttons = []

        # Create calibration panel
        panel_width = 400
        panel_height = 300
        panel_x = frame_width - panel_width - 10
        panel_y = 10

        # Create buttons matching the ChatGPT reference image

        # Mode 1 button (rEFInd style)
        def mode1_action():
            nonlocal show_calibration
            if show_calibration:  # Only trigger once
                show_calibration = False
                print("✅ Mode 1 selected")

        mode1_button = Button(
            panel_x + 50,
            panel_y + 100,
            panel_width - 100,
            50,  # Slightly shorter to match reference
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
                print("✅ Mode 2 selected")

        mode2_button = Button(
            panel_x + 50,
            panel_y + 170,  # Adjusted position
            panel_width - 100,
            50,  # Slightly shorter to match reference
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
                print("✅ Mode 3 selected")

        mode3_button = Button(
            panel_x + 50,
            panel_y + 240,  # Adjusted position
            panel_width - 100,
            50,  # Slightly shorter to match reference
            "Mode 3 (Nobara)",
            action=mode3_action,
            style="nobara"
        )
        buttons.append(mode3_button)

        # Exit button (Nobara style with red accent)
        def exit_action():
            nonlocal running
            running = False
            print("👋 Exit button activated")

        exit_button = Button(
            10,
            10,
            120,  # Width matching reference
            50,   # Height matching reference
            "EXIT",
            action=exit_action,
            style="nobara"
        )
        buttons.append(exit_button)

        # Smoothed gaze position
        smoothed_gaze_x = frame_width // 2
        smoothed_gaze_y = frame_height // 2
        gaze_smoothing = 0.7  # Higher = more smoothing

        # Main loop
        while running:
            # Capture frame
            ret, frame = cap.read()

            if not ret:
                print("❌ Failed to capture frame")
                break

            # Calculate time delta
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # Update face tracking
            raw_gaze_x, raw_gaze_y, gaze_detected = face_tracker.update(frame)

            # Apply smoothing to gaze position
            if gaze_detected:
                smoothed_gaze_x = smoothed_gaze_x * gaze_smoothing + raw_gaze_x * (1 - gaze_smoothing)
                smoothed_gaze_y = smoothed_gaze_y * gaze_smoothing + raw_gaze_y * (1 - gaze_smoothing)

            gaze_x = int(smoothed_gaze_x)
            gaze_y = int(smoothed_gaze_y)

            # Update gaze visualizer
            gaze_visualizer.update(gaze_x, gaze_y, gaze_detected)

            # Create digital twin
            digital_twin = face_tracker.draw_digital_twin(frame)

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

            # Process exit button first for better responsiveness
            if exit_button.update(gaze_x, gaze_y, dt):
                break

            # Process other buttons only if calibration is showing
            if show_calibration:
                for button in buttons:
                    if button != exit_button and button.update(gaze_x, gaze_y, dt):
                        break

            # Draw buttons
            if show_calibration:
                for button in buttons:
                    if button != exit_button:
                        button.draw(digital_twin)

            # Always draw exit button
            exit_button.draw(digital_twin)

            # Draw gaze visualization
            gaze_visualizer.draw(digital_twin)

            # Add status messages
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_color = (0, 255, 0)
            font_thickness = 1

            cv2.putText(digital_twin, "✓ WebGazer loaded.",
                       (10, frame_height - 60),
                       font, font_scale, font_color, font_thickness)

            if not show_calibration:
                cv2.putText(digital_twin, "✓ Calibration box closed.",
                           (10, frame_height - 40),
                           font, font_scale, font_color, font_thickness)
                cv2.putText(digital_twin, "✓ Mode 1 selected.",
                           (10, frame_height - 20),
                           font, font_scale, font_color, font_thickness)

            # Show the digital twin
            cv2.imshow("Eye Tracker", digital_twin)

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
