# Gaze Boot Selector

## Overview

The Gaze Boot Selector is a modern, eye-tracking enabled interface for selecting boot options in GRUB and rEFInd boot managers. It allows users to select boot options using just their gaze, making the system more accessible and solving issues with jumpiness in eye tracking.

## Features

### Modern UI Design
- Clean, high-contrast interface inspired by ChatGPT images
- Color-coded buttons for different boot options
- Gradient backgrounds and subtle grid patterns
- Responsive hover effects
- Animated selection feedback

### Improved Gaze Tracking
- Enhanced gaze indicator with center dot for precise targeting
- Visual progress feedback during dwell selection
- Pulsing animation during selection
- Status bar with real-time feedback

### Stability Improvements
- Adaptive dwell radius to reduce jumpiness
- Forgiving dwell time calculation
- Larger initial dwell radius for more stable selection
- Partial progress retention when gaze moves slightly

### Boot Option Detection
- Automatic detection of GRUB and rEFInd boot entries
- Fallback to default options if detection fails
- Custom icons for different types of boot options

## Usage

1. Start the WebSocket server for eye tracking:
   ```bash
   python3 gaze_ws_server.py
   ```

2. Start the Gaze Boot Selector:
   ```bash
   python3 gaze_boot_selector.py
   ```

3. Look at the desired boot option and keep your gaze on it until the progress indicator completes.

4. The selected option will be highlighted with a pulsing animation and then activated.

5. Press Escape or 'q' to exit the selector.

## Configuration

You can customize the Gaze Boot Selector with command-line options:

```bash
python3 gaze_boot_selector.py --dwell-time 1.5 --dwell-radius 40 --smoothing 0.6 --save-config
```

Options:
- `--dwell-time`: Time in seconds to dwell for selection (default: 2.0)
- `--dwell-radius`: Radius in pixels for dwell detection (default: 50)
- `--smoothing`: Smoothing factor for gaze movement (default: 0.5)
- `--save-config`: Save configuration to file for future use

## How It Solves Jumpiness

The Gaze Boot Selector addresses jumpiness issues through several mechanisms:

1. **Adaptive Dwell Radius**: Uses a larger radius during the initial phase of selection
2. **Forgiving Dwell Time**: Only partially resets progress when gaze moves slightly outside the dwell radius
3. **Smoothing**: Implements configurable smoothing to reduce jitter in gaze position
4. **Larger Buttons**: Provides larger targets that are easier to focus on
5. **Visual Feedback**: Shows gaze position and selection progress for better user control
6. **Status Updates**: Provides real-time feedback on what the system is detecting

## Design Inspiration

The UI design is inspired by modern interfaces seen in ChatGPT images, featuring:

1. **Color Scheme**: 
   - Blue for Linux (#0078D7)
   - Light blue for Windows (#00A4EF)
   - Yellow for Recovery Mode (#FFB900)
   - Red for Fix GRUB (#F25022)
   - Green for UEFI Settings (#7FBA00)

2. **Visual Elements**:
   - Gradient backgrounds
   - Subtle grid patterns
   - Flat design buttons
   - Animated progress indicators
   - Pulsing selection effects

## Requirements

- Python 3.6 or higher
- Tkinter (usually included with Python)
- WebSocket client library: `pip install websocket-client`
- Running gaze tracking system (gaze_ws_server.py)
