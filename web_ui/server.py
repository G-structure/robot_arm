#!/usr/bin/env python3
"""
Robot Arm Camera and SDR Web UI
Provides live camera stream, SDR waterfall, and robot arm control.
"""

import cv2
import json
import time
import threading
from flask import Flask, Response, render_template, request, jsonify
from flask_sock import Sock
import requests
import logging
import numpy as np
import os
import SoapySDR
from .sdr import device as sdr_device
from .sdr import signal as sdr_signal

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
            self.initialize_camera()

        if self.camera is None or not self.camera.isOpened():
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

class SDRController:
    def __init__(self, fft_size=1024, sample_rate=2.048e6):
        self.sdr = None
        self.stream = None
        self.lock = threading.Lock()
        self.is_streaming = False
        self.fft_size = fft_size
        self.sample_rate = sample_rate
        self.center_freq = 100e6
        self.gain = 30
        self.sdr_thread = None

    def initialize_sdr(self):
        try:
            args = "driver=hackrf"
            self.sdr = sdr_device.setup_sdr_device(
                device_args=args,
                sample_rate=self.sample_rate,
                center_freq=self.center_freq,
                rx_gain=self.gain
            )
            self.stream = self.sdr.setupStream(SoapySDR.SOAPY_SDR_RX, SoapySDR.SOAPY_SDR_CF32)
            self.sdr.activateStream(self.stream)
            self.is_streaming = True
            logger.info("SDR Initialized: HackRF")
            return True
        except Exception as e:
            logger.error(f"SDR Initialization Error: {e}")
            self.is_streaming = False
            return False

    def start_streaming(self, websocket):
        if not self.is_streaming:
            if not self.initialize_sdr():
                return 

        def stream_loop():
            buffer = np.empty(self.fft_size, dtype=np.complex64)
            while self.is_streaming:
                try:
                    sr = self.sdr.readStream(self.stream, [buffer], len(buffer), timeoutUs=int(1e6))
                    if sr.ret > 0:
                        psd = sdr_signal.compute_psd_db(buffer, self.fft_size)
                        websocket.send(json.dumps(psd.tolist()))
                    time.sleep(0.01)
                except Exception as e:
                    logger.error(f"SDR Streaming Error: {e}")
                    self.is_streaming = False
                    break
            self.cleanup()

        self.sdr_thread = threading.Thread(target=stream_loop)
        self.sdr_thread.start()

    def stop_streaming(self):
        with self.lock:
            self.is_streaming = False
        if self.sdr_thread:
            self.sdr_thread.join()

    def set_config(self, config):
        with self.lock:
            if 'freq' in config:
                self.center_freq = float(config['freq'])
                self.sdr.setFrequency(SoapySDR.SOAPY_SDR_RX, 0, self.center_freq)
            if 'gain' in config:
                self.gain = float(config['gain'])
                self.sdr.setGain(SoapySDR.SOAPY_SDR_RX, 0, self.gain)
            if 'rate' in config:
                self.sample_rate = float(config['rate'])
                self.sdr.setSampleRate(SoapySDR.SOAPY_SDR_RX, 0, self.sample_rate)
        return self.get_status()

    def get_status(self):
        return {
            "streaming": self.is_streaming,
            "center_freq": self.center_freq,
            "sample_rate": self.sample_rate,
            "gain": self.gain,
        }

    def cleanup(self):
        if self.stream:
            self.sdr.deactivateStream(self.stream)
            self.sdr.closeStream(self.stream)
        logger.info("SDR Stream closed.")

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
sdr_controller = SDRController()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(camera_stream.generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@sock.route('/sdr')
def sdr_feed(ws):
    logger.info("SDR WebSocket connection established.")
    sdr_controller.start_streaming(ws)
    while ws.connected:
        message = ws.receive()
        if message:
            try:
                config = json.loads(message)
                sdr_controller.set_config(config)
                ws.send(json.dumps({"status": "updated", "config": sdr_controller.get_status()}))
            except json.JSONDecodeError:
                ws.send(json.dumps({"error": "Invalid JSON"}))
        time.sleep(0.1)
    sdr_controller.stop_streaming()
    logger.info("SDR WebSocket connection closed.")

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

@app.route('/sdr/status')
def sdr_status():
    """Get SDR status"""
    return jsonify(sdr_controller.get_status())

@app.route('/camera/info')
def camera_info():
    """Get camera information"""
    return jsonify({
        "status": "active" if camera_stream.camera and camera_stream.camera.isOpened() else "inactive",
        "resolution": "640x480",
        "fps": 30
    })

def main():
    """Main entry point to run the Flask application."""
    try:
        # Run the Flask app
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        camera_stream.cleanup()
        sdr_controller.cleanup()

if __name__ == '__main__':
    main() 