#!/usr/bin/env python3
# exact_match_buttons.py — PRF‑EXACT‑MATCH‑BUTTONS‑2025‑05‑02
# Description: Buttons exactly matching the ChatGPT reference image
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import tkinter as tk
from tkinter import font
import threading
import time
import json
import logging
import math
import random
from datetime import datetime
import cv2
import numpy as np
from PIL import Image, ImageTk

# === Logging Setup ===
def setup_logging():
    """Set up logging to file and console"""
    log_dir = "/tmp"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/exact_match_buttons_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return log_file

# Initialize logging
log_file = setup_logging()

def log(message):
    """Log a message to both console and log file"""
    logging.info(message)

# === Main Application ===
class ExactMatchButtons:
    """Buttons exactly matching the ChatGPT reference image"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Exact Match Buttons")
        
        # Set window size
        self.root.geometry("800x600")
        
        # Create a black background
        self.bg_frame = tk.Frame(self.root, bg="#000000")
        self.bg_frame.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Create a frame for the buttons
        self.button_frame = tk.Frame(self.bg_frame, bg="#000000")
        self.button_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Create title
        self.title_label = tk.Label(
            self.button_frame,
            text="Calibration Options",
            font=("Helvetica", 16),
            fg="#FFFFFF",
            bg="#000000"
        )
        self.title_label.pack(pady=(0, 20))
        
        # Create buttons
        self.buttons = []
        self.create_buttons()
        
        # Add exit button
        self.create_exit_button()
        
        # Gaze tracking variables
        self.gaze_x = None
        self.gaze_y = None
        self.dwell_start_time = None
        self.dwell_button = None
        
        # Create gaze indicator
        self.gaze_indicator = self.create_gaze_indicator()
        
        # Start simulated gaze movement
        self.running = True
        threading.Thread(target=self.simulate_gaze, daemon=True).start()
        
        # Add key bindings for exit
        self.root.bind("<Escape>", self.exit)
        self.root.bind("q", self.exit)
        
        # Start update loop
        self.update_ui()
    
    def create_buttons(self):
        """Create buttons exactly matching the reference image"""
        # Button styles from the reference image
        button_styles = [
            {
                "text": "Mode 1 (Haar Eye)",
                "bg": "#2D2D2D",
                "border": "#666666",
                "hover": "#3D3D3D",
                "progress": "#3B82F6"  # Blue
            },
            {
                "text": "Mode 2 (DNN Face)",
                "bg": "#2D2D2D",
                "border": "#666666",
                "hover": "#3D3D3D",
                "progress": "#8B5CF6"  # Purple
            },
            {
                "text": "Mode 3 (Nobara)",
                "bg": "#2D2D2D",
                "border": "#666666",
                "hover": "#3D3D3D",
                "progress": "#EC4899"  # Pink
            }
        ]
        
        # Create each button
        for i, style in enumerate(button_styles):
            # Create a frame for the button
            button_frame = tk.Frame(
                self.button_frame,
                bg=style["border"],
                padx=1,
                pady=1
            )
            button_frame.pack(pady=10)
            
            # Create the button
            button_width = 300
            button_height = 50
            
            # Create a canvas for the button
            button = tk.Canvas(
                button_frame,
                width=button_width,
                height=button_height,
                bg=style["bg"],
                highlightthickness=0
            )
            button.pack()
            
            # Add text to the button
            button.create_text(
                button_width // 2,
                button_height // 2,
                text=style["text"],
                fill="#FFFFFF",
                font=("Helvetica", 12)
            )
            
            # Store button info
            self.buttons.append({
                "button": button,
                "frame": button_frame,
                "style": style,
                "width": button_width,
                "height": button_height,
                "progress": None
            })
            
            # Add hover effect
            def on_enter(e, button=button, style=style):
                button.config(bg=style["hover"])
            
            def on_leave(e, button=button, style=style):
                button.config(bg=style["bg"])
            
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
    
    def create_exit_button(self):
        """Create an exit button matching the reference image"""
        # Exit button style
        exit_style = {
            "text": "EXIT",
            "bg": "#2D2D2D",
            "border": "#666666",
            "hover": "#3D3D3D",
            "progress": "#EF4444"  # Red
        }
        
        # Create a frame for the button
        exit_frame = tk.Frame(
            self.root,
            bg=exit_style["border"],
            padx=1,
            pady=1
        )
        exit_frame.place(x=10, y=10)
        
        # Create the button
        button_width = 120
        button_height = 50
        
        # Create a canvas for the button
        exit_button = tk.Canvas(
            exit_frame,
            width=button_width,
            height=button_height,
            bg=exit_style["bg"],
            highlightthickness=0
        )
        exit_button.pack()
        
        # Add text to the button
        exit_button.create_text(
            button_width // 2,
            button_height // 2,
            text=exit_style["text"],
            fill="#FFFFFF",
            font=("Helvetica", 12, "bold")
        )
        
        # Store button info
        self.exit_button = {
            "button": exit_button,
            "frame": exit_frame,
            "style": exit_style,
            "width": button_width,
            "height": button_height,
            "progress": None
        }
        
        # Add hover effect
        def on_enter(e):
            exit_button.config(bg=exit_style["hover"])
        
        def on_leave(e):
            exit_button.config(bg=exit_style["bg"])
        
        exit_button.bind("<Enter>", on_enter)
        exit_button.bind("<Leave>", on_leave)
        
        # Add click event
        exit_button.bind("<Button-1>", self.exit)
    
    def create_gaze_indicator(self):
        """Create a gaze indicator"""
        # Create a canvas for the gaze indicator
        indicator_size = 30
        indicator = tk.Canvas(
            self.root,
            width=indicator_size,
            height=indicator_size,
            bg="#000000",
            highlightthickness=0
        )
        
        # Create the indicator elements
        outer_circle = indicator.create_oval(
            2, 2,
            indicator_size - 2, indicator_size - 2,
            outline="#00FF00",
            width=2
        )
        
        inner_circle = indicator.create_oval(
            8, 8,
            indicator_size - 8, indicator_size - 8,
            outline="#FFFFFF",
            width=1
        )
        
        # Create progress arc (initially empty)
        progress_arc = indicator.create_arc(
            8, 8,
            indicator_size - 8, indicator_size - 8,
            start=90,
            extent=0,
            outline="",
            fill="#00FF00"
        )
        
        return {
            "canvas": indicator,
            "outer": outer_circle,
            "inner": inner_circle,
            "progress": progress_arc,
            "size": indicator_size
        }
    
    def simulate_gaze(self):
        """Simulate gaze movement for testing"""
        width = self.root.winfo_width() or 800
        height = self.root.winfo_height() or 600
        
        # Start at center
        self.gaze_x = width // 2
        self.gaze_y = height // 2
        
        while self.running:
            # Add some random movement
            self.gaze_x += random.randint(-5, 5)
            self.gaze_y += random.randint(-5, 5)
            
            # Keep within window bounds
            self.gaze_x = max(0, min(width, self.gaze_x))
            self.gaze_y = max(0, min(height, self.gaze_y))
            
            # Sleep to control update rate
            time.sleep(0.05)
    
    def update_ui(self):
        """Update UI based on gaze position"""
        if not self.running:
            return
        
        # Check if we have gaze data
        if self.gaze_x is not None and self.gaze_y is not None:
            x, y = self.gaze_x, self.gaze_y
            
            # Update gaze indicator position
            indicator_size = self.gaze_indicator["size"]
            self.gaze_indicator["canvas"].place(
                x=x - indicator_size // 2,
                y=y - indicator_size // 2
            )
            
            # Check if gaze is on a button
            hovered_button = None
            
            # Check exit button first
            exit_button = self.exit_button
            ex = exit_button["button"].winfo_rootx()
            ey = exit_button["button"].winfo_rooty()
            ew = exit_button["width"]
            eh = exit_button["height"]
            
            # Add margin for easier selection
            margin = 20
            if (ex - margin <= x <= ex + ew + margin and
                ey - margin <= y <= ey + eh + margin):
                hovered_button = exit_button
            
            # Check other buttons
            if not hovered_button:
                for button_info in self.buttons:
                    button = button_info["button"]
                    
                    # Get button position
                    bx = button.winfo_rootx()
                    by = button.winfo_rooty()
                    bw = button_info["width"]
                    bh = button_info["height"]
                    
                    # Add margin for easier selection
                    if (bx - margin <= x <= bx + bw + margin and
                        by - margin <= y <= by + bh + margin):
                        hovered_button = button_info
                        break
            
            # Handle dwell selection
            if hovered_button:
                # If we just started hovering over this button
                if self.dwell_button != hovered_button:
                    self.dwell_button = hovered_button
                    self.dwell_start_time = time.time()
                else:
                    # Continue dwelling on the same button
                    dwell_time = time.time() - self.dwell_start_time
                    dwell_threshold = 1.0  # seconds
                    
                    # Calculate progress
                    progress = min(1.0, dwell_time / dwell_threshold)
                    
                    # Update gaze indicator progress
                    extent = 360 * progress
                    self.gaze_indicator["canvas"].itemconfig(
                        self.gaze_indicator["progress"],
                        extent=extent
                    )
                    
                    # Update button progress bar
                    button = hovered_button["button"]
                    style = hovered_button["style"]
                    width = hovered_button["width"]
                    height = hovered_button["height"]
                    
                    # Remove old progress bar if exists
                    if hovered_button["progress"]:
                        button.delete(hovered_button["progress"])
                    
                    # Draw new progress bar
                    progress_width = int(width * progress)
                    progress_height = 4  # Thin progress bar
                    
                    hovered_button["progress"] = button.create_rectangle(
                        0, height - progress_height,
                        progress_width, height,
                        fill=style["progress"],
                        outline=""
                    )
                    
                    # Check if dwell is complete
                    if progress >= 1.0:
                        # Activate button
                        self.activate_button(hovered_button)
                        
                        # Reset dwell
                        self.dwell_button = None
                        self.dwell_start_time = None
            else:
                # Not hovering over any button
                self.dwell_button = None
                self.dwell_start_time = None
                
                # Reset gaze indicator progress
                self.gaze_indicator["canvas"].itemconfig(
                    self.gaze_indicator["progress"],
                    extent=0
                )
                
                # Clear all progress bars
                for button_info in self.buttons + [self.exit_button]:
                    if button_info["progress"]:
                        button_info["button"].delete(button_info["progress"])
                        button_info["progress"] = None
        
        # Schedule next update
        self.root.after(16, self.update_ui)  # ~60 FPS
    
    def activate_button(self, button_info):
        """Activate a button"""
        # Get button info
        button = button_info["button"]
        style = button_info["style"]
        
        # Flash the button
        def flash(count=0):
            if count >= 6:  # 3 flashes
                # If it's the exit button, exit the application
                if button_info == self.exit_button:
                    self.exit()
                return
            
            # Toggle button color
            if count % 2 == 0:
                button.config(bg=style["hover"])
            else:
                button.config(bg=style["bg"])
            
            # Schedule next flash
            self.root.after(100, lambda: flash(count + 1))
        
        # Start flashing
        flash()
    
    def exit(self, event=None):
        """Exit the application"""
        self.running = False
        self.root.destroy()

# === Main Function ===
def main():
    """Main function"""
    # Create Tkinter root
    root = tk.Tk()
    
    # Create application
    app = ExactMatchButtons(root)
    
    # Start Tkinter main loop
    root.mainloop()

if __name__ == "__main__":
    main()
