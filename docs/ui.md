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

## How It Works: Data Flow

The web interface is a dynamic application that communicates with a backend server to control the robot and display real-time data. Here's a brief overview of what happens when you use different parts of the UI.

### Robot Controls

When you click a control button (e.g., move a joint) or send a custom JSON command:
1.  Your browser sends the command to the web server over an HTTP POST request.
2.  The server forwards this command to the robot arm's controller.
3.  The robot's response is sent back to the server, which then displays it in the "Feedback Log" on the UI.
4.  The status panel is updated periodically to show the last command sent and the last response received.

### Camera Feed

The live video is not streamed directly from the camera to your browser. Instead:
1.  The backend server continuously captures frames from the connected USB camera.
2.  It streams these frames as a Motion JPEG (MJPEG) feed.
3.  The `<img>` tag in the UI points to this server endpoint, rendering the sequence of images as a live video. This is an efficient method for low-latency video streaming in web applications.

### SDR Waterfall

The real-time spectrum analyzer is powered by a WebSocket connection:
1.  When the page loads, the UI establishes a persistent WebSocket connection to the server.
2.  On the server, a dedicated process reads data from the connected SDR device (e.g., HackRF).
3.  This data is processed into a Power Spectral Density (PSD) array.
4.  The server broadcasts this array over the WebSocket to all connected clients.
5.  The JavaScript in your browser receives this data and renders it onto the waterfall canvas, creating the real-time display.

### Chatbot

The chatbot feature is designed to be non-blocking, allowing for potentially long-running language model inference without freezing the UI.
1.  When you send a message, it's submitted to the server, which creates a "job" and returns a unique Job ID.
2.  A separate program, the **Chatbot Worker**, constantly asks the server for new jobs.
3.  The server gives your job to the worker.
4.  The worker processes the job (e.g., by calling a language model) and submits the reply back to the server.
5.  Meanwhile, your browser periodically asks the server if the job is done. Once the result is ready, it's fetched and displayed in the chat window.

This architecture is explained with more technical detail in the **[System Architecture document](architecture.md)**.

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

### Chatbot API Endpoints
The server includes a set of endpoints to manage a job queue for an external chatbot worker. This allows the UI to offload model inference to a separate process.

- `POST /chatbot`
  - **Description**: Called by the frontend to submit a new chatbot message from the user. The server adds the message to a job queue.
  - **Request Body**: `{"message": "Your question for the chatbot."}`
  - **Response**: `{"job_id": "a-unique-job-identifier"}`

- `GET /chatbot/next`
  - **Description**: Called by a chatbot worker to request the next available job from the queue.
  - **Response (Job Available)**: `{"job_id": "...", "message": "..."}`
  - **Response (No Jobs)**: `{"status": "no_jobs"}`

- `POST /chatbot/submit`
  - **Description**: Called by a chatbot worker to submit the results of a completed job.
  - **Request Body**: `{"job_id": "...", "reply": "...", "logprobs": [...], "expert_groups": [...]}`
  - **Response**: `{"status": "ok"}`

- `GET /chatbot/result/<job_id>`
  - **Description**: Called by the frontend to poll for the result of a specific job.
  - **Response (Pending)**: `{"status": "pending"}`
  - **Response (Complete)**: `{"reply": "...", "logprobs": [...], "expert_groups": [...]}`
  - **Response (Not Found)**: `{"error": "Job not found"}`, 404 status code.

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