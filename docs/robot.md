# Controlling the RoArm-M2-S Robot Arm via HTTP

This document outlines the procedure for controlling the RoArm-M2-S robot arm using HTTP requests. The primary method described uses Python, with notes on potential implementation using JavaScript and HTML.

## Network Connection

To communicate with the robot arm, you must first connect to its Wi-Fi network.

1.  **Power on** the robot arm.
2.  The arm will create a Wi-Fi Access Point (AP). The network name (SSID) is typically `RoArm-M2`.
3.  Connect your computer to this network.
4.  The robot arm's web server will usually be available at a static IP address, which is often `192.168.4.1` in AP mode. The IP address may be displayed on the robot's OLED screen upon startup.

## Control via Python

Communication with the arm is performed by sending JSON-formatted commands via HTTP GET requests.

### Python Example

The provided `python_example/http_simple_ctrl.py` script demonstrates this process.

```python
import requests
import argparse


def main():
    parser = argparse.ArgumentParser(description='Http JSON Communication')
    parser.add_argument('ip', type=str, help='IP address: 192.168.4.1')

    args = parser.parse_args()

    ip_addr = args.ip

    try:
        while True:
            command = input("input your json cmd: ")
            url = "http://" + ip_addr + "/js?json=" + command
            response = requests.get(url)
            content = response.text
            print(content)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
```

### Usage

1.  Run the script from your terminal, passing the robot arm's IP address as an argument:
    ```bash
    python python_example/http_simple_ctrl.py 192.168.4.1
    ```

2.  The script will prompt you to enter JSON commands.

### Example Commands

-   **Get Device Information:**
    ```json
    {"T":100}
    ```
-   **Set all servo angles to middle position (180 degrees):**
    ```json
    {"T":2,"angle_array":[180,180,180,180,180]}
    ```

For a full list of commands, refer to the official Waveshare `RoArm-M2-S_JSON_Command_Meaning` documentation.

## Speculative: Control with JavaScript and HTML

It is theoretically possible to control the robot arm using a custom web interface built with HTML and JavaScript, as the control mechanism relies on standard HTTP requests. This has not been tested but provides a potential avenue for creating a user-friendly, browser-based controller.

The core of this approach would be using the `fetch` API in JavaScript to send commands to the robot arm.

### Conceptual JavaScript Example

```javascript
// This is a conceptual, untested example.

async function sendRobotCommand(command) {
  const ipAddress = '192.168.4.1'; // Robot arm IP
  const url = `http://${ipAddress}/js?json=${encodeURIComponent(JSON.stringify(command))}`;

  try {
    const response = await fetch(url);
    const responseData = await response.text();
    console.log('Robot Response:', responseData);
  } catch (error) {
    console.error('Error sending command:', error);
  }
}

// Example: send command to get device info
sendRobotCommand({ T: 100 });

// Example: send command to move servos
const moveCommand = {
    "T": 2,
    "angle_array": [180, 180, 180, 180, 180]
};
sendRobotCommand(moveCommand);
```

This script could be embedded in an HTML file with buttons or sliders to generate and send commands, creating a rich control interface that can be accessed from any web browser on the same network. 