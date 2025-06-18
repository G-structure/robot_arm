#!/bin/bash

# Robot WiFi Connection Script
# This script connects to the RoArm-M2 WiFi network and verifies connectivity

set -e

# Default robot WiFi credentials
ROBOT_SSID="RoArm-M2"
DEFAULT_PASSWORD="12345678"
ROBOT_IP="192.168.4.1"

echo "Robot WiFi Connection Script"
echo "============================"

# Function to check if NetworkManager is available
check_networkmanager() {
    if ! command -v nmcli &> /dev/null; then
        echo "Error: NetworkManager (nmcli) is not installed."
        echo "Please install it with: sudo apt-get install network-manager"
        exit 1
    fi
}

# Function to scan for available networks
scan_networks() {
    echo "Scanning for available WiFi networks..."
    nmcli dev wifi rescan
    sleep 2
}

# Function to check if robot network is available
check_robot_network() {
    echo "Checking if $ROBOT_SSID network is available..."
    if nmcli dev wifi list | grep -q "$ROBOT_SSID"; then
        echo "✓ Found $ROBOT_SSID network"
        return 0
    else
        echo "✗ $ROBOT_SSID network not found"
        echo "Available networks:"
        nmcli dev wifi list | head -10
        return 1
    fi
}

# Function to connect to robot WiFi
connect_to_robot() {
    local password=${1:-$DEFAULT_PASSWORD}
    
    echo "Attempting to connect to $ROBOT_SSID..."
    echo "Using password: $password"
    
    if sudo nmcli dev wifi connect "$ROBOT_SSID" password "$password"; then
        echo "✓ Successfully connected to $ROBOT_SSID"
        return 0
    else
        echo "✗ Failed to connect to $ROBOT_SSID"
        return 1
    fi
}

# Function to verify connection
verify_connection() {
    echo "Verifying WiFi connection..."
    
    # Check if connected to the right network
    current_ssid=$(nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2)
    if [ "$current_ssid" = "$ROBOT_SSID" ]; then
        echo "✓ Connected to $ROBOT_SSID"
    else
        echo "✗ Not connected to $ROBOT_SSID (currently connected to: $current_ssid)"
        return 1
    fi
    
    # Check IP connectivity to robot
    echo "Testing connectivity to robot at $ROBOT_IP..."
    if ping -c 3 -W 5 "$ROBOT_IP" > /dev/null 2>&1; then
        echo "✓ Robot is reachable at $ROBOT_IP"
    else
        echo "⚠ Warning: Cannot ping robot at $ROBOT_IP"
        echo "  This might be normal if the robot is not powered on"
    fi
    
    # Try to reach robot web interface
    echo "Testing robot web interface..."
    if curl --connect-timeout 5 -s -o /dev/null "http://$ROBOT_IP"; then
        echo "✓ Robot web interface is accessible at http://$ROBOT_IP"
    else
        echo "⚠ Warning: Robot web interface not accessible"
        echo "  Make sure the robot arm is powered on"
    fi
}

# Function to show connection status
show_status() {
    echo ""
    echo "Current WiFi Status:"
    echo "===================="
    nmcli dev status | grep wifi
    echo ""
    echo "Current IP configuration:"
    ip addr show wlan0 | grep inet || echo "No IP address assigned"
}

# Main script execution
main() {
    local custom_password=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--password)
                custom_password="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: $0 [-p|--password PASSWORD]"
                echo ""
                echo "Options:"
                echo "  -p, --password   Custom WiFi password (default: $DEFAULT_PASSWORD)"
                echo "  -h, --help       Show this help message"
                echo ""
                echo "This script connects to the $ROBOT_SSID WiFi network"
                echo "and verifies connectivity to the robot arm."
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Use custom password if provided, otherwise use default
    local password=${custom_password:-$DEFAULT_PASSWORD}
    
    echo "Connecting to robot WiFi network: $ROBOT_SSID"
    echo ""
    
    # Check prerequisites
    check_networkmanager
    
    # Scan for networks
    scan_networks
    
    # Check if robot network is available
    if ! check_robot_network; then
        echo ""
        echo "Troubleshooting tips:"
        echo "1. Make sure the robot arm is powered on"
        echo "2. Wait a few seconds for the robot to create its WiFi network"
        echo "3. Try scanning again: nmcli dev wifi rescan"
        exit 1
    fi
    
    # Connect to robot network
    if connect_to_robot "$password"; then
        sleep 3  # Wait for connection to stabilize
        verify_connection
        show_status
        
        echo ""
        echo "✓ Successfully connected to robot WiFi!"
        echo "You can now access the robot at: http://$ROBOT_IP"
        echo "To start the reverse proxy, run: ./scripts/reverse-proxy-robot-ui.sh"
    else
        echo ""
        echo "Connection failed. Possible issues:"
        echo "1. Incorrect password (tried: $password)"
        echo "2. Robot not powered on or network not ready"
        echo "3. WiFi adapter issues"
        echo ""
        echo "Try again with a custom password: $0 -p YOUR_PASSWORD"
        exit 1
    fi
}

# Run main function with all arguments
main "$@" 