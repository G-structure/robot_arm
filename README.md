# Robot Arm Control Interface

## UI Modernization Update

The web interface has been modernized with a cyberpunk-inspired design while preserving all existing functionality:

### Visual Enhancements
- **Typography**: Switched to Share Tech Mono font for a futuristic look
- **Color Scheme**: Dark theme with cyan accents (`#00ffff`) on dark navy background (`#05051f`)
- **Visual Effects**: Added subtle scan line effects and background patterns
- **Layout**: Improved responsive grid layout with better visual hierarchy
- **Components**: Cyberpunk-styled buttons, inputs, sliders, and cards

### 3D Robot Model Integration
- **Three.js Visualization**: Added real-time 3D robot arm model
- **Live Synchronization**: 3D model reflects actual robot arm position
- **Interactive Controls**: Sliders update both robot and 3D visualization
- **Camera Controls**: Orbit controls for viewing the 3D model from any angle

### Preserved Functionality
- **Robot Communication**: All existing robot control commands maintained
- **SDR Waterfall**: Spectrum analyzer visualization preserved with themed styling  
- **Camera Feed**: Live video stream with cyberpunk-styled overlay
- **Command Interface**: JSON command interface with improved UX
- **Status Monitoring**: Real-time robot and system status updates

### Technical Implementation
- **Modular Design**: Clean separation between functionality and styling
- **Performance**: Optimized Three.js rendering with proper resource management
- **Responsive**: Mobile-friendly design with adaptive layouts
- **Accessibility**: Improved focus states and keyboard navigation

## Original Features

A web interface for controlling a robot arm and viewing its camera feed.

## Features

- Live camera stream from robot arm
- Real-time robot arm control interface  
- 3D visualization with position feedback
- SDR spectrum analyzer with waterfall display
- Command library with pre-defined actions
- Status monitoring and feedback logging

## Setup

```bash
# Install dependencies
uv sync

# Run the server
uv run python -m web_ui.server

# Access the interface
open http://localhost:5000
```

## Usage

1. **Camera View**: Live feed from robot arm camera
2. **3D Model**: Interactive 3D visualization of robot arm position
3. **Joint Control**: Use sliders to control individual joint angles
4. **System Functions**: Initialize, torque control, LED control
5. **SDR Waterfall**: Real-time spectrum analysis
6. **Command Interface**: Send custom JSON commands

## Configuration

Set the robot IP address via environment variable:
```bash
export ROBOT_IP=192.168.4.1
```

## Dependencies

- Flask (web framework)
- OpenCV (camera handling)
- NumPy (data processing)
- Three.js (3D visualization)
- SciPy (signal processing)

## Project Structure

- `web_ui/`: Contains the Flask web application.
- `docs/`: Project documentation.
- `python_example/`: Original Python examples for controlling the arm.
- `notes/`: Scratchpad and development notes.
- `pyproject.toml`: Project definition and dependencies for `uv`.

## Getting Started

This project is managed with `uv`.

### Prerequisites

- Python 3.9+
- `uv` installed. See [official instructions](https://docs.astral.sh/uv/install.sh).
- CUDA-compatible GPU (recommended for MoE backend)

### Installation

Clone the repository and install the dependencies using `uv`:

```bash
uv sync
```

This will create a virtual environment in `.venv` and install all required packages.

### Running the Web UI

To start the web interface, run the following command from the project root:

```bash
uv run start-robot-ui
```

The application will be available at [http://localhost:5000](http://localhost:5000).

### Running the MoE Backend

The project includes a new MoE (Mixture of Experts) backend for real-time streaming of expert selection data during model inference:

```bash
# Start the MoE backend server
uv run start-moe-backend

# Interactive CLI chat with expert visualization
uv run moe-cli chat

# Health check
uv run moe-cli health
```

See [`moe_backend/README.md`](moe_backend/README.md) for detailed documentation.

## Command Line Options

The web UI supports the following command line arguments:

```bash
uv run start-robot-ui --help
```

### Available Arguments

- `--port PORT`: Specify the port to run the web server on (default: 5000)
- `--no-robot`: Disable robot connection for testing without a physical robot

### Examples

```bash
# Run on default port (5000)
uv run start-robot-ui

# Run on custom port
uv run start-robot-ui --port 8080

# Run without robot connection (for testing)
uv run start-robot-ui --no-robot

# Combine arguments
uv run start-robot-ui --port 3000 --no-robot
```

When using `--no-robot`, all robot commands will be simulated and the interface will show "Robot disabled (--no-robot mode)" in the status section. 