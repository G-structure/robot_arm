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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class CameraStream:
    def __init__(self):
        self.camera = None
        self.lock = threading.Lock()
        self.frame = None
        self.initialize_camera()
        
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
    
    def get_frame(self):
        """Get the latest frame from camera"""
        if self.camera is None:
            return None
            
        ret, frame = self.camera.read()
        if ret:
            with self.lock:
                self.frame = frame.copy()
            return frame
        return None
    
    def generate_frames(self):
        """Generate frames for video streaming"""
        while True:
            frame = self.get_frame()
            if frame is not None:
                # Add timestamp and info overlay
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, f"Robot Arm Camera - {timestamp}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame, 
                                         [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # If camera fails, yield a black frame with error message
                error_frame = self.create_error_frame()
                ret, buffer = cv2.imencode('.jpg', error_frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.033)  # ~30 FPS
    
    def create_error_frame(self):
        """Create an error frame when camera is not available"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, "Camera Not Available", 
                   (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return frame
    
    def cleanup(self):
        """Clean up camera resources"""
        if self.camera:
            self.camera.release()

# Global camera stream instance
camera_stream = CameraStream()

class RobotController:
    def __init__(self, robot_ip=None):
        self.robot_ip = robot_ip
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

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(camera_stream.generate_frames(),
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

@app.route('/robot/config', methods=['POST'])
def robot_config():
    """Configure robot IP"""
    data = request.get_json()
    if not data or 'ip' not in data:
        return jsonify({"error": "No IP provided"}), 400
    
    robot_controller.robot_ip = data['ip']
    return jsonify({"success": True, "ip": data['ip']})

@app.route('/camera/info')
def camera_info():
    """Get camera information"""
    return jsonify({
        "status": "active" if camera_stream.camera and camera_stream.camera.isOpened() else "inactive",
        "resolution": "640x480",
        "fps": 30
    })

if __name__ == '__main__':
    try:
        # Run the Flask app
        app.run(host='0.0.0.0', port=3334, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        camera_stream.cleanup() 