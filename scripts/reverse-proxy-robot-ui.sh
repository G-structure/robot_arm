#!/bin/bash

# Robot UI Reverse Proxy Setup Script
# This script creates a reverse proxy to expose the robot dashboard
# from the RoArm-M2 network (192.168.4.1:80) to other networks
# via the Raspberry Pi's interfaces on port 3333

echo "Setting up reverse proxy for Robot UI Dashboard..."

# Check if socat is installed
if ! command -v socat &> /dev/null; then
    echo "socat is not installed. Installing..."
    sudo apt-get update && sudo apt-get install -y socat
    if [ $? -ne 0 ]; then
        echo "Failed to install socat. Please check your internet connection and try again."
        exit 1
    fi
fi

# Check if robot dashboard is accessible
echo "Checking robot dashboard availability at 192.168.4.1..."
if ! curl --connect-timeout 5 -s -o /dev/null http://192.168.4.1; then
    echo "Warning: Cannot reach robot dashboard at 192.168.4.1"
    echo "Make sure you are connected to the RoArm-M2 WiFi network"
    echo "Continuing anyway..."
fi

# Check if port 3333 is already in use
if netstat -tuln | grep -q ":3333 "; then
    echo "Port 3333 is already in use. Checking if it's our reverse proxy..."
    if pgrep -f "socat.*3333.*192.168.4.1:80" > /dev/null; then
        echo "Reverse proxy is already running!"
        exit 0
    else
        echo "Port 3333 is occupied by another process. Please stop it or choose a different port."
        exit 1
    fi
fi

# Start the reverse proxy
echo "Starting reverse proxy on port 3333..."
socat TCP-LISTEN:3333,fork TCP:192.168.4.1:80 &
SOCAT_PID=$!

# Verify the proxy started successfully
sleep 2
if kill -0 $SOCAT_PID 2>/dev/null; then
    echo "✓ Reverse proxy started successfully (PID: $SOCAT_PID)"
    echo ""
    echo "Robot dashboard is now accessible at:"
    echo "  - Tailscale: http://100.73.250.34:3333"
    echo "  - Local network: http://<pi-ethernet-ip>:3333"
    echo ""
    echo "To stop the proxy, run: kill $SOCAT_PID"
else
    echo "✗ Failed to start reverse proxy"
    exit 1
fi 