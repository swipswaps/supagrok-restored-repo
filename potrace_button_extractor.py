#!/usr/bin/env python3
# potrace_button_extractor.py — PRF‑POTRACE‑BUTTON‑EXTRACTOR‑2025‑05‑02
# Description: Extract buttons from reference image using Potrace for true vector tracing
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import cv2
import numpy as np
import subprocess
from PIL import Image
import tempfile
import shutil
import json
from pathlib import Path

# === Potrace Button Extractor Class ===
class PotraceButtonExtractor:
    """Extract buttons from reference image using Potrace for true vector tracing"""
    
    def __init__(self):
        """Initialize the extractor"""
        # Check if potrace is installed
        if not self._check_potrace():
            print("❌ Potrace is not installed. Please install it first.")
            print("   On Ubuntu/Debian: sudo apt-get install potrace")
            print("   On macOS: brew install potrace")
            sys.exit(1)
        
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
        
        # Create output directory
        self.output_dir = "potrace_buttons"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create temp directory for intermediate files
        self.temp_dir = tempfile.mkdtemp()
        print(f"📁 Created temporary directory: {self.temp_dir}")
        
        # Define button regions based on the reference image
        self.define_button_regions()
    
    def _check_potrace(self):
        """Check if potrace is installed"""
        try:
            subprocess.run(["potrace", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            return False
    
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
    
    def extract_button_colors(self, region, image):
        """Extract exact button colors from the image using color sampling"""
        x, y, width, height = region["x"], region["y"], region["width"], region["height"]
        
        # Extract button region from the image
        button_region = image[y:y+height, x:x+width]
        
        # Convert to RGB for better color analysis
        button_rgb = cv2.cvtColor(button_region, cv2.COLOR_BGR2RGB)
        
        # Sample colors from different parts of the button
        
        # Background color - sample from center
        center_x, center_y = width // 2, height // 2
        bg_color = button_rgb[center_y, center_x]
        
        # Border color - sample from edges
        border_samples = []
        # Top edge
        border_samples.extend([button_rgb[0, i] for i in range(0, width, width//10)])
        # Bottom edge
        border_samples.extend([button_rgb[height-1, i] for i in range(0, width, width//10)])
        # Left edge
        border_samples.extend([button_rgb[i, 0] for i in range(0, height, height//5)])
        # Right edge
        border_samples.extend([button_rgb[i, width-1] for i in range(0, height, height//5)])
        
        # Calculate average border color
        border_color = np.mean(border_samples, axis=0).astype(int)
        
        # Text color - assume white for now
        # In a more sophisticated implementation, we would use OCR to locate text
        # and then sample those pixels
        text_color = (255, 255, 255)  # White
        
        # Progress color - use the provided color
        progress_color_hex = region["progress_color"]
        progress_color = self.hex_to_rgb(progress_color_hex)
        
        return {
            "background": self.rgb_to_hex(bg_color),
            "border": self.rgb_to_hex(border_color),
            "text": self.rgb_to_hex(text_color),
            "progress": progress_color_hex
        }
    
    def rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex color string"""
        return f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color string to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def extract_button_svg(self, name, region):
        """Extract button as SVG using Potrace for true vector tracing"""
        x, y, width, height = region["x"], region["y"], region["width"], region["height"]
        
        # Extract button region from the reference image
        button_region = self.reference_image[y:y+height, x:x+width]
        
        # Save button region as temporary PNG
        temp_png = os.path.join(self.temp_dir, f"{name}_button.png")
        cv2.imwrite(temp_png, button_region)
        
        # Extract exact colors
        colors = self.extract_button_colors(region, self.reference_image)
        
        # Create a high-contrast version for better tracing
        high_contrast = self.create_high_contrast_image(button_region)
        high_contrast_png = os.path.join(self.temp_dir, f"{name}_button_high_contrast.png")
        cv2.imwrite(high_contrast_png, high_contrast)
        
        # Convert to BMP (Potrace requires BMP or PBM)
        temp_bmp = os.path.join(self.temp_dir, f"{name}_button.bmp")
        subprocess.run(["convert", high_contrast_png, temp_bmp], check=True)
        
        # Trace with Potrace
        temp_svg = os.path.join(self.temp_dir, f"{name}_button_traced.svg")
        subprocess.run([
            "potrace",
            "--svg",
            "--output", temp_svg,
            "--turdsize", "3",  # Remove small speckles
            "--alphamax", "1",  # Corner threshold
            "--color", "#000000",  # Trace color
            temp_bmp
        ], check=True)
        
        # Read the traced SVG
        with open(temp_svg, 'r') as f:
            svg_content = f.read()
        
        # Modify the SVG to add styling and progress bar
        modified_svg = self.modify_svg(svg_content, colors, width, height, name)
        
        # Save the final SVG
        output_svg = os.path.join(self.output_dir, f"{name}_button.svg")
        with open(output_svg, 'w') as f:
            f.write(modified_svg)
        
        print(f"✅ Created SVG for {name} button: {output_svg}")
        
        # Save color information
        color_info = os.path.join(self.output_dir, f"{name}_colors.json")
        with open(color_info, 'w') as f:
            json.dump(colors, f, indent=2)
        
        return output_svg
    
    def create_high_contrast_image(self, image):
        """Create a high-contrast version of the image for better tracing"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    
    def modify_svg(self, svg_content, colors, width, height, name):
        """Modify the SVG to add styling and progress bar"""
        # Add viewBox attribute if not present
        if 'viewBox' not in svg_content:
            svg_content = svg_content.replace('<svg', f'<svg viewBox="0 0 {width} {height}"')
        
        # Set width and height
        svg_content = svg_content.replace('<svg', f'<svg width="{width}" height="{height}"')
        
        # Add background rectangle with exact color
        bg_rect = f'<rect x="0" y="0" width="{width}" height="{height}" fill="{colors["background"]}" stroke="{colors["border"]}" stroke-width="1" />'
        svg_content = svg_content.replace('<svg', f'<svg\n  xmlns:xlink="http://www.w3.org/1999/xlink"')
        svg_content = svg_content.replace('</svg>', f'{bg_rect}\n</svg>')
        
        # Add text with exact color
        text_element = f'<text x="{width/2}" y="{height/2}" font-family="Arial, sans-serif" font-size="16" fill="{colors["text"]}" text-anchor="middle" dominant-baseline="middle">{self.button_regions[name]["text"]}</text>'
        svg_content = svg_content.replace('</svg>', f'{text_element}\n</svg>')
        
        # Add progress bar (initially empty)
        progress_bar = f'<rect class="progress" x="0" y="{height-4}" width="0" height="4" fill="{colors["progress"]}" />'
        svg_content = svg_content.replace('</svg>', f'{progress_bar}\n</svg>')
        
        return svg_content
    
    def extract_panel_svg(self):
        """Extract panel as SVG using Potrace for true vector tracing"""
        x, y, width, height = self.panel_region["x"], self.panel_region["y"], self.panel_region["width"], self.panel_region["height"]
        
        # Extract panel region from the reference image
        panel_region = self.reference_image[y:y+height, x:x+width]
        
        # Save panel region as temporary PNG
        temp_png = os.path.join(self.temp_dir, "panel.png")
        cv2.imwrite(temp_png, panel_region)
        
        # Create a high-contrast version for better tracing
        high_contrast = self.create_high_contrast_image(panel_region)
        high_contrast_png = os.path.join(self.temp_dir, "panel_high_contrast.png")
        cv2.imwrite(high_contrast_png, high_contrast)
        
        # Convert to BMP (Potrace requires BMP or PBM)
        temp_bmp = os.path.join(self.temp_dir, "panel.bmp")
        subprocess.run(["convert", high_contrast_png, temp_bmp], check=True)
        
        # Trace with Potrace
        temp_svg = os.path.join(self.temp_dir, "panel_traced.svg")
        subprocess.run([
            "potrace",
            "--svg",
            "--output", temp_svg,
            "--turdsize", "3",  # Remove small speckles
            "--alphamax", "1",  # Corner threshold
            "--color", "#000000",  # Trace color
            temp_bmp
        ], check=True)
        
        # Read the traced SVG
        with open(temp_svg, 'r') as f:
            svg_content = f.read()
        
        # Modify the SVG to add styling and title
        modified_svg = self.modify_panel_svg(svg_content, width, height)
        
        # Save the final SVG
        output_svg = os.path.join(self.output_dir, "panel.svg")
        with open(output_svg, 'w') as f:
            f.write(modified_svg)
        
        print(f"✅ Created SVG for panel: {output_svg}")
        
        return output_svg
    
    def modify_panel_svg(self, svg_content, width, height):
        """Modify the panel SVG to add styling and title"""
        # Add viewBox attribute if not present
        if 'viewBox' not in svg_content:
            svg_content = svg_content.replace('<svg', f'<svg viewBox="0 0 {width} {height}"')
        
        # Set width and height
        svg_content = svg_content.replace('<svg', f'<svg width="{width}" height="{height}"')
        
        # Add background rectangle
        bg_rect = f'<rect x="0" y="0" width="{width}" height="{height}" fill="#1a1a1a" stroke="#666666" stroke-width="1" />'
        svg_content = svg_content.replace('<svg', f'<svg\n  xmlns:xlink="http://www.w3.org/1999/xlink"')
        svg_content = svg_content.replace('</svg>', f'{bg_rect}\n</svg>')
        
        # Add title text
        title_element = f'<text x="{width/2}" y="30" font-family="Arial, sans-serif" font-size="18" fill="#ffffff" text-anchor="middle" dominant-baseline="middle">{self.panel_region["title"]}</text>'
        svg_content = svg_content.replace('</svg>', f'{title_element}\n</svg>')
        
        return svg_content
    
    def create_html_demo(self):
        """Create HTML demo with the traced SVG buttons"""
        # Extract all buttons as SVGs
        button_svgs = {}
        for name, region in self.button_regions.items():
            button_svgs[name] = self.extract_button_svg(name, region)
        
        # Extract panel as SVG
        panel_svg = self.extract_panel_svg()
        
        # Create HTML file
        html_path = os.path.join(self.output_dir, "buttons_demo.html")
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Potrace Button Demo</title>
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
        <object data="{os.path.basename(button_svgs['exit'])}" type="image/svg+xml" width="{self.button_regions['exit']['width']}" height="{self.button_regions['exit']['height']}"></object>
    </div>
    
    <div class="panel">
        <object data="{os.path.basename(panel_svg)}" type="image/svg+xml" width="{self.panel_region['width']}" height="{self.panel_region['height']}"></object>
        
        <div class="button mode1-button" id="mode1Button">
            <object data="{os.path.basename(button_svgs['mode1'])}" type="image/svg+xml" width="{self.button_regions['mode1']['width']}" height="{self.button_regions['mode1']['height']}"></object>
        </div>
        
        <div class="button mode2-button" id="mode2Button">
            <object data="{os.path.basename(button_svgs['mode2'])}" type="image/svg+xml" width="{self.button_regions['mode2']['width']}" height="{self.button_regions['mode2']['height']}"></object>
        </div>
        
        <div class="button mode3-button" id="mode3Button">
            <object data="{os.path.basename(button_svgs['mode3'])}" type="image/svg+xml" width="{self.button_regions['mode3']['width']}" height="{self.button_regions['mode3']['height']}"></object>
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
                            const width = button.progress.getAttribute('width').baseVal.valueInSpecifiedUnits;
                            const progressWidth = (progress / 100) * {self.button_regions["mode1"]["width"]};
                            
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
    
    def cleanup(self):
        """Clean up temporary files"""
        print(f"🧹 Cleaning up temporary directory: {self.temp_dir}")
        shutil.rmtree(self.temp_dir)

# === Main Function ===
def main():
    """Main function"""
    try:
        extractor = PotraceButtonExtractor()
        html_path = extractor.create_html_demo()
        
        print(f"✅ Potrace button extraction complete")
        print(f"📂 Output directory: {extractor.output_dir}")
        print(f"🌐 HTML demo: {html_path}")
        print(f"🚀 Open the HTML demo in a web browser to see the buttons")
        
        # Clean up temporary files
        extractor.cleanup()
    except KeyboardInterrupt:
        print("🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
