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
- Chatbot interface for interacting with a model worker

## Running the Application

To run the full application with chatbot functionality, you need to start two separate components: the **Web UI Server** and the **Chatbot Worker**.

### 1. Start the Web UI Server

The server hosts the web interface, streams the camera feed, and manages the chatbot job queue.

1.  **Navigate to the `robot_arm` directory.**

2.  **Install dependencies using `uv`**:
    If you haven't already, this command creates a virtual environment in `.venv` and installs all required packages from `pyproject.toml`.
    ```bash
    uv sync
    ```

3.  **Run the server**:
    ```bash
    uv run start-robot-ui
    ```
    The web interface will now be accessible at `http://localhost:5000`.

### 2. Start the Chatbot Worker

The chatbot worker is a separate Python script that polls the web server for new messages, processes them, and submits the results. The provided example client simulates a model's response.

1.  **Navigate to the `moe_channel` directory**:
    This component is in a different project folder.
    ```bash
    cd ../GPU-side-channels/moe_channel
    ```

2.  **Install dependencies for the client**:
    This project has its own set of dependencies defined in its `pyproject.toml`.
    ```bash
    uv sync
    ```

3.  **Configure the server IP (IMPORTANT)**:
    Before running the client, you must configure it to point to the machine running the Web UI server. Open the client file: `src/moe_channel/simple_python_client.py`.

    Modify the `SERVER` variable to match your server's IP address:
    ```python
    # Change this to your server's IP address
    SERVER = "http://<YOUR_SERVER_IP>:5000" 
    ```

4.  **Run the chatbot client**:
    The client now loads the trained steganography model to generate responses.
    ```bash
    # Run with default model path
    uv run client

    # Or specify a path to your model checkpoint
    uv run client -- --model_path /path/to/your/best_model
    ```
    The client will load the model, start polling the server for jobs, and when it receives one, it will generate a response while also extracting the hidden data from the expert layer usage. You can now use the chatbot feature in the web UI to interact with your trained model.

## Usage

1. **Camera View**: Live feed from robot arm camera
2. **3D Model**: Interactive 3D visualization of robot arm position
3. **Joint Control**: Use sliders to control individual joint angles
4. **System Functions**: Initialize, torque control, LED control
5. **SDR Waterfall**: Real-time spectrum analysis
6. **Command Interface**: Send custom JSON commands
7. **Chatbot**: Interact with the connected model worker.

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
# From the robot_arm directory
uv sync
```
This will create a virtual environment in `.venv` and install all required packages.

### Running the Web UI and Chatbot

The full system requires two components running simultaneously. Follow the steps in the **[Running the Application](#running-the-application)** section above for detailed instructions.

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