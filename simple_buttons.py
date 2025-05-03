#!/usr/bin/env python3
# simple_buttons.py — PRF‑SIMPLE‑BUTTONS‑2025‑05‑02
# Description: Simple buttons matching the ChatGPT reference image
# Status: ✅ PRF‑COMPLIANT

import cv2
import numpy as np
import time
import random

# Create a window
window_name = "Simple Buttons"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 800, 600)

# Create a black canvas
canvas = np.zeros((600, 800, 3), dtype=np.uint8)

# Button properties
button_width = 300
button_height = 50
button_bg_color = (45, 45, 45)  # Dark gray
button_border_color = (100, 100, 100)  # Light gray
button_text_color = (255, 255, 255)  # White
button_hover_color = (60, 60, 60)  # Slightly lighter gray

# Progress bar colors
progress_colors = {
    "mode1": (246, 130, 59),  # Blue (BGR)
    "mode2": (246, 92, 139),  # Purple (BGR)
    "mode3": (153, 76, 236),  # Pink (BGR)
    "exit": (0, 0, 200)       # Red (BGR)
}

# Button positions
buttons = {
    "exit": {"x": 10, "y": 10, "width": 120, "height": 50, "text": "EXIT", "hover": False, "dwell": 0},
    "mode1": {"x": 250, "y": 150, "width": button_width, "height": button_height, "text": "Mode 1 (Haar Eye)", "hover": False, "dwell": 0},
    "mode2": {"x": 250, "y": 220, "width": button_width, "height": button_height, "text": "Mode 2 (DNN Face)", "hover": False, "dwell": 0},
    "mode3": {"x": 250, "y": 290, "width": button_width, "height": button_height, "text": "Mode 3 (Nobara)", "hover": False, "dwell": 0}
}

# Draw panel
panel_x = 230
panel_y = 100
panel_width = 340
panel_height = 260

# Simulated gaze position
gaze_x, gaze_y = 400, 300
last_time = time.time()

# Main loop
running = True
while running:
    # Create a fresh canvas
    canvas = np.zeros((600, 800, 3), dtype=np.uint8)
    
    # Calculate time delta
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time
    
    # Update simulated gaze position
    gaze_x += random.randint(-5, 5)
    gaze_y += random.randint(-5, 5)
    gaze_x = max(0, min(800, gaze_x))
    gaze_y = max(0, min(600, gaze_y))
    
    # Draw panel
    cv2.rectangle(canvas, (panel_x, panel_y), (panel_x + panel_width, panel_y + panel_height), (30, 30, 30), -1)
    cv2.rectangle(canvas, (panel_x, panel_y), (panel_x + panel_width, panel_y + panel_height), (80, 80, 80), 1)
    
    # Draw panel title
    cv2.putText(canvas, "Calibration Options", (panel_x + 70, panel_y + 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Draw buttons
    for name, button in buttons.items():
        x, y = button["x"], button["y"]
        w, h = button["width"], button["height"]
        text = button["text"]
        
        # Check if gaze is on button
        margin = 20
        if (x - margin <= gaze_x <= x + w + margin and
            y - margin <= gaze_y <= y + h + margin):
            button["hover"] = True
            button["dwell"] += dt
            bg_color = button_hover_color
        else:
            button["hover"] = False
            button["dwell"] = 0
            bg_color = button_bg_color
        
        # Draw button background
        cv2.rectangle(canvas, (x, y), (x + w, y + h), bg_color, -1)
        
        # Draw button border
        cv2.rectangle(canvas, (x, y), (x + w, y + h), button_border_color, 1)
        
        # Draw button text
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        text_x = x + (w - text_size[0]) // 2
        text_y = y + (h + text_size[1]) // 2
        cv2.putText(canvas, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, button_text_color, 2)
        
        # Draw progress bar if hovering
        if button["hover"] and button["dwell"] > 0:
            dwell_threshold = 1.0  # seconds
            progress = min(1.0, button["dwell"] / dwell_threshold)
            progress_width = int(w * progress)
            
            # Get progress color for this button
            progress_color = progress_colors.get(name, (0, 255, 0))
            
            # Draw progress bar
            cv2.rectangle(canvas, (x, y + h - 4), (x + progress_width, y + h), progress_color, -1)
            
            # Check if dwell is complete
            if progress >= 1.0:
                if name == "exit":
                    running = False
                else:
                    print(f"Selected: {name}")
                    # Reset dwell
                    button["dwell"] = 0
    
    # Draw gaze indicator
    cv2.circle(canvas, (gaze_x, gaze_y), 10, (0, 255, 0), -1)
    cv2.circle(canvas, (gaze_x, gaze_y), 5, (255, 255, 255), -1)
    
    # Show the canvas
    cv2.imshow(window_name, canvas)
    
    # Check for key press
    key = cv2.waitKey(16)  # ~60 FPS
    if key == 27:  # ESC key
        running = False

# Clean up
cv2.destroyAllWindows()
print("Done")
