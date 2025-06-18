#!/usr/bin/env python3
"""
Test script for USB webcam connectivity
"""
import cv2
import sys

def test_camera():
    print('OpenCV version:', cv2.__version__)
    print('Testing camera connection...')
    
    # Test camera connection
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print('ERROR: Could not open camera')
        return False
    
    # Try to read a frame
    ret, frame = cap.read()
    if ret:
        print('SUCCESS: Camera connection established')
        print('Frame shape:', frame.shape)
        print('Frame dtype:', frame.dtype)
        
        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f'Camera resolution: {width}x{height}')
        print(f'Camera FPS: {fps}')
        
        # Test different resolutions
        test_resolutions = [(640, 480), (1280, 720), (1920, 1080)]
        print('\nTesting different resolutions:')
        for w, h in test_resolutions:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f'  {w}x{h} -> {actual_w}x{actual_h}')
            
        cap.release()
        return True
    else:
        print('ERROR: Could not read frame from camera')
        cap.release()
        return False

if __name__ == '__main__':
    success = test_camera()
    print('Camera test completed.')
    sys.exit(0 if success else 1) 