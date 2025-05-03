#!/usr/bin/env python3
# refind_style_buttons.py — PRF‑REFIND‑BUTTONS‑2025‑05‑02
# Description: rEFInd-style buttons matching the ChatGPT reference image
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import tkinter as tk
from tkinter import font
import threading
import time
import json
import logging
import websocket
import math
import random
from datetime import datetime

# === Logging Setup ===
def setup_logging():
    """Set up logging to file and console"""
    log_dir = "/tmp"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/refind_style_buttons_{timestamp}.log"
    
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

# === Boot Entries ===
def get_boot_entries():
    """Get boot entries with icons"""
    return [
        {
            "name": "Linux",
            "command": "linux",
            "icon": "🐧"
        },
        {
            "name": "Windows",
            "command": "windows",
            "icon": "🪟"
        },
        {
            "name": "Recovery",
            "command": "recovery",
            "icon": "🔧"
        },
        {
            "name": "Fix GRUB",
            "command": "fix_grub",
            "icon": "🛠️"
        },
        {
            "name": "UEFI Setup",
            "command": "uefi",
            "icon": "⚙️"
        }
    ]

# === Main Application ===
class RefindStyleButtons:
    """rEFInd-style buttons matching the ChatGPT reference image"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("rEFInd Style Buttons")
        
        # Make fullscreen
        self.root.attributes("-fullscreen", True)
        
        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Create a background canvas
        self.bg_canvas = tk.Canvas(
            self.root,
            bg="#000000",
            highlightthickness=0
        )
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Draw background
        self.draw_background()
        
        # Create a frame for content
        self.frame = tk.Frame(self.root, bg="#000000")
        self.frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Get boot entries
        self.boot_entries = get_boot_entries()
        
        # Create buttons
        self.buttons = []
        self.create_buttons()
        
        # Gaze tracking variables
        self.last_x = None
        self.last_y = None
        self.dwell_start_time = None
        self.dwell_position = None
        self.dwell_button = None
        self.gaze_indicator = None
        
        # Create a gaze indicator
        self.create_gaze_indicator()
        
        # Add a status bar at the bottom
        self.status_frame = tk.Frame(self.root, bg="#000000", height=30)
        self.status_frame.pack(side="bottom", fill="x")
        
        self.status_label = tk.Label(
            self.status_frame,
            text="rEFInd Style Buttons | Connected to eye tracker | Press ESC to exit",
            font=("Helvetica", 10),
            fg="#AAAAAA",
            bg="#000000",
            anchor="w",
            padx=10
        )
        self.status_label.pack(side="left", fill="x")
        
        # Add version and credits
        self.version_label = tk.Label(
            self.status_frame,
            text="v1.0 | PRF‑REFIND‑BUTTONS‑2025‑05‑02",
            font=("Helvetica", 10),
            fg="#AAAAAA",
            bg="#000000",
            anchor="e",
            padx=10
        )
        self.version_label.pack(side="right")
        
        # Start WebSocket connection in a separate thread
        self.ws = None
        self.running = True
        threading.Thread(target=self._connect_websocket, daemon=True).start()
        
        # Add key bindings for exit
        self.root.bind("<Escape>", self.exit)
        self.root.bind("q", self.exit)
        
        # Update loop
        self.update_ui()
    
    def draw_background(self):
        """Draw a gradient background"""
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        
        # Configure canvas size
        self.bg_canvas.config(width=width, height=height)
        
        # Define gradient colors
        top_color = "#000000"
        bottom_color = "#1A1A1A"
        
        # Draw gradient rectangles
        for i in range(height):
            # Calculate color for this line
            ratio = i / height
            r = int(int(top_color[1:3], 16) * (1 - ratio) + int(bottom_color[1:3], 16) * ratio)
            g = int(int(top_color[3:5], 16) * (1 - ratio) + int(bottom_color[3:5], 16) * ratio)
            b = int(int(top_color[5:7], 16) * (1 - ratio) + int(bottom_color[5:7], 16) * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            
            self.bg_canvas.create_line(0, i, width, i, fill=color)
        
        # Add a subtle grid pattern
        grid_spacing = 50
        grid_color = "#222222"
        
        for x in range(0, width, grid_spacing):
            self.bg_canvas.create_line(x, 0, x, height, fill=grid_color, width=1)
        
        for y in range(0, height, grid_spacing):
            self.bg_canvas.create_line(0, y, width, y, fill=grid_color, width=1)
    
    def create_buttons(self):
        """Create buttons matching the ChatGPT reference image"""
        # Calculate grid dimensions
        num_entries = len(self.boot_entries)
        cols = min(3, num_entries)
        rows = (num_entries + cols - 1) // cols
        
        # Create custom fonts
        title_font = font.Font(family="Helvetica", size=32, weight="bold")
        button_font = font.Font(family="Helvetica", size=24, weight="bold")
        subtitle_font = font.Font(family="Helvetica", size=12)
        
        # Add a title at the top
        title_frame = tk.Frame(self.frame, bg="#000000", padx=20, pady=20)
        title_frame.grid(row=0, column=0, columnspan=cols, padx=20, pady=20, sticky="ew")
        
        title_label = tk.Label(
            title_frame,
            text="Boot Menu",
            font=title_font,
            fg="#FFFFFF",
            bg="#000000"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Select an option with your gaze - Dwell to activate",
            font=subtitle_font,
            fg="#CCCCCC",
            bg="#000000"
        )
        subtitle_label.pack()
        
        # Create buttons with styles matching the ChatGPT reference image
        for i, entry in enumerate(self.boot_entries):
            row = (i // cols) + 1  # +1 to account for title
            col = i % cols
            
            # Create a frame for the button
            frame = tk.Frame(self.frame, bg="#000000", padx=15, pady=15)
            frame.grid(row=row, column=col, padx=25, pady=25)
            
            # Define button styles based on ChatGPT reference image
            styles = {
                "linux": {
                    "bg": "#2D2D2D",  # Dark gray
                    "border": "#666666",  # Light gray
                    "hover": "#4D4D4D",  # Lighter gray
                    "text": "#FFFFFF",  # White
                    "progress": "#3B82F6"  # Blue
                },
                "windows": {
                    "bg": "#2D2D2D",  # Dark gray
                    "border": "#666666",  # Light gray
                    "hover": "#4D4D4D",  # Lighter gray
                    "text": "#FFFFFF",  # White
                    "progress": "#8B5CF6"  # Purple
                },
                "recovery": {
                    "bg": "#2D2D2D",  # Dark gray
                    "border": "#666666",  # Light gray
                    "hover": "#4D4D4D",  # Lighter gray
                    "text": "#FFFFFF",  # White
                    "progress": "#F59E0B"  # Amber
                },
                "fix_grub": {
                    "bg": "#2D2D2D",  # Dark gray
                    "border": "#666666",  # Light gray
                    "hover": "#4D4D4D",  # Lighter gray
                    "text": "#FFFFFF",  # White
                    "progress": "#EC4899"  # Pink
                },
                "uefi": {
                    "bg": "#2D2D2D",  # Dark gray
                    "border": "#666666",  # Light gray
                    "hover": "#4D4D4D",  # Lighter gray
                    "text": "#FFFFFF",  # White
                    "progress": "#10B981"  # Green
                }
            }
            
            # Get style for this entry
            cmd = entry["command"]
            style = styles.get(cmd, {
                "bg": "#2D2D2D",  # Dark gray
                "border": "#666666",  # Light gray
                "hover": "#4D4D4D",  # Lighter gray
                "text": "#FFFFFF",  # White
                "progress": "#8B5CF6"  # Purple (default)
            })
            
            # Create a canvas for the button
            button_width = 300
            button_height = 50  # Shorter height to match ChatGPT image
            button_canvas = tk.Canvas(
                frame,
                width=button_width,
                height=button_height,
                bg=style["bg"],
                highlightthickness=1,
                highlightbackground=style["border"]
            )
            button_canvas.pack(fill="both", expand=True)
            
            # Draw button text
            button_canvas.create_text(
                button_width // 2,
                button_height // 2,
                text=entry['name'],
                font=("Helvetica", 14),
                fill=style["text"]
            )
            
            # Make the canvas clickable
            button_canvas.bind("<Button-1>", lambda e, cmd=entry["command"]: self.select_boot_option(cmd))
            
            # Add hover effect
            def on_enter(e, canvas=button_canvas, style=style):
                canvas.config(bg=style["hover"])
            
            def on_leave(e, canvas=button_canvas, style=style):
                canvas.config(bg=style["bg"])
            
            button_canvas.bind("<Enter>", on_enter)
            button_canvas.bind("<Leave>", on_leave)
            
            # Store button reference
            self.buttons.append({
                "button": button_canvas,
                "entry": entry,
                "frame": frame,
                "style": style,
                "width": button_width,
                "height": button_height
            })
    
    def create_gaze_indicator(self):
        """Create a gaze indicator"""
        # Create a visible indicator
        indicator_size = 30
        self.gaze_indicator = tk.Canvas(
            self.root,
            width=indicator_size,
            height=indicator_size,
            bg="black",
            highlightthickness=0
        )
        self.gaze_indicator.place(x=0, y=0)
        
        # Create outer circle
        self.gaze_outer = self.gaze_indicator.create_oval(
            2, 2,
            indicator_size - 2, indicator_size - 2,
            outline="#00FF00",
            width=2,
            fill=""
        )
        
        # Create inner circle
        inner_padding = 8
        self.gaze_inner = self.gaze_indicator.create_oval(
            inner_padding,
            inner_padding,
            indicator_size - inner_padding,
            indicator_size - inner_padding,
            outline="#FFFFFF",
            width=1,
            fill=""
        )
        
        # Create a progress arc (initially empty)
        self.gaze_progress = self.gaze_indicator.create_arc(
            inner_padding,
            inner_padding,
            indicator_size - inner_padding,
            indicator_size - inner_padding,
            start=90,
            extent=0,
            outline="",
            fill="#00FF00"
        )
    
    def update_gaze_indicator(self, x, y, progress=0):
        """Update the gaze indicator position and progress"""
        if x is None or y is None:
            return
        
        # Get indicator size
        indicator_size = 30
        
        # Update position (center the indicator on the gaze point)
        self.gaze_indicator.place(x=x-(indicator_size/2), y=y-(indicator_size/2))
        
        # Update progress arc
        extent = 360 * progress
        self.gaze_indicator.itemconfig(
            self.gaze_progress,
            extent=extent
        )
    
    def _connect_websocket(self):
        """Connect to WebSocket server for gaze data"""
        ws_url = "ws://localhost:8765"
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if "x" in data and "y" in data:
                    self.last_x = data["x"]
                    self.last_y = data["y"]
            except Exception as e:
                log(f"Error processing message: {e}")
        
        def on_error(ws, error):
            log(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            log("WebSocket connection closed")
            if self.running:
                # Try to reconnect after a delay
                time.sleep(2)
                self._connect_websocket()
        
        def on_open(ws):
            log("WebSocket connection established")
        
        # Create WebSocket connection
        try:
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            self.ws.run_forever()
        except Exception as e:
            log(f"Failed to connect to WebSocket: {e}")
            # Use simulated gaze data for testing
            self._simulate_gaze_data()
    
    def _simulate_gaze_data(self):
        """Simulate gaze data for testing"""
        log("Using simulated gaze data")
        
        def update_gaze():
            while self.running:
                # Simulate smooth movement
                if self.last_x is None or self.last_y is None:
                    self.last_x = self.screen_width // 2
                    self.last_y = self.screen_height // 2
                
                # Add some random movement
                self.last_x += random.randint(-5, 5)
                self.last_y += random.randint(-5, 5)
                
                # Keep within screen bounds
                self.last_x = max(0, min(self.screen_width, self.last_x))
                self.last_y = max(0, min(self.screen_height, self.last_y))
                
                time.sleep(0.05)
        
        # Start simulation in a separate thread
        threading.Thread(target=update_gaze, daemon=True).start()
    
    def update_ui(self):
        """Update UI based on gaze position"""
        if not self.running:
            return
        
        # Check if we have gaze data
        if self.last_x is not None and self.last_y is not None:
            x, y = self.last_x, self.last_y
            
            # Check if gaze is on a button
            hovered_button = None
            for button_info in self.buttons:
                button = button_info["button"]
                
                # Get button position in screen coordinates
                button_x = button.winfo_rootx()
                button_y = button.winfo_rooty()
                button_width = button_info["width"]
                button_height = button_info["height"]
                
                # Add margin for easier selection
                margin = 20
                if (button_x - margin <= x <= button_x + button_width + margin and
                    button_y - margin <= y <= button_y + button_height + margin):
                    hovered_button = button_info
                    break
            
            # Handle dwell selection
            if hovered_button:
                # If we just started hovering over this button
                if self.dwell_button != hovered_button:
                    self.dwell_button = hovered_button
                    self.dwell_start_time = time.time()
                    self.dwell_position = (x, y)
                else:
                    # Continue dwelling on the same button
                    dwell_time = time.time() - self.dwell_start_time
                    dwell_threshold = 1.0  # seconds
                    
                    # Calculate progress
                    progress = min(1.0, dwell_time / dwell_threshold)
                    
                    # Update gaze indicator with progress
                    self.update_gaze_indicator(x, y, progress)
                    
                    # Draw progress bar on button
                    button = hovered_button["button"]
                    style = hovered_button["style"]
                    width = hovered_button["width"]
                    height = hovered_button["height"]
                    
                    # Clear previous progress bar
                    button.delete("progress")
                    
                    # Draw new progress bar
                    progress_width = int(width * progress)
                    button.create_rectangle(
                        0, height - 4,
                        progress_width, height,
                        fill=style["progress"],
                        tags="progress"
                    )
                    
                    # Check if dwell is complete
                    if progress >= 1.0:
                        # Select this option
                        self.select_boot_option(hovered_button["entry"]["command"])
                        
                        # Reset dwell
                        self.dwell_button = None
                        self.dwell_start_time = None
                        self.dwell_position = None
            else:
                # Not hovering over any button
                self.dwell_button = None
                self.dwell_start_time = None
                self.dwell_position = None
                
                # Just update gaze indicator position
                self.update_gaze_indicator(x, y)
        
        # Schedule next update
        self.root.after(16, self.update_ui)  # ~60 FPS
    
    def select_boot_option(self, command):
        """Select a boot option"""
        log(f"Selected boot option: {command}")
        
        # Find the selected button
        selected_button_info = None
        for button_info in self.buttons:
            if button_info["entry"]["command"] == command:
                selected_button_info = button_info
                break
        
        if selected_button_info:
            # Highlight the selected button
            button = selected_button_info["button"]
            style = selected_button_info["style"]
            
            # Create a pulsing effect
            def pulse_animation(count=0, max_count=5):
                if count >= max_count:
                    # Animation complete, proceed to boot
                    self.show_boot_message(command)
                    return
                
                # Toggle between normal and highlight colors
                if count % 2 == 0:
                    button.config(bg=style["hover"])
                else:
                    button.config(bg=style["bg"])
                
                # Schedule next pulse
                self.root.after(200, lambda: pulse_animation(count + 1, max_count))
            
            # Start the animation
            pulse_animation()
        else:
            # If button not found, just show the boot message
            self.show_boot_message(command)
    
    def show_boot_message(self, command):
        """Show boot message and exit"""
        # Create a fullscreen message
        message_frame = tk.Frame(self.root, bg="#000000")
        message_frame.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Add boot message
        message_label = tk.Label(
            message_frame,
            text=f"Booting into: {command}...",
            font=("Helvetica", 36, "bold"),
            fg="#FFFFFF",
            bg="#000000"
        )
        message_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Exit after a delay
        self.root.after(2000, self.exit)
    
    def exit(self, event=None):
        """Exit the application"""
        log("Exiting application")
        self.running = False
        if self.ws:
            self.ws.close()
        self.root.destroy()

# === Main Function ===
def main():
    """Main function"""
    log("Starting rEFInd Style Buttons")
    
    # Create Tkinter root
    root = tk.Tk()
    
    # Create application
    app = RefindStyleButtons(root)
    
    # Start Tkinter main loop
    root.mainloop()

if __name__ == "__main__":
    main()
