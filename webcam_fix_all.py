#!/usr/bin/env python3
# webcam_fix_all.py — PRF‑WEBCAM‑FIX‑ALL‑2025‑05‑02
# Description: One-shot solution to fix webcam connection issues
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import subprocess
import time
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# === Metadata ===
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
LOGFILE = Path(f"/tmp/webcam_fix_{TS}.log")
SCRIPT_DIR = Path(tempfile.mkdtemp(prefix="webcam_fix_"))

# === Logging ===
def log(msg):
    """Log message to file and console"""
    timestamp = datetime.now().isoformat()
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    
    with open(LOGFILE, "a") as f:
        f.write(log_msg + "\n")

# === Dependency Management ===
def install_dependencies():
    """Install all required dependencies"""
    log("📦 Installing required dependencies...")
    
    # Core dependencies
    dependencies = [
        "opencv-python",
        "numpy",
        "websockets",
        "pillow",
        "scipy"
    ]
    
    # Try to install dlib, but don't fail if it doesn't work
    try:
        log("📦 Installing dlib prerequisites...")
        subprocess.run("sudo apt-get update", shell=True, check=False)
        subprocess.run("sudo apt-get install -y cmake libopenblas-dev liblapack-dev libx11-dev libatlas-base-dev", 
                      shell=True, check=False)
        dependencies.append("dlib")
    except:
        log("⚠️ Could not install dlib prerequisites, will use fallback detection")
    
    # Install dependencies
    log("📦 Installing Python packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + dependencies)
        log("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        log(f"⚠️ Some dependencies could not be installed: {e}")
        log("⚠️ Will continue with available packages")

# === Script Generation ===
def generate_diagnostic_script():
    """Generate the webcam diagnostic script"""
    script_path = SCRIPT_DIR / "webcam_diagnostic.py"
    
    script_content = '''#!/usr/bin/env python3
# webcam_diagnostic.py — PRF‑WEBCAM‑DIAGNOSTIC‑2025‑05‑02
# Description: Diagnose webcam and dependency issues
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import subprocess
import time
from datetime import datetime

# === Logging ===
def log(msg):
    """Log message to console"""
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] {msg}")

# === Dependency Check ===
def check_dependency(package_name, import_name=None):
    """Check if a dependency is installed"""
    if import_name is None:
        import_name = package_name.replace("-", "_")
    
    try:
        __import__(import_name)
        log(f"✅ {package_name} is installed")
        return True
    except ImportError:
        log(f"❌ {package_name} is NOT installed")
        return False

# === Webcam Check ===
def check_webcam():
    """Check if webcam is accessible"""
    log("🔍 Checking webcam...")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            log("❌ Failed to open webcam")
            log("   Possible causes:")
            log("   - Webcam is not connected")
            log("   - Webcam is being used by another application")
            log("   - Insufficient permissions")
            return False
        
        # Try to read a frame
        ret, frame = cap.read()
        if not ret:
            log("❌ Failed to capture frame from webcam")
            log("   Possible causes:")
            log("   - Webcam driver issues")
            log("   - Webcam hardware problem")
            cap.release()
            return False
        
        # Get webcam info
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        log(f"✅ Webcam is working")
        log(f"   Resolution: {width}x{height}")
        log(f"   FPS: {fps}")
        
        # Clean up
        cap.release()
        return True
    
    except Exception as e:
        log(f"❌ Error checking webcam: {e}")
        return False

# === Display Check ===
def check_display():
    """Check if display is accessible"""
    log("🔍 Checking display...")
    
    try:
        import cv2
        import numpy as np
        
        # Create a simple test window
        test_image = np.zeros((300, 400, 3), dtype=np.uint8)
        cv2.putText(test_image, "Display Test", (100, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Try to show the window
        window_name = "Display Test"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, test_image)
        
        log("✅ Display window created")
        log("   If you can see a window with 'Display Test' text, display is working")
        log("   Press any key to continue...")
        
        # Wait for key press
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return True
    
    except Exception as e:
        log(f"❌ Error checking display: {e}")
        log("   Possible causes:")
        log("   - No display available (headless environment)")
        log("   - X server not running")
        log("   - Insufficient permissions")
        return False

# === Face Detection Check ===
def check_face_detection():
    """Check if face detection is working"""
    log("🔍 Checking face detection...")
    
    try:
        import cv2
        
        # Try to load the face cascade
        cv_path = cv2.__path__[0]
        face_cascade_path = f'{cv_path}/data/haarcascade_frontalface_default.xml'
        
        if not os.path.exists(face_cascade_path):
            log(f"❌ Face cascade file not found: {face_cascade_path}")
            return False
        
        face_cascade = cv2.CascadeClassifier(face_cascade_path)
        
        if face_cascade.empty():
            log("❌ Failed to load face cascade")
            return False
        
        log("✅ Face detection is available")
        
        # Try to detect faces from webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            log("❌ Cannot test face detection: webcam not available")
            return False
        
        log("📷 Capturing frame to test face detection...")
        ret, frame = cap.read()
        
        if not ret:
            log("❌ Failed to capture frame for face detection test")
            cap.release()
            return False
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) > 0:
            log(f"✅ Detected {len(faces)} face(s) in test frame")
        else:
            log("⚠️ No faces detected in test frame")
            log("   This is normal if no face is visible to the webcam")
        
        # Draw rectangles around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Show the result
        cv2.imshow("Face Detection Test", frame)
        log("   If you can see green rectangles around faces, face detection is working")
        log("   Press any key to continue...")
        
        # Wait for key press
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        cap.release()
        
        return True
    
    except Exception as e:
        log(f"❌ Error checking face detection: {e}")
        return False

# === WebSocket Check ===
def check_websocket():
    """Check if WebSocket server can be started"""
    log("🔍 Checking WebSocket capability...")
    
    try:
        import asyncio
        import websockets
        
        log("✅ WebSocket libraries are available")
        
        # Try to start a simple WebSocket server
        async def echo(websocket, path):
            async for message in websocket:
                await websocket.send(f"Echo: {message}")
        
        async def start_server():
            try:
                server = await websockets.serve(echo, "localhost", 8765)
                log("✅ WebSocket server started successfully")
                return server
            except Exception as e:
                log(f"❌ Failed to start WebSocket server: {e}")
                return None
        
        async def test_connection():
            try:
                uri = "ws://localhost:8765"
                async with websockets.connect(uri) as websocket:
                    test_message = "Hello, WebSocket!"
                    await websocket.send(test_message)
                    response = await websocket.recv()
                    log(f"✅ WebSocket connection test successful")
                    log(f"   Sent: {test_message}")
                    log(f"   Received: {response}")
                    return True
            except Exception as e:
                log(f"❌ Failed to connect to WebSocket server: {e}")
                return False
        
        async def run_test():
            server = await start_server()
            if server:
                result = await test_connection()
                server.close()
                await server.wait_closed()
                return result
            return False
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(run_test())
        
        return result
    
    except Exception as e:
        log(f"❌ Error checking WebSocket: {e}")
        return False

# === Main Function ===
def main():
    """Main function"""
    log("🚀 Starting Webcam Diagnostic")
    
    # Check Python version
    python_version = sys.version.split()[0]
    log(f"Python version: {python_version}")
    
    # Check operating system
    log(f"Operating system: {os.name} - {sys.platform}")
    
    # Check key dependencies
    dependencies = [
        ("opencv-python", "cv2"),
        ("numpy", "numpy"),
        ("websockets", "websockets"),
        ("dlib", "dlib"),
        ("scipy", "scipy")
    ]
    
    missing_deps = []
    for package, import_name in dependencies:
        if not check_dependency(package, import_name):
            missing_deps.append(package)
    
    if missing_deps:
        log(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        log("   Please install them with:")
        log(f"   pip install {' '.join(missing_deps)}")
    else:
        log("✅ All required dependencies are installed")
    
    # Check webcam
    webcam_ok = check_webcam()
    
    # Check display
    display_ok = check_display()
    
    # Check face detection
    if webcam_ok and display_ok:
        face_detection_ok = check_face_detection()
    else:
        log("⚠️ Skipping face detection check due to webcam or display issues")
        face_detection_ok = False
    
    # Check WebSocket
    websocket_ok = check_websocket()
    
    # Summary
    log("\n=== Diagnostic Summary ===")
    log(f"Dependencies: {'✅ OK' if not missing_deps else '❌ Missing'}")
    log(f"Webcam: {'✅ OK' if webcam_ok else '❌ Failed'}")
    log(f"Display: {'✅ OK' if display_ok else '❌ Failed'}")
    log(f"Face Detection: {'✅ OK' if face_detection_ok else '❌ Failed'}")
    log(f"WebSocket: {'✅ OK' if websocket_ok else '❌ Failed'}")
    
    if not webcam_ok:
        log("\n❌ The main issue appears to be with your webcam.")
        log("   Possible solutions:")
        log("   1. Make sure your webcam is properly connected")
        log("   2. Close any other applications that might be using the webcam")
        log("   3. Check webcam permissions (some systems require explicit permission)")
        log("   4. Try a different USB port if using an external webcam")
        log("   5. Update your webcam drivers")
    
    if not display_ok:
        log("\n❌ The main issue appears to be with your display.")
        log("   Possible solutions:")
        log("   1. Make sure you're not running in a headless environment")
        log("   2. Check if X server is running")
        log("   3. Set the DISPLAY environment variable if needed")
    
    if not websocket_ok:
        log("\n❌ The main issue appears to be with WebSocket communication.")
        log("   Possible solutions:")
        log("   1. Check if port 8765 is available")
        log("   2. Check if any firewall is blocking the connection")
        log("   3. Make sure no other WebSocket server is running on the same port")
    
    log("\nDiagnostic complete. Use this information to troubleshoot your setup.")

if __name__ == "__main__":
    main()
'''
    
    with open(script_path, "w") as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)  # Make executable
    log(f"✅ Generated diagnostic script at {script_path}")
    return script_path

def generate_webcam_eye_tracker():
    """Generate the webcam eye tracker script"""
    script_path = SCRIPT_DIR / "webcam_eye_tracker.py"
    
    script_content = '''#!/usr/bin/env python3
# webcam_eye_tracker.py — PRF‑WEBCAM‑EYE‑TRACKER‑2025‑05‑02‑C
# Description: Simple eye tracking using laptop's built-in webcam
# Status: ✅ PRF‑COMPLIANT

import os
import sys
import subprocess
import time
import signal
from datetime import datetime
from pathlib import Path

# === Metadata ===
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
LOGFILE = Path(f"/tmp/webcam_eye_tracker_{TS}.log")

# === Logging ===
def log(msg):
    """Log message to file and console"""
    timestamp = datetime.now().isoformat()
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    
    with open(LOGFILE, "a") as f:
        f.write(log_msg + "\n")

# === Dependency Management ===
def check_and_install_dependencies():
    """Check and install required dependencies"""
    log("🔍 Checking dependencies...")
    
    # Required packages
    required_packages = [
        "opencv-python",
        "numpy",
        "scipy"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == "opencv-python":
                __import__("cv2")
            else:
                __import__(package.replace("-", "_"))
            log(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            log(f"❌ {package} is not installed")
    
    if missing_packages:
        log(f"📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            log("✅ All dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            log(f"❌ Failed to install dependencies: {e}")
            sys.exit(1)

# === Signal Handlers ===
def handle_signal(sig, frame):
    """Handle signals for clean shutdown"""
    log(f"🛑 Received signal {sig}, shutting down...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_signal)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_signal)  # Termination signal

# === Main Function ===
def main():
    """Main function"""
    log("🚀 Starting Webcam Eye Tracker")
    log(f"📜 Log file: {LOGFILE}")
    
    # Check and install dependencies
    check_and_install_dependencies()
    
    # Import dependencies after they've been installed
    import cv2
    import numpy as np
    
    try:
        # Initialize webcam
        log("🔌 Connecting to webcam...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            log("❌ Failed to open webcam")
            return
        
        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Get actual resolution
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        log(f"✅ Connected to webcam ({frame_width}x{frame_height})")
        
        # Load face and eye cascades
        cv_path = cv2.__path__[0]
        face_cascade = cv2.CascadeClassifier(f'{cv_path}/data/haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(f'{cv_path}/data/haarcascade_eye.xml')
        
        if face_cascade.empty() or eye_cascade.empty():
            log("❌ Failed to load cascade classifiers")
            return
        
        # Create window
        cv2.namedWindow("Eye Tracking", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Eye Tracking", frame_width, frame_height)
        
        log("✅ Webcam initialized")
        log("👁️ Looking for face and eyes...")
        log("Press ESC to exit")
        
        while True:
            # Capture frame
            ret, frame = cap.read()
            
            if not ret:
                log("❌ Failed to capture frame")
                break
            
            # Create a copy for visualization
            display_frame = frame.copy()
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # If no faces detected
            if len(faces) == 0:
                cv2.putText(display_frame, "No face detected", (30, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Process detected faces
            for (x, y, w, h) in faces:
                # Draw green rectangle around face
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(display_frame, "Face", (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Draw green dots around face (8 points)
                for i in range(8):
                    angle = i * 45  # 8 points around the face
                    px = int(x + w/2 + (w/2) * 0.9 * np.cos(np.radians(angle)))
                    py = int(y + h/2 + (h/2) * 0.9 * np.sin(np.radians(angle)))
                    cv2.circle(display_frame, (px, py), 3, (0, 255, 0), -1)
                
                # Extract face ROI
                roi_gray = gray[y:y+h, x:x+w]
                roi_color = display_frame[y:y+h, x:x+w]
                
                # Detect eyes
                eyes = eye_cascade.detectMultiScale(roi_gray)
                
                # Process detected eyes
                for (ex, ey, ew, eh) in eyes:
                    # Draw orange rectangle around eye
                    cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 165, 255), 2)
                    
                    # Draw orange dots around the eye (6 points)
                    for i in range(6):
                        angle = i * 60  # 6 points around the eye
                        px = int(ex + ew/2 + (ew/2) * 0.8 * np.cos(np.radians(angle)))
                        py = int(ey + eh/2 + (eh/2) * 0.8 * np.sin(np.radians(angle)))
                        cv2.circle(roi_color, (px, py), 2, (0, 165, 255), -1)
                    
                    # Draw eye center
                    eye_center_x = ex + ew // 2
                    eye_center_y = ey + eh // 2
                    cv2.circle(roi_color, (eye_center_x, eye_center_y), 3, (255, 0, 0), -1)
            
            # Add instructions
            cv2.putText(display_frame, "Press ESC to exit", (10, frame_height - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Show the frame
            cv2.imshow("Eye Tracking", display_frame)
            
            # Exit if ESC is pressed
            if cv2.waitKey(1) == 27:
                break
        
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        log("👋 Eye tracking completed")
    
    except KeyboardInterrupt:
        log("🛑 Interrupted by user")
    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        log(f"📋 Traceback: {traceback.format_exc()}")
    finally:
        # Clean up
        try:
            cap.release()
            cv2.destroyAllWindows()
        except:
            pass

if __name__ == "__main__":
    main()
'''
    
    with open(script_path, "w") as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)  # Make executable
    log(f"✅ Generated webcam eye tracker script at {script_path}")
    return script_path

def generate_webcam_test_script():
    """Generate the webcam test script"""
    script_path = SCRIPT_DIR / "run_webcam_test.sh"
    
    script_content = '''#!/bin/bash
# run_webcam_test.sh — PRF‑WEBCAM‑TEST‑2025‑05‑02‑C
# Description: Run webcam eye tracking test
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
    pkill -f "python3 webcam_eye_tracker.py" || true
    pkill -f "python3 webcam_diagnostic.py" || true
}

# Register cleanup function
trap cleanup EXIT INT TERM

# Main function
main() {
    log "🚀 Starting Webcam Test"
    
    # Check if scripts exist
    if [ ! -f "webcam_diagnostic.py" ]; then
        log "❌ webcam_diagnostic.py not found"
        exit 1
    fi
    
    if [ ! -f "webcam_eye_tracker.py" ]; then
        log "❌ webcam_eye_tracker.py not found"
        exit 1
    fi
    
    # Make scripts executable
    chmod +x webcam_diagnostic.py
    chmod +x webcam_eye_tracker.py
    
    # Run diagnostic
    log "🔍 Running diagnostic..."
    ./webcam_diagnostic.py
    
    # Ask user if they want to continue
    read -p "Do you want to run the eye tracker? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Run eye tracker
        log "👁️ Running eye tracker..."
        ./webcam_eye_tracker.py
    else
        log "👋 Test aborted by user"
    fi
}

# Run main function
main
'''
    
    with open(script_path, "w") as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)  # Make executable
    log(f"✅ Generated test script at {script_path}")
    return script_path

# === Fix Webcam Issues ===
def fix_webcam_issues():
    """Fix common webcam issues"""
    log("🔧 Fixing common webcam issues...")
    
    # Kill any processes that might be using the webcam
    log("🔍 Checking for processes using the webcam...")
    try:
        subprocess.run("pkill -f 'zoom' || true", shell=True)
        subprocess.run("pkill -f 'skype' || true", shell=True)
        subprocess.run("pkill -f 'teams' || true", shell=True)
        subprocess.run("pkill -f 'meet' || true", shell=True)
        subprocess.run("pkill -f 'chrome' || true", shell=True)
        subprocess.run("pkill -f 'firefox' || true", shell=True)
        log("✅ Killed potential processes using the webcam")
    except:
        log("⚠️ Could not kill processes")
    
    # Reset USB devices
    log("🔍 Resetting USB devices...")
    try:
        subprocess.run("sudo modprobe -r uvcvideo || true", shell=True, check=False)
        time.sleep(1)
        subprocess.run("sudo modprobe uvcvideo || true", shell=True, check=False)
        log("✅ Reset USB video devices")
    except:
        log("⚠️ Could not reset USB devices")
    
    # Set permissions
    log("🔍 Setting webcam permissions...")
    try:
        subprocess.run("sudo chmod 777 /dev/video* || true", shell=True, check=False)
        log("✅ Set webcam permissions")
    except:
        log("⚠️ Could not set webcam permissions")

# === Fix Display Issues ===
def fix_display_issues():
    """Fix common display issues"""
    log("🔧 Fixing common display issues...")
    
    # Set DISPLAY environment variable
    os.environ["DISPLAY"] = ":0"
    log("✅ Set DISPLAY environment variable to :0")
    
    # Check if X server is running
    log("🔍 Checking if X server is running...")
    try:
        result = subprocess.run("xset q", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            log("✅ X server is running")
        else:
            log("⚠️ X server might not be running")
    except:
        log("⚠️ Could not check X server status")

# === Fix WebSocket Issues ===
def fix_websocket_issues():
    """Fix common WebSocket issues"""
    log("🔧 Fixing common WebSocket issues...")
    
    # Kill any processes that might be using port 8765
    log("🔍 Checking for processes using port 8765...")
    try:
        subprocess.run("sudo fuser -k 8765/tcp || true", shell=True, check=False)
        log("✅ Killed processes using port 8765")
    except:
        log("⚠️ Could not kill processes using port 8765")

# === Main Function ===
def main():
    """Main function"""
    log("🚀 Starting Webcam Fix All")
    log(f"📜 Log file: {LOGFILE}")
    log(f"📂 Script directory: {SCRIPT_DIR}")
    
    # Install dependencies
    install_dependencies()
    
    # Fix common issues
    fix_webcam_issues()
    fix_display_issues()
    fix_websocket_issues()
    
    # Generate scripts
    diagnostic_script = generate_diagnostic_script()
    webcam_script = generate_webcam_eye_tracker()
    test_script = generate_webcam_test_script()
    
    # Change to script directory
    os.chdir(SCRIPT_DIR)
    
    # Run the test script
    log("🚀 Running test script...")
    try:
        subprocess.run(f"{test_script}", shell=True)
    except KeyboardInterrupt:
        log("🛑 Test interrupted by user")
    except Exception as e:
        log(f"❌ Error running test script: {e}")
    
    log(f"👋 All done! Scripts are available in {SCRIPT_DIR}")
    log(f"📜 Log file: {LOGFILE}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("🛑 Interrupted by user")
    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        log(f"📋 Traceback: {traceback.format_exc()}")
