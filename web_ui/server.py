#!/usr/bin/env python3
"""
Robot Arm Camera Web UI
Provides live camera stream and control interface for the robot arm
"""

import cv2
import json
import time
import threading
from flask import Flask, Response, render_template, request, jsonify
import requests
import logging
import numpy as np
import os
from flask_sock import Sock
import uuid
from collections import deque

from web_ui.sdr.stream import SDRStreamer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
sock = Sock(app)

class CameraStream:
    def __init__(self):
        self.camera = None
        self.lock = threading.Lock()
        self.frame = None
        self.clients = set()
        self.capture_thread = None
        self.running = False
        
    def initialize_camera(self):
        """Initialize the camera"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                logger.error("Failed to open camera")
                return False
                
            # Set camera properties for better performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            logger.info("Camera initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Camera initialization error: {e}")
            return False

    def start_capture(self):
        """Start the background capture thread"""
        if self.capture_thread is not None and self.capture_thread.is_alive():
            return
            
        if not self.initialize_camera():
            return
            
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_frames)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        logger.info("Camera capture thread started")

    def stop_capture(self):
        """Stop the background capture thread"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        if self.camera:
            self.camera.release()
        logger.info("Camera capture stopped")

    def _capture_frames(self):
        """Background thread to continuously capture frames"""
        while self.running:
            if self.camera is None or not self.camera.isOpened():
                time.sleep(0.1)
                continue
                
            ret, frame = self.camera.read()
            if ret:
                # Add timestamp and info overlay
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, f"Robot Arm Camera - {timestamp}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                with self.lock:
                    self.frame = frame.copy()
            else:
                # Create error frame
                error_frame = self.create_error_frame()
                with self.lock:
                    self.frame = error_frame
                    
            time.sleep(0.033)  # ~30 FPS

    def add_client(self, client_id):
        """Register a new client"""
        with self.lock:
            self.clients.add(client_id)
            logger.info(f"Camera client added: {client_id} (total: {len(self.clients)})")
            
        # Start capture if this is the first client
        if len(self.clients) == 1:
            self.start_capture()

    def remove_client(self, client_id):
        """Unregister a client"""
        with self.lock:
            self.clients.discard(client_id)
            logger.info(f"Camera client removed: {client_id} (total: {len(self.clients)})")
            
        # Stop capture if no clients remain
        if len(self.clients) == 0:
            self.stop_capture()

    def get_frame(self):
        """Get the latest frame (thread-safe)"""
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def generate_frames(self, client_id):
        """Generate frames for a specific client"""
        self.add_client(client_id)
        try:
            while client_id in self.clients:
                frame = self.get_frame()
                if frame is not None:
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, 
                                             [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(0.033)  # ~30 FPS
        finally:
            self.remove_client(client_id)

    def create_error_frame(self):
        """Create an error frame when camera is not available"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, "Camera Not Available", 
                   (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return frame
    
    def cleanup(self):
        """Clean up camera resources"""
        self.stop_capture()

# Global camera stream instance
camera_stream = CameraStream()

# Global SDR streamer instance
sdr_streamer = SDRStreamer(app_logger=logger)

class RobotController:
    def __init__(self):
        self.robot_ip = os.environ.get("ROBOT_IP", "192.168.4.1")
        self.last_command = None
        self.last_response = None
        
    def send_command(self, command):
        """Send JSON command to robot arm"""
        if not self.robot_ip:
            return {"error": "Robot IP not configured"}
            
        try:
            url = f"http://{self.robot_ip}/js?json={command}"
            response = requests.get(url, timeout=5)
            self.last_command = command
            self.last_response = response.text
            return {"success": True, "response": response.text}
        except requests.RequestException as e:
            logger.error(f"Robot command error: {e}")
            return {"error": str(e)}
    
    def get_status(self):
        """Get robot status"""
        return {
            "last_command": self.last_command,
            "last_response": self.last_response,
            "robot_ip": self.robot_ip
        }

# Global robot controller
robot_controller = RobotController()

# In-memory job queue and result store
chatbot_job_queue = deque()
chatbot_results = {}
chatbot_pending = {}

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    logger.info(f"Video feed client connected: {client_ip}")
    
    def generate_with_cleanup():
        try:
            for frame in camera_stream.generate_frames(client_ip):
                yield frame
        except GeneratorExit:
            logger.info(f"Video feed client disconnected: {client_ip}")
        except Exception as e:
            logger.error(f"Video feed error for client {client_ip}: {e}")
    
    return Response(generate_with_cleanup(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/robot/command', methods=['POST'])
def robot_command():
    """Send command to robot"""
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({"error": "No command provided"}), 400
    
    result = robot_controller.send_command(data['command'])
    return jsonify(result)

@app.route('/robot/status')
def robot_status():
    """Get robot status"""
    return jsonify(robot_controller.get_status())

@app.route('/camera/info')
def camera_info():
    """Get camera information"""
    return jsonify({
        "status": "active" if camera_stream.camera and camera_stream.camera.isOpened() else "inactive",
        "resolution": "640x480",
        "fps": 30
    })

@app.route('/chatbot', methods=['POST'])
def chatbot_enqueue():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided.'}), 400
    user_message = data['message']
    job_id = str(uuid.uuid4())
    job = {'job_id': job_id, 'message': user_message}
    chatbot_job_queue.append(job)
    chatbot_pending[job_id] = job
    return jsonify({'job_id': job_id})

@app.route('/chatbot/result/<job_id>', methods=['GET'])
def chatbot_result(job_id):
    result = chatbot_results.get(job_id)
    if result:
        return jsonify(result)
    elif job_id in chatbot_pending:
        return jsonify({'status': 'pending'})
    else:
        return jsonify({'error': 'Job not found'}), 404

@app.route('/chatbot/next', methods=['GET'])
def chatbot_next():
    if chatbot_job_queue:
        job = chatbot_job_queue.popleft()
        return jsonify({'job_id': job['job_id'], 'message': job['message']})
    else:
        return jsonify({'status': 'no_jobs'})

@app.route('/chatbot/submit', methods=['POST'])
def chatbot_submit():
    data = request.get_json()
    job_id = data.get('job_id')
    reply = data.get('reply')
    logprobs = data.get('logprobs')
    expert_groups = data.get('expert_groups')
    if not job_id or reply is None:
        return jsonify({'error': 'Missing job_id or reply'}), 400
    chatbot_results[job_id] = {
        'reply': reply,
        'logprobs': logprobs,
        'expert_groups': expert_groups
    }
    chatbot_pending.pop(job_id, None)
    return jsonify({'status': 'ok'})

@sock.route('/sdr')
def sdr_socket(ws):
    """SDR data websocket."""
    logger.info("SDR WebSocket client connected.")
    sdr_streamer.add_client(ws)
    try:
        while True:
            # Keep the connection alive. Data is broadcasted from the streamer thread.
            # We can receive control messages here if we want.
            message = ws.receive()
            if message:
                try:
                    # TODO: Implement control messages from client
                    data = json.loads(message)
                    logger.info(f"Received SDR control message: {data}")
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from SDR client: {message}")

    except Exception as e:
        logger.info(f"SDR WebSocket client disconnected: {e}")
    finally:
        sdr_streamer.remove_client(ws)
        logger.info("SDR WebSocket client removed.")

@app.route('/sdr/settings', methods=['GET', 'POST'])
def sdr_settings():
    """Get or update SDR settings."""
    if request.method == 'POST':
        settings = request.get_json()
        if not settings:
            return jsonify({"error": "No settings provided"}), 400
        logger.info(f"Updating SDR settings: {settings}")
        sdr_streamer.update_settings(settings)
        return jsonify({"success": True, "message": "Settings updated."})
    else:
        return jsonify(sdr_streamer.get_status())

@app.route('/sdr/status')
def sdr_status():
    """Get SDR status."""
    return jsonify(sdr_streamer.get_status())

def main():
    """Main entry point to run the Flask application."""
    try:
        # Run the Flask app
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Clean up camera resources
        camera_stream.cleanup()
        logger.info("Cleanup complete")

if __name__ == '__main__':
    main() 