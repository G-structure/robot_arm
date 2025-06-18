# Robot Arm Web Interface

## Overview
The robot arm includes a comprehensive web interface that provides:
- Live camera streaming
- Robot arm control
- System status monitoring
- Real-time command interface

## Accessing the Web Interface
- **Local Access**: `http://localhost:5000`
- **Network Access**: The server is accessible on the host machine's IP address at port 5000.

## Starting the Web Server
The web server is managed as a Python project with `uv`.

### Installation
From the project's root directory, install the necessary dependencies using `uv`:
```bash
uv sync
```
This command installs all dependencies defined in the `pyproject.toml` file into a local virtual environment.

### Running the Server
```bash
uv run start-robot-ui
```
The server will start and be accessible on port `5000`.

## Web Interface Features

The interface is divided into three main sections:

### 1. Live Camera Feed
- Real-time video streaming using Motion JPEG.
- Displays at 640x480 resolution at 30 FPS.
- Includes a timestamp overlay for reference.
- Shows a "Camera Not Available" message as a fallback on camera errors.

### 2. Robot Control Panel
This panel contains all the interactive controls for the robot.

- **Robot Configuration**:
  - An input field to set the IP address of the robot arm controller. This must be set before sending commands.

- **Quick Commands**:
  - Pre-defined buttons for common robot actions:
    - **Home Position**: `{"T":104}`
    - **Get Status**: `{"T":1}`
    - **Stop**: `{"T":2}`
    - **Reset**: `{"T":3}`

- **Custom Commands**:
  - A text area to send any valid JSON command to the robot arm.

### 3. System Status
This section provides real-time feedback from the system.
- **Camera Status**: Shows if the camera is active and its current resolution/FPS.
- **Robot Connection**: Displays the configured robot IP or "Not configured".
- **Last Command**: Shows the last JSON command sent to the robot.
- **Last Response**: Displays the last response received from the robot.

## API Endpoints

The web interface is powered by a set of REST API endpoints that can also be used for programmatic control.

### Camera Endpoints
- `GET /video_feed`: The live MJPEG video stream.
- `GET /camera/info`: JSON object with camera status and capabilities.
  - **Example**: `curl http://localhost:5000/camera/info`

### Robot Control Endpoints
- `POST /robot/command`: Send a JSON command to the robot.
  - **Body**: `{"command": "{\"T\":1}"}`
- `GET /robot/status`: Get the last command and response from the robot.
- `POST /robot/config`: Configure the robot IP address.
  - **Body**: `{"ip": "192.168.1.100"}`

**Example API Usage**:
```bash
# Send Robot Command
curl -X POST http://localhost:5000/robot/command \
     -H "Content-Type: application/json" \
     -d '{"command": "{\"T\":1}"}'

# Configure Robot IP
curl -X POST http://localhost:5000/robot/config \
     -H "Content-Type: application/json" \
     -d '{"ip": "192.168.1.100"}'
```

## Troubleshooting

### Web Interface Issues
1.  **Port Already in Use**: If another service is using port `5000`.
    ```bash
    # Find the process using the port
    sudo netstat -tlpn | grep 5000
    # Stop the conflicting process
    sudo kill <process_id>
    ```

2.  **Camera Permission Issues**: If the user running the script cannot access `/dev/video0`.
    ```bash
    sudo usermod -a -G video $USER
    # Log out and log back in for the change to take effect.
    ```

3.  **"Camera Not Available"**:
    - Check the physical USB connection of the camera.
    - Verify camera permissions (as above).
    - Restart the application.

4.  **"Robot IP not configured"**:
    - Use the web interface to set the robot's IP address.
    - Ensure the robot is powered on and accessible on the network. 