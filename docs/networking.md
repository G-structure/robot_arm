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

### Network Interface Information
```bash
# View detailed interface information
ip addr show wlan0
```

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