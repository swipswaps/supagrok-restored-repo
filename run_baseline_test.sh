#!/bin/bash
# run_baseline_test.sh - Run a baseline test with actual eye tracking

# Kill any existing processes
echo "Killing any existing processes..."
pkill -f "python3 gaze_ws_server.py" || true
pkill -f "python3 eye_tracker_connector.py" || true
pkill -f "python3 gaze_boot_selector.py" || true
sleep 1

# Start the WebSocket server
echo "Starting WebSocket server..."
python3 gaze_ws_server.py &
SERVER_PID=$!
sleep 2

# Start the eye tracker connector
echo "Starting eye tracker connector..."
python3 eye_tracker_connector.py &
TRACKER_PID=$!
sleep 2

# Start the Gaze Boot Selector
echo "Starting Gaze Boot Selector..."
python3 gaze_boot_selector.py &
SELECTOR_PID=$!

# Wait for user to press Enter
echo ""
echo "Baseline test is running."
echo "The Gaze Boot Selector should be visible on your screen."
echo "Your eye movements should control the cursor."
echo "Press Enter to stop the test..."
read

# Kill all processes
echo "Stopping test..."
kill $SELECTOR_PID $TRACKER_PID $SERVER_PID
sleep 1

echo "Test completed."
