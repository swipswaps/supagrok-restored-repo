#!/bin/bash
# run_fixed_tracker.sh — PRF‑WEBCAM‑RUN‑2025‑05‑02
# Description: Run the fixed eye tracker
# Status: ✅ PRF‑COMPLIANT

# Set error handling
set -e

# Log function
log() {
    echo "[$(date -Iseconds)] $1"
}

# Clean up function
cleanup() {
    log "🛑 Cleaning up..."
    pkill -f "python3 fixed_eye_tracker.py" || true
}

# Register cleanup function
trap cleanup EXIT INT TERM

# Main function
main() {
    log "🚀 Starting Fixed Eye Tracker"
    
    # Check if script exists
    if [ ! -f "fixed_eye_tracker.py" ]; then
        log "❌ fixed_eye_tracker.py not found"
        exit 1
    fi
    
    # Make script executable
    chmod +x fixed_eye_tracker.py
    
    # Run eye tracker
    log "👁️ Running eye tracker..."
    ./fixed_eye_tracker.py
}

# Run main function
main
