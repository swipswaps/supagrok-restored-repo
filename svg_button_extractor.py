#!/usr/bin/env python3
# svg_button_extractor.py — PRF‑SVG‑BUTTON‑EXTRACTOR‑2025‑05‑02
# Description: Extract buttons from reference image as SVG elements
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import cv2
import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET
from xml.dom import minidom

# === SVG Button Extractor Class ===
class SVGButtonExtractor:
    """Extract buttons from reference image as SVG elements"""
    
    def __init__(self):
        """Initialize the extractor"""
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
        
        # Define button regions based on the reference image
        self.define_button_regions()
        
        # Create output directory
        self.output_dir = "svg_buttons"
        os.makedirs(self.output_dir, exist_ok=True)
    
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
            if file.lower().endswith((".png", ".jpg")) and "chatgpt" in file.lower():
                return file
        
        # Try Downloads folder with different name patterns
        downloads_dir = os.path.join(home_dir, "Downloads")
        if os.path.exists(downloads_dir):
            for file in os.listdir(downloads_dir):
                if file.lower().endswith((".png", ".jpg")) and "chatgpt" in file.lower():
                    return os.path.join(downloads_dir, file)
        
        return None
    
    def define_button_regions(self):
        """Define button regions based on the reference image"""
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
                "text": "EXIT",
                "progress_color": "#ef4444"  # Red
            },
            "mode1": {
                "x": 170,
                "y": 100,
                "width": 300,
                "height": 50,
                "text": "Mode 1 (Haar Eye)",
                "progress_color": "#3b82f6"  # Blue
            },
            "mode2": {
                "x": 170,
                "y": 170,
                "width": 300,
                "height": 50,
                "text": "Mode 2 (DNN Face)",
                "progress_color": "#8b5cf6"  # Purple
            },
            "mode3": {
                "x": 170,
                "y": 240,
                "width": 300,
                "height": 50,
                "text": "Mode 3 (Nobara)",
                "progress_color": "#ec4899"  # Pink
            }
        }
        
        # Define panel region
        self.panel_region = {
            "x": 150,
            "y": 50,
            "width": 340,
            "height": 300,
            "title": "Calibration Options"
        }
    
    def extract_button_colors(self, region):
        """Extract button colors from the reference image"""
        x, y, width, height = region["x"], region["y"], region["width"], region["height"]
        
        # Extract button region from the reference image
        button_region = self.reference_image[y:y+height, x:x+width]
        
        # Convert to RGB for better color analysis
        button_rgb = cv2.cvtColor(button_region, cv2.COLOR_BGR2RGB)
        
        # Get dominant colors
        pixels = button_rgb.reshape(-1, 3)
        
        # Get background color (most common color)
        bg_color = self.get_dominant_color(pixels)
        
        # Get border color (look at edges)
        top_edge = button_rgb[0, :, :]
        bottom_edge = button_rgb[-1, :, :]
        left_edge = button_rgb[:, 0, :]
        right_edge = button_rgb[:, -1, :]
        edges = np.vstack([top_edge, bottom_edge, left_edge.reshape(-1, 3), right_edge.reshape(-1, 3)])
        border_color = self.get_dominant_color(edges)
        
        # Get text color (usually white or very light)
        # This is a simplification - in a real implementation, you'd use OCR or more sophisticated methods
        text_color = (255, 255, 255)  # White
        
        return {
            "background": self.rgb_to_hex(bg_color),
            "border": self.rgb_to_hex(border_color),
            "text": self.rgb_to_hex(text_color)
        }
    
    def get_dominant_color(self, pixels):
        """Get the dominant color from a set of pixels"""
        # Simple approach: average the colors
        avg_color = np.mean(pixels, axis=0).astype(int)
        return tuple(avg_color)
    
    def rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex color string"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def create_button_svg(self, name, region):
        """Create SVG for a button"""
        # Extract colors
        colors = self.extract_button_colors(region)
        
        # Create SVG element
        svg = ET.Element("svg")
        svg.set("xmlns", "http://www.w3.org/2000/svg")
        svg.set("width", str(region["width"]))
        svg.set("height", str(region["height"]))
        svg.set("viewBox", f"0 0 {region['width']} {region['height']}")
        
        # Create button background
        rect = ET.SubElement(svg, "rect")
        rect.set("x", "0")
        rect.set("y", "0")
        rect.set("width", str(region["width"]))
        rect.set("height", str(region["height"]))
        rect.set("rx", "0")  # No rounded corners
        rect.set("ry", "0")  # No rounded corners
        rect.set("fill", colors["background"])
        rect.set("stroke", colors["border"])
        rect.set("stroke-width", "1")
        
        # Create text element
        text = ET.SubElement(svg, "text")
        text.set("x", str(region["width"] // 2))
        text.set("y", str(region["height"] // 2))
        text.set("font-family", "Arial, sans-serif")
        text.set("font-size", "16")
        text.set("fill", colors["text"])
        text.set("text-anchor", "middle")
        text.set("dominant-baseline", "middle")
        text.text = region["text"]
        
        # Create progress bar (initially empty)
        progress = ET.SubElement(svg, "rect")
        progress.set("x", "0")
        progress.set("y", str(region["height"] - 4))
        progress.set("width", "0")
        progress.set("height", "4")
        progress.set("fill", region["progress_color"])
        progress.set("class", "progress")
        
        # Convert to string
        rough_string = ET.tostring(svg, "utf-8")
        reparsed = minidom.parseString(rough_string)
        pretty_svg = reparsed.toprettyxml(indent="  ")
        
        # Save to file
        output_path = os.path.join(self.output_dir, f"{name}_button.svg")
        with open(output_path, "w") as f:
            f.write(pretty_svg)
        
        print(f"✅ Created SVG for {name} button: {output_path}")
        
        return output_path
    
    def create_panel_svg(self):
        """Create SVG for the panel"""
        region = self.panel_region
        
        # Create SVG element
        svg = ET.Element("svg")
        svg.set("xmlns", "http://www.w3.org/2000/svg")
        svg.set("width", str(region["width"]))
        svg.set("height", str(region["height"]))
        svg.set("viewBox", f"0 0 {region['width']} {region['height']}")
        
        # Create panel background
        rect = ET.SubElement(svg, "rect")
        rect.set("x", "0")
        rect.set("y", "0")
        rect.set("width", str(region["width"]))
        rect.set("height", str(region["height"]))
        rect.set("rx", "0")  # No rounded corners
        rect.set("ry", "0")  # No rounded corners
        rect.set("fill", "#1a1a1a")  # Dark gray
        rect.set("stroke", "#666666")  # Light gray
        rect.set("stroke-width", "1")
        
        # Create title text
        text = ET.SubElement(svg, "text")
        text.set("x", str(region["width"] // 2))
        text.set("y", "30")
        text.set("font-family", "Arial, sans-serif")
        text.set("font-size", "18")
        text.set("fill", "#ffffff")  # White
        text.set("text-anchor", "middle")
        text.set("dominant-baseline", "middle")
        text.text = region["title"]
        
        # Convert to string
        rough_string = ET.tostring(svg, "utf-8")
        reparsed = minidom.parseString(rough_string)
        pretty_svg = reparsed.toprettyxml(indent="  ")
        
        # Save to file
        output_path = os.path.join(self.output_dir, "panel.svg")
        with open(output_path, "w") as f:
            f.write(pretty_svg)
        
        print(f"✅ Created SVG for panel: {output_path}")
        
        return output_path
    
    def create_html_demo(self):
        """Create HTML demo with the SVG buttons"""
        # Create SVGs for all buttons
        button_svgs = {}
        for name, region in self.button_regions.items():
            button_svgs[name] = self.create_button_svg(name, region)
        
        # Create SVG for panel
        panel_svg = self.create_panel_svg()
        
        # Create HTML file
        html_path = os.path.join(self.output_dir, "buttons_demo.html")
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SVG Button Demo</title>
    <style>
        body {{
            background-color: #000000;
            color: #ffffff;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }}
        
        .panel {{
            position: relative;
            width: {self.panel_region["width"]}px;
            height: {self.panel_region["height"]}px;
        }}
        
        .button {{
            position: absolute;
            cursor: pointer;
        }}
        
        .exit-button {{
            top: 10px;
            left: 10px;
        }}
        
        .mode1-button {{
            top: {self.button_regions["mode1"]["y"] - self.panel_region["y"]}px;
            left: {self.button_regions["mode1"]["x"] - self.panel_region["x"]}px;
        }}
        
        .mode2-button {{
            top: {self.button_regions["mode2"]["y"] - self.panel_region["y"]}px;
            left: {self.button_regions["mode2"]["x"] - self.panel_region["x"]}px;
        }}
        
        .mode3-button {{
            top: {self.button_regions["mode3"]["y"] - self.panel_region["y"]}px;
            left: {self.button_regions["mode3"]["x"] - self.panel_region["x"]}px;
        }}
        
        .progress {{
            transition: width 0.1s linear;
        }}
        
        .gaze-indicator {{
            position: absolute;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            border: 2px solid #00ff00;
            pointer-events: none;
            transform: translate(-50%, -50%);
            z-index: 1000;
        }}
        
        .gaze-indicator::after {{
            content: '';
            position: absolute;
            width: 10px;
            height: 10px;
            background-color: #00ff00;
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}
    </style>
</head>
<body>
    <div class="button exit-button" id="exitButton">
        <object data="exit_button.svg" type="image/svg+xml" width="{self.button_regions["exit"]["width"]}" height="{self.button_regions["exit"]["height"]}"></object>
    </div>
    
    <div class="panel">
        <object data="panel.svg" type="image/svg+xml" width="{self.panel_region["width"]}" height="{self.panel_region["height"]}"></object>
        
        <div class="button mode1-button" id="mode1Button">
            <object data="mode1_button.svg" type="image/svg+xml" width="{self.button_regions["mode1"]["width"]}" height="{self.button_regions["mode1"]["height"]}"></object>
        </div>
        
        <div class="button mode2-button" id="mode2Button">
            <object data="mode2_button.svg" type="image/svg+xml" width="{self.button_regions["mode2"]["width"]}" height="{self.button_regions["mode2"]["height"]}"></object>
        </div>
        
        <div class="button mode3-button" id="mode3Button">
            <object data="mode3_button.svg" type="image/svg+xml" width="{self.button_regions["mode3"]["width"]}" height="{self.button_regions["mode3"]["height"]}"></object>
        </div>
    </div>
    
    <div class="gaze-indicator" id="gazeIndicator"></div>
    
    <script>
        // Wait for SVG objects to load
        document.addEventListener('DOMContentLoaded', function() {{
            // Get SVG documents
            const exitButton = document.querySelector('.exit-button object');
            const mode1Button = document.querySelector('.mode1-button object');
            const mode2Button = document.querySelector('.mode2-button object');
            const mode3Button = document.querySelector('.mode3-button object');
            
            // Wait for SVG documents to load
            exitButton.addEventListener('load', function() {{
                initButton(exitButton, 'exit');
            }});
            
            mode1Button.addEventListener('load', function() {{
                initButton(mode1Button, 'mode1');
            }});
            
            mode2Button.addEventListener('load', function() {{
                initButton(mode2Button, 'mode2');
            }});
            
            mode3Button.addEventListener('load', function() {{
                initButton(mode3Button, 'mode3');
            }});
            
            // Initialize gaze tracking
            initGazeTracking();
        }});
        
        // Button states
        const buttonStates = {{
            'exit': {{ hover: false, dwellTime: 0 }},
            'mode1': {{ hover: false, dwellTime: 0 }},
            'mode2': {{ hover: false, dwellTime: 0 }},
            'mode3': {{ hover: false, dwellTime: 0 }}
        }};
        
        // Button references
        const buttons = {{}};
        
        // Initialize button
        function initButton(buttonObj, name) {{
            const svgDoc = buttonObj.contentDocument;
            const progressBar = svgDoc.querySelector('.progress');
            
            buttons[name] = {{
                element: buttonObj,
                progress: progressBar
            }};
        }}
        
        // Initialize gaze tracking
        function initGazeTracking() {{
            const gazeIndicator = document.getElementById('gazeIndicator');
            let mouseX = 0;
            let mouseY = 0;
            let lastTime = Date.now();
            const dwellThreshold = 1000; // 1 second
            
            // Use mouse position as simulated gaze
            document.addEventListener('mousemove', (e) => {{
                mouseX = e.clientX;
                mouseY = e.clientY;
                
                // Update gaze indicator position
                gazeIndicator.style.left = mouseX + 'px';
                gazeIndicator.style.top = mouseY + 'px';
            }});
            
            // Main update loop
            function update() {{
                const currentTime = Date.now();
                const dt = currentTime - lastTime;
                lastTime = currentTime;
                
                // Check if all buttons are loaded
                if (Object.keys(buttons).length < 4) {{
                    requestAnimationFrame(update);
                    return;
                }}
                
                // Check if gaze is on a button
                let isHovering = false;
                
                for (const [name, button] of Object.entries(buttons)) {{
                    const rect = button.element.getBoundingClientRect();
                    
                    // Add margin for easier selection
                    const margin = 20;
                    if (mouseX >= rect.left - margin && 
                        mouseX <= rect.right + margin && 
                        mouseY >= rect.top - margin && 
                        mouseY <= rect.bottom + margin) {{
                        
                        isHovering = true;
                        
                        // If we just started hovering over this button
                        if (!buttonStates[name].hover) {{
                            buttonStates[name].hover = true;
                            buttonStates[name].dwellTime = 0;
                        }} else {{
                            // Continue dwelling on the same button
                            buttonStates[name].dwellTime += dt;
                            
                            // Calculate progress
                            const progress = Math.min(100, (buttonStates[name].dwellTime / dwellThreshold) * 100);
                            const progressWidth = (progress / 100) * parseInt(button.progress.getAttribute('width').baseVal.value);
                            
                            // Update progress bar
                            button.progress.setAttribute('width', progressWidth);
                            
                            // Check if dwell is complete
                            if (buttonStates[name].dwellTime >= dwellThreshold) {{
                                // Button activated
                                if (name === 'exit') {{
                                    alert('EXIT button activated');
                                }} else {{
                                    alert(name + ' button selected');
                                }}
                                
                                // Reset dwell
                                buttonStates[name].dwellTime = 0;
                                button.progress.setAttribute('width', '0');
                            }}
                        }}
                        
                        break;
                    }} else {{
                        // Not hovering over this button
                        buttonStates[name].hover = false;
                        buttonStates[name].dwellTime = 0;
                        button.progress.setAttribute('width', '0');
                    }}
                }}
                
                // If not hovering over any button
                if (!isHovering) {{
                    for (const [name, state] of Object.entries(buttonStates)) {{
                        state.hover = false;
                        state.dwellTime = 0;
                        buttons[name].progress.setAttribute('width', '0');
                    }}
                }}
                
                requestAnimationFrame(update);
            }}
            
            // Start the update loop
            update();
        }}
    </script>
</body>
</html>
"""
        
        with open(html_path, "w") as f:
            f.write(html_content)
        
        print(f"✅ Created HTML demo: {html_path}")
        
        return html_path

# === Main Function ===
def main():
    """Main function"""
    try:
        extractor = SVGButtonExtractor()
        html_path = extractor.create_html_demo()
        
        print(f"✅ SVG button extraction complete")
        print(f"📂 Output directory: {extractor.output_dir}")
        print(f"🌐 HTML demo: {html_path}")
        print(f"🚀 Open the HTML demo in a web browser to see the buttons")
    except KeyboardInterrupt:
        print("🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
