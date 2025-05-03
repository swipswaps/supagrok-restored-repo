#!/bin/bash
# run_svg_extractor.sh — PRF‑SVG‑EXTRACTOR‑RUN‑2025‑05‑02
# Description: Run the SVG button extractor
# Status: ✅ PRF‑COMPLIANT

echo "🚀 Starting SVG Button Extractor"

# Make script executable
chmod +x svg_button_extractor.py

# Run the extractor
python3 svg_button_extractor.py

# Open the HTML demo in the default browser
if [ -f "svg_buttons/buttons_demo.html" ]; then
    echo "🌐 Opening HTML demo in browser"
    xdg-open "svg_buttons/buttons_demo.html"
fi

echo "👋 Done"
