# Network Configuration Documentation

## Hardware Specifications
- **Device**: Raspberry Pi
- **WiFi Interface**: wlan0
- **MAC Address**: 2c:cf:67:7e:4d:12
- **Maximum TX Power**: 31 dBm

## Available Networks
Primary networks detected in order of signal strength:

1. RoArm-M2
   - Signal Strength: 89%
   - Security: WPA2
   - Channel: 1
   - Rate: 135 Mbit/s

2. 🤖 - IoT
   - Signal Strength: 82%
   - Security: WPA2
   - Channel: 1
   - Rate: 270 Mbit/s

## Network Commands Reference

### Check WiFi Status
```bash
# View wireless interface details
iwconfig

# Show current connection
iw wlan0 link

# List available networks
nmcli dev wifi
```

### Connecting to a WiFi Network
To connect to a WiFi network, you can use the `nmcli` (NetworkManager command-line interface) tool. This is the recommended method as it does not interfere with other active connections like Ethernet or Tailscale.

You will need the network's name (SSID) and password. The command requires `sudo` privileges to modify network settings.

```bash
# Connect to a WiFi network
sudo nmcli dev wifi connect "YOUR_SSID" password "YOUR_PASSWORD"
```

For example, to connect to the `RoArm-M2` network:

```bash
sudo nmcli dev wifi connect "RoArm-M2" password "12345678"
```

After running the command, you can verify the connection status:
```bash
nmcli dev status
```

### Network Interface Information
```bash
# View detailed interface information
ip addr show wlan0
```

## Robot Dashboard Reverse Proxy

The robot arm dashboard is accessible on the RoArm-M2 network at `192.168.4.1:80`. To make this dashboard accessible from other networks (Tailscale, Ethernet), we use a reverse proxy setup.

### Quick Setup
Use the provided script for automated setup:
```bash
./scripts/reverse-proxy-robot-ui.sh
```

### Manual Setup
If you prefer to set it up manually:

1. **Install socat** (if not already installed):
   ```bash
   sudo apt-get update && sudo apt-get install -y socat
   ```

2. **Verify robot dashboard is accessible**:
   ```bash
   curl -I http://192.168.4.1
   ```

3. **Start the reverse proxy**:
   ```bash
   socat TCP-LISTEN:3333,fork TCP:192.168.4.1:80 &
   ```

### Access Points
Once the reverse proxy is running, the robot dashboard is accessible at:
- **Tailscale network**: `http://100.73.250.34:3333`
- **Local Ethernet network**: `http://<pi-ethernet-ip>:3333`

### Managing the Proxy
- **Check if running**: `pgrep -f "socat.*3333.*192.168.4.1:80"`
- **Stop the proxy**: `pkill -f "socat.*3333.*192.168.4.1:80"`
- **Check port usage**: `netstat -tuln | grep :3333`

### How It Works
The reverse proxy uses `socat` to:
1. Listen for incoming TCP connections on port 3333 on all network interfaces
2. Forward any received traffic to the robot dashboard at `192.168.4.1:80`
3. Return responses back to the original client

This allows devices on the Tailscale mesh network or local Ethernet to access the robot's web interface without needing direct access to the RoArm-M2 WiFi network.

## Network Architecture Notes
- Multiple IoT-specific networks are available in the environment
- RoArm-M2 appears to be a dedicated network for the robot arm
- Backup IoT networks are available with good signal strength
- Network environment supports both WPA2 and WPA3 security protocols

## Security Considerations
- All detected networks use at minimum WPA2 encryption
- Some networks offer WPA3 support for enhanced security
- Network selection should prioritize:
  1. Security protocol support
  2. Signal strength
  3. Network stability 

## Tailscale VPN Configuration
- **Interface**: tailscale0
- **IPv4 Address**: 100.73.250.34/32
- **IPv6 Addresses**:
  - fd7a:115c:a1e0::aa01:fa22/128 (Global)
  - fe80::df8f:8450:84f7:e531/64 (Link Local)
- **MTU**: 1280
- **Device Name**: sc7
- **Account**: jacobklagerros@
- **Network Type**: Tailscale Mesh VPN

### Tailscale Network Details
- Part of a large mesh network with multiple peers
- Connected to various devices across different platforms (Linux, macOS, Windows, Android)
- Notable active connections:
  - Direct connection with "wikis-macbook-pro" (100.78.104.97)
  - Connection with "lucs-macbook-air" (100.88.136.3) in idle state

### Tailscale Network Health
- Interface is UP and operational
- Point-to-Point configuration
- No route acceptance enabled (--accept-routes is false)
- Permanent IPv4/IPv6 address assignment (valid_lft forever)

### Security Notes
- Tailscale provides encrypted mesh VPN connectivity
- Each device has a unique IPv4 address in the 100.x.x.x range
- IPv6 connectivity is also configured and available
- Direct peer-to-peer connections when possible 