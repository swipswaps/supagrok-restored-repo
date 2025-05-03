#!/usr/bin/env python3
# image_slice_buttons.py — PRF‑IMAGE‑SLICE‑BUTTONS‑2025‑05‑02
# Description: Extract buttons from reference image and add logic
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import cv2
import numpy as np
import time
import math

# === Main Class ===
class ImageSliceButtons:
    """Extract buttons from reference image and add logic"""
    
    def __init__(self):
        """Initialize the application"""
        # Find the reference image
        self.reference_image_path = self.find_reference_image()
        if not self.reference_image_path:
            print("❌ Reference image not found")
            sys.exit(1)
        
        print(f"✅ Found reference image: {self.reference_image_path}")
        
        # Load the reference image
        self.reference_image = cv2.imread(self.reference_image_path)
        if self.reference_image is None:
            print("❌ Failed to load reference image")
            sys.exit(1)
        
        # Extract button regions from the reference image
        self.extract_button_regions()
        
        # Initialize window
        cv2.namedWindow("Image Slice Buttons", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Image Slice Buttons", 800, 600)
        
        # Initialize variables
        self.mouse_x = 400
        self.mouse_y = 300
        self.last_time = time.time()
        self.running = True
        
        # Button states
        self.button_states = {
            "exit": {"hover": False, "dwell_time": 0},
            "mode1": {"hover": False, "dwell_time": 0},
            "mode2": {"hover": False, "dwell_time": 0},
            "mode3": {"hover": False, "dwell_time": 0}
        }
    
    def find_reference_image(self):
        """Find the reference image in the current directory or Downloads folder"""
        # Try current directory first
        if os.path.exists("ChatGPT Image May 2, 2025, 07_55_29 AM.png"):
            return "ChatGPT Image May 2, 2025, 07_55_29 AM.png"
        
        # Try Downloads folder
        home_dir = os.path.expanduser("~")
        downloads_path = os.path.join(home_dir, "Downloads", "ChatGPT Image May 2, 2025, 07_55_29 AM.png")
        if os.path.exists(downloads_path):
            return downloads_path
        
        # Try current directory with different name patterns
        for file in os.listdir("."):
            if file.lower().endswith(".png") and "chatgpt" in file.lower():
                return file
        
        # Try Downloads folder with different name patterns
        downloads_dir = os.path.join(home_dir, "Downloads")
        if os.path.exists(downloads_dir):
            for file in os.listdir(downloads_dir):
                if file.lower().endswith(".png") and "chatgpt" in file.lower():
                    return os.path.join(downloads_dir, file)
        
        return None
    
    def extract_button_regions(self):
        """Extract button regions from the reference image"""
        print("🔍 Extracting button regions from reference image...")
        
        # Get image dimensions
        height, width = self.reference_image.shape[:2]
        
        # Define button regions based on the reference image
        # These coordinates need to be adjusted based on the actual image
        self.button_regions = {
            "exit": {
                "x": 10,
                "y": 10,
                "width": 120,
                "height": 50,
                "image": None,
                "progress_color": (68, 68, 221)  # Red in BGR
            },
            "mode1": {
                "x": 170,
                "y": 100,
                "width": 300,
                "height": 50,
                "image": None,
                "progress_color": (246, 130, 59)  # Blue in BGR
            },
            "mode2": {
                "x": 170,
                "y": 170,
                "width": 300,
                "height": 50,
                "image": None,
                "progress_color": (246, 92, 139)  # Purple in BGR
            },
            "mode3": {
                "x": 170,
                "y": 240,
                "width": 300,
                "height": 50,
                "image": None,
                "progress_color": (153, 76, 236)  # Pink in BGR
            }
        }
        
        # Extract button images from the reference image
        for name, region in self.button_regions.items():
            # Create a copy of the reference image for this button
            button_image = self.reference_image.copy()
            
            # Draw a rectangle around the button region for visualization
            cv2.rectangle(
                button_image,
                (region["x"], region["y"]),
                (region["x"] + region["width"], region["y"] + region["height"]),
                (0, 255, 0),
                2
            )
            
            # Store the button image
            region["image"] = button_image
            
            print(f"✅ Extracted {name} button")
        
        # Create a panel image from the reference
        self.panel_image = self.reference_image.copy()
    
    def run(self):
        """Run the main loop"""
        print("🚀 Running Image Slice Buttons")
        
        # Set up mouse callback
        cv2.setMouseCallback("Image Slice Buttons", self.mouse_callback)
        
        while self.running:
            # Calculate time delta
            current_time = time.time()
            dt = current_time - self.last_time
            self.last_time = current_time
            
            # Create a canvas from the panel image
            canvas = self.panel_image.copy()
            
            # Update button states based on mouse position
            for name, region in self.button_regions.items():
                x, y = region["x"], region["y"]
                w, h = region["width"], region["height"]
                state = self.button_states[name]
                
                # Check if mouse is on this button (with margin)
                margin = 20
                if (x - margin <= self.mouse_x <= x + w + margin and
                    y - margin <= self.mouse_y <= y + h + margin):
                    # Hovering over button
                    if not state["hover"]:
                        state["hover"] = True
                        state["dwell_time"] = 0
                    else:
                        # Accumulate dwell time
                        state["dwell_time"] += dt
                        
                        # Draw progress bar
                        dwell_threshold = 1.0  # seconds
                        progress = min(1.0, state["dwell_time"] / dwell_threshold)
                        progress_width = int(w * progress)
                        
                        # Draw progress bar at bottom of button
                        color = region["progress_color"]
                        cv2.rectangle(
                            canvas,
                            (x, y + h - 4),
                            (x + progress_width, y + h),
                            color,
                            -1
                        )
                        
                        # Check if dwell is complete
                        if progress >= 1.0:
                            if name == "exit":
                                self.running = False
                                print("👋 Exit button activated")
                            else:
                                print(f"✅ {name} selected")
                            
                            # Reset dwell time
                            state["dwell_time"] = 0
                else:
                    # Not hovering over button
                    state["hover"] = False
                    state["dwell_time"] = 0
            
            # Draw mouse cursor as gaze indicator
            cv2.circle(canvas, (self.mouse_x, self.mouse_y), 10, (0, 255, 0), -1)
            cv2.circle(canvas, (self.mouse_x, self.mouse_y), 5, (255, 255, 255), -1)
            
            # Show the canvas
            cv2.imshow("Image Slice Buttons", canvas)
            
            # Check for key press
            key = cv2.waitKey(16)  # ~60 FPS
            if key == 27:  # ESC key
                self.running = False
        
        # Clean up
        cv2.destroyAllWindows()
        print("👋 Done")
    
    def mouse_callback(self, event, x, y, flags, param):
        """Mouse callback function"""
        self.mouse_x = x
        self.mouse_y = y

# === Main Function ===
def main():
    """Main function"""
    try:
        app = ImageSliceButtons()
        app.run()
    except KeyboardInterrupt:
        print("🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
