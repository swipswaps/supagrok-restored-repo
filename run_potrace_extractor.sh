#!/bin/bash
# run_potrace_extractor.sh — PRF‑POTRACE‑EXTRACTOR‑RUN‑2025‑05‑02
# Description: Run the Potrace button extractor
# Status: ✅ PRF‑COMPLIANT

echo "🚀 Starting Potrace Button Extractor"

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "❌ ImageMagick is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y imagemagick
fi

# Check if Potrace is installed
if ! command -v potrace &> /dev/null; then
    echo "❌ Potrace is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y potrace
fi

# Make script executable
chmod +x potrace_button_extractor.py

# Run the extractor
python3 potrace_button_extractor.py

# Open the HTML demo in the default browser
if [ -f "potrace_buttons/buttons_demo.html" ]; then
    echo "🌐 Opening HTML demo in browser"
    xdg-open "potrace_buttons/buttons_demo.html"
fi

echo "👋 Done"
