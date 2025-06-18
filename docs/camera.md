# Robot Arm Camera Documentation

## Overview

The robot arm system includes a USB webcam for visual monitoring and potential computer vision applications. This document covers the camera setup, capabilities, and web interface.

## Hardware Information

### Camera Details
- **Model**: EMEET SmartCam C950
- **Vendor**: EMEET (ID: 328f)
- **Product ID**: 00ba
- **Serial Number**: 24082114152
- **Interface**: USB 3.0 (UVC 1.00 compatible)

### Device Files
- **Primary Video Device**: `/dev/video0`
- **Secondary Video Device**: `/dev/video1` 
- **Media Device**: `/dev/media3`

## Supported Formats and Resolutions

### Motion JPEG (MJPG) - Compressed
- 1920x1080 @ 30 FPS
- 1280x960 @ 30 FPS
- 1280x720 @ 30 FPS
- 1024x576 @ 30 FPS
- 800x600 @ 30 FPS
- 640x480 @ 30 FPS
- 640x360 @ 30 FPS

### YUYV 4:2:2 - Uncompressed
- 640x480 @ 30 FPS
- 640x360 @ 30 FPS

## Installation and Setup

### 1. Hardware Connection
1. Connect the USB webcam to any available USB port on the Raspberry Pi
2. The camera should be automatically detected and the UVC driver loaded
3. Verify detection with: `lsusb | grep EMEET`

### 2. Software Dependencies
The camera requires the following Python packages (included in `python_example/requirements.txt`):
```
opencv-python==4.11.0.86
numpy==2.0.2
flask==3.0.0
```

### 3. Installation Commands
```bash
cd python_example
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Camera Testing

### Basic Connectivity Test
Use the provided test script to verify camera functionality:
```bash
cd python_example
source venv/bin/activate
python3 test_camera.py
```

Expected output:
```
OpenCV version: 4.11.0
Testing camera connection...
SUCCESS: Camera connection established
Frame shape: (480, 640, 3)
Frame dtype: uint8
Camera resolution: 640x480
Camera FPS: 30.0
```

### Manual Testing with V4L2
```bash
# List video devices
v4l2-ctl --list-devices

# Get camera information
v4l2-ctl --device=/dev/video0 --list-formats-ext

# Test different resolutions
v4l2-ctl --device=/dev/video0 --set-fmt-video=width=1280,height=720
```

## Web Interface

### Overview
The robot arm includes a comprehensive web interface that provides:
- Live camera streaming
- Robot arm control
- System status monitoring
- Real-time command interface

### Accessing the Web Interface
- **URL**: `http://100.73.250.34:3334`
- **Local Access**: `http://localhost:3334`
- **Network Access**: Available on the Pi's Tailscale network

### Starting the Web Server
```bash
cd python_example
source venv/bin/activate
python3 camera_webui.py
```

### Web Interface Features

#### 1. Live Camera Feed
- Real-time video streaming using Motion JPEG
- 640x480 resolution at 30 FPS
- Timestamp overlay
- Automatic fallback on camera errors

#### 2. Robot Control Panel
- **Robot Configuration**: Set robot arm IP address
- **Quick Commands**: Pre-defined common commands
  - Home Position (`{"T":104}`)
  - Get Status (`{"T":1}`)
  - Stop (`{"T":2}`)
  - Reset (`{"T":3}`)
- **Custom Commands**: Send arbitrary JSON commands

#### 3. System Status
- Camera status and resolution info
- Robot connection status
- Last command sent
- Last response received

### API Endpoints

The web interface provides several REST API endpoints:

#### Camera Endpoints
- `GET /video_feed` - Live video stream
- `GET /camera/info` - Camera status and capabilities

#### Robot Control Endpoints
- `POST /robot/command` - Send JSON command to robot
- `GET /robot/status` - Get robot status
- `POST /robot/config` - Configure robot IP

### Example API Usage

#### Get Camera Info
```bash
curl http://100.73.250.34:3334/camera/info
```

#### Send Robot Command
```bash
curl -X POST http://100.73.250.34:3334/robot/command \
     -H "Content-Type: application/json" \
     -d '{"command": "{\"T\":1}"}'
```

#### Configure Robot IP
```bash
curl -X POST http://100.73.250.34:3334/robot/config \
     -H "Content-Type: application/json" \
     -d '{"ip": "192.168.1.100"}'
```

## Performance Considerations

### Camera Performance
- **Default Resolution**: 640x480 for optimal performance
- **Frame Rate**: Consistent 30 FPS
- **Encoding**: JPEG compression at 85% quality
- **Latency**: Typically <100ms for local network

### Network Performance
- **Bandwidth Usage**: ~2-4 Mbps for video stream
- **Concurrent Users**: Supports multiple viewers
- **Network Requirements**: Stable connection recommended

## Troubleshooting

### Camera Not Detected
1. Check USB connection: `lsusb | grep EMEET`
2. Verify video devices: `ls -la /dev/video*`
3. Check kernel messages: `dmesg | tail -20`

### Web Interface Issues
1. **Port Already in Use**: 
   ```bash
   sudo netstat -tlpn | grep 3334
   sudo kill <process_id>
   ```

2. **Camera Permission Issues**:
   ```bash
   sudo usermod -a -G video $USER
   # Logout and login again
   ```

3. **Virtual Environment Issues**:
   ```bash
   cd python_example
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Common Error Messages

#### "Camera Not Available"
- Check USB connection
- Verify camera permissions
- Restart the web application

#### "Robot IP not configured"
- Use the web interface to set robot IP
- Verify robot is accessible on network

## Security Considerations

### Network Security
- Web interface accessible on configured IP only
- No authentication implemented (suitable for private networks)
- Consider firewall rules for external access

### Camera Privacy
- Camera feed only accessible through web interface
- No automatic recording or storage
- Stream stops when web application is closed

## Future Enhancements

### Potential Features
- Computer vision integration
- Motion detection
- Image capture and storage
- Multi-camera support
- Authentication system
- HTTPS support

### Integration Opportunities
- Robot arm position feedback
- Visual servo control
- Object detection and tracking
- Automated operation monitoring

## Maintenance

### Regular Checks
1. Monitor camera connectivity
2. Check web server logs
3. Verify network accessibility
4. Update dependencies as needed

### Log Files
Web server logs are displayed in the terminal when running the application. For production deployment, consider implementing proper logging to files.

## Support

For issues related to the camera system:
1. Check this documentation
2. Verify hardware connections
3. Review system logs
4. Test with provided scripts

The camera system is designed to be robust and self-recovering, automatically handling temporary disconnections and errors. 