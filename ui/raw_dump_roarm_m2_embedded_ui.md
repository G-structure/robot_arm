# RoArm-M2 Web UI Documentation

This document provides a complete overview of the features available in the RoArm-M2 web user interface. The UI allows for direct control of the robotic arm, configuration of its settings, and execution of complex command sequences.

The UI is divided into several main sections:
- **AngleCtrl**: For controlling individual joints.
- **CoordCtrl**: For controlling the arm's end-effector in a Cartesian coordinate system.
- **Feedback Information**: To display feedback from the arm and send custom JSON commands.
- **Pre-defined JSON Commands**: A list of commands for various functionalities.

## Main Controls

### Angle Control (`AngleCtrl`)

This section allows for manual control of each of the arm's joints.

- **Joint Controls**: The UI provides controls for four joints:
    - **B**: Base joint
    - **S**: Shoulder joint
    - **E**: Elbow joint
    - **H**: Hand/gripper joint
- **Movement**: Each joint has a pair of buttons for movement in two directions (e.g., Left/Right for the Base, Up/Down for the Shoulder and Elbow).
    - Pressing and holding a button moves the joint continuously.
    - Releasing the button stops the movement.
    - The numbers displayed above each control group show the current angle/position of the respective joint. This value is updated periodically.
    - The underlying command sent is `{"T": 123, "m": 0, "axis": [1-4], "cmd": [1-2], "spd": 10}`. `m:0` indicates Angle control mode. `axis` specifies the joint. `cmd` specifies direction. On release, `cmd:0` is sent to stop.
- **INIT Button**:
    - This button initializes the arm to a default position.
    - It sends the command `{"T":102,"base":0,"shoulder":0,"elbow":1.5707965,"hand":3.1415926,"spd":0,"acc":0}` which corresponds to setting the base to 0 rad, shoulder to 0 rad, elbow to ~90 degrees, and hand to ~180 degrees.

### Coordinate Control (`CoordCtrl`)

This section allows for controlling the end-effector's position and orientation in 3D space.

- **Coordinate Controls**:
    - **X, Y, Z**: Control the Cartesian position of the end-effector.
    - **T**: Controls the tool's rotation.
- **Movement**: Each axis has `+` and `-` buttons for movement.
    - The numbers displayed above each control group show the current coordinate value.
    - The underlying command is `{"T": 123, "m": 1, "axis": [1-4], "cmd": [1-2], "spd": 10}`. `m:1` indicates Coordinate control mode.
- **INIT Button**:
    - This performs the same initialization as the one in the `AngleCtrl` section.

## Other Controls

Below the `AngleCtrl` section, there are several buttons for toggling different states or modes.

- **Torque ON/OFF**:
    - These buttons enable or disable torque for all motors. When torque is off, the arm can be moved by hand.
    - **Torque OFF**: `{"T":210,"cmd":0}`
    - **Torque ON**: `{"T":210,"cmd":1}`
- **DEFA ON/OFF**:
    - Controls "Dynamic Adaptation".
    - **DEFA OFF**: `{"T":112,"mode":0,"b":60,"s":110,"e":50,"h":50}`
    - **DEFA ON**: `{"T":112,"mode":1,"b":60,"s":110,"e":50,"h":50}`
- **LED ON/OFF**:
    - Controls the onboard LED.
    - **LED OFF**: `{"T":114,"led":0}`
    - **LED ON**: `{"T":114,"led":255}`
- **HORIZONTAL DRAG / VERTICAL DRAG**:
    - These buttons navigate to different pages (`/horiDrag` and `/vertDrag`) for specialized drag-to-teach modes. Their functionality is not detailed in this main UI page.

## Feedback and Manual Commands

### Feedback Display

- A text area under "Feedback infomation" (`GetInfoText`) displays responses from the robot arm. This is where status messages, command acknowledgements, and data from queries are shown.

### Manual JSON Command Input

- A text area (`jsonData`) allows you to type or paste custom JSON commands to send to the arm.
- The **SEND** button sends the JSON string from the text area to the robot.
- Pressing the `Enter` key also sends the command.

## Pre-defined JSON Commands

The UI provides a long, scrollable list of pre-defined commands. Clicking on any of these commands copies its JSON representation into the manual command input area, from where it can be sent. The commands are grouped by functionality.

### WIFI SETTINGS

- **CMD_WIFI_ON_BOOT**: `{"T":401,"cmd":3}`
- **CMD_SET_AP**: `{"T":402,"ssid":"RoArm-M2","password":"12345678"}`
- **CMD_SET_STA**: `{"T":403,"ssid":"yourWifi","password":"yourPassword"}`
- **CMD_WIFI_APSTA**: `{"T":404,"ap_ssid":"RoArm-M2","ap_password":"12345678","sta_ssid":"yourWifi","sta_password":"yourPassword"}`
- **CMD_WIFI_INFO**: `{"T":405}`
- **CMD_WIFI_CONFIG_CREATE_BY_STATUS**: `{"T":406}`
- **CMD_WIFI_CONFIG_CREATE_BY_INPUT**: `{"T":407,"mode":3,"ap_ssid":"RoArm-M2","ap_password":"12345678","sta_ssid":"yourWifi","sta_password":"yourPassword"}`

### ESP-NOW SETTINGS

- **CMD_BROADCAST_FOLLOWER**: `{"T":300,"mode":0,"mac":"CC:DB:A7:5B:E4:1C"}`
- **CMD_ESP_NOW_CONFIG**: `{"T":301,"mode":0,"dev":0,"cmd":0,"megs":0}`
- **CMD_GET_MAC_ADDRESS**: `{"T":302}`
- **CMD_ESP_NOW_ADD_FOLLOWER**: `{"T":303,"mac":"CC:DB:A7:5B:E4:1C"}`
- **CMD_ESP_NOW_REMOVE_FOLLOWER**: `{"T":304,"mac":"CC:DB:A7:5B:E4:1C"}`
- **CMD_ESP_NOW_MANY_CTRL**: `{"T":305,"dev":0,"b":0,"s":0,"e":1.57,"h":1.57,"cmd":0,"megs":"hello!"}`
- **CMD_ESP_NOW_SINGLE**: `{"T":306,"mac":"FF:FF:FF:FF:FF:FF","dev":0,"b":0,"s":0,"e":1.57,"h":1.57,"cmd":0,"megs":"hello!"}`

### TORQUE CTRL

- **CMD_TORQUE_CTRL**: `{"T":210,"cmd":0}`

### DYNAMIC ADAPTATION

- **CMD_SET_NEW_X**: `{"T":112,"mode":1,"b":60,"s":110,"e":50,"h":50}`

### MOVING CTRL

- **CMD_MOVE_INIT**: `{"T":100}`
- **CMD_SINGLE_JOINT_CTRL**: `{"T":101,"joint":0,"rad":0,"spd":0,"acc":10}`
- **CMD_JOINTS_RAD_CTRL**: `{"T":102,"base":0,"shoulder":0,"elbow":1.57,"hand":1.57,"spd":0,"acc":10}`
- **CMD_XYZT_GOAL_CTRL**: `{"T":104,"x":235,"y":0,"z":234,"t":3.14,"spd":0.25}`
- **CMD_XYZT_DIRECT_CTRL**: `{"T":1041,"x":235,"y":0,"z":234,"t":3.14}`
- **CMD_SERVO_RAD_FEEDBACK**: `{"T":105}`
- **CMD_EOAT_HAND_CTRL**: `{"T":106,"cmd":3.14,"spd":0,"acc":0}`
- **CMD_SINGLE_JOINT_ANGLE**: `{"T":121,"joint":1,"angle":0,"spd":10,"acc":10}`
- **CMD_JOINTS_ANGLE_CTRL**: `{"T":122,"b":0,"s":0,"e":90,"h":180,"spd":10,"acc":10}`
- **CMD_CONSTANT_CTRL**: `{"T":123,"m":0,"axis":0,"cmd":0,"spd":0}`
- **CMD_DELAY_MILLIS**: `{"T":111,"cmd":3000}`

### EOAT CTRL

- **CMD_EOAT_TYPE**: `{"T":1,"mode":0}`
- **CMD_CONFIG_EOAT**: `{"T":2,"pos":3,"ea":0,"eb":20}`
- **CMD_EOAT_GRAB_TORQUE**: `{"T":107,"tor":200}`

### JOINTS PID CTRL

- **CMD_SET_JOINT_PID**: `{"T":108,"joint":3,"p":16,"i":0}`
- **CMD_RESET_PID**: `{"T":109}`

### SET X-AXIS

- **CMD_SET_NEW_X**: `{"T":110,"xAxisAngle":0}`

### MISSION & STEPS EDIT

- **CMD_CREATE_MISSION**: `{"T":220,"name":"mission_a","intro":"test mission created in flash."}`
- **CMD_MISSION_CONTENT**: `{"T":221,"name":"mission_a"}`
- **CMD_APPEND_STEP_JSON**: `{"T":222,"name":"mission_a","step":"{\"T\":104,\"x\":235,\"y\":0,\"z\":234,\"t\":3.14,\"spd\":0.25}"}`
- **CMD_APPEND_STEP_FB**: `{"T":223,"name":"mission_a","spd":0.25}`
- **CMD_APPEND_DELAY**: `{"T":224,"name":"mission_a","delay":3000}`
- **CMD_INSERT_STEP_JSON**: `{"T":225,"name":"mission_a","stepNum":3,"step":"{\"T\":114,\"led\":255}"}`
- **CMD_INSERT_STEP_FB**: `{"T":226,"name":"mission_a","stepNum":3,"spd":0.25}`
- **CMD_INSERT_DELAY**: `{"T":227,"stepNum":3,"delay":3000}`
- **CMD_REPLACE_STEP_JSON**: `{"T":228,"name":"mission_a","stepNum":3,"step":"{\"T\":114,\"led\":255}"}`
- **CMD_REPLACE_STEP_FB**: `{"T":229,"name":"mission_a","stepNum":3}`
- **CMD_REPLACE_DELAY**: `{"T":230,"name":"mission_a","stepNum":3,"delay":3000}`
- **CMD_DELETE_STEP**: `{"T":231,"name":"mission_a","stepNum":3}`
- **CMD_MOVE_TO_STEP**: `{"T":241,"name":"mission_a","stepNum":3}`
- **CMD_MISSION_PLAY**: `{"T":242,"name":"mission_a","times":3}`

### FILE SYSTEM CTRL

- **CMD_SCAN_FILES**: `{"T":200}`
- **CMD_CREATE_FILE**: `{"T":201,"name":"file.txt","content":"inputContentHere."}`
- **CMD_READ_FILE**: `{"T":202,"name":"file.txt"}`
- **CMD_DELETE_FILE**: `{"T":203,"name":"file.txt"}`
- **CMD_APPEND_LINE**: `{"T":204,"name":"file.txt","content":"inputContentHere."}`
- **CMD_INSERT_LINE**: `{"T":205,"name":"file.txt","lineNum":3,"content":"content"}`
- **CMD_REPLACE_LINE**: `{"T":206,"name":"file.txt","lineNum":3,"content":"Content"}`
- **CMD_READ_LINE**: `{"T":207,"name":"file.txt","lineNum":3}`
- **CMD_DELETE_LINE**: `{"T":208,"name":"file.txt","lineNum":3}`

### SWITCH CTRL

- **CMD_SWITCH_CTRL**: `{"T":113,"pwm_a":-255,"pwm_b":-255}`
- **CMD_LIGHT_CTRL**: `{"T":114,"led":255}`
- **CMD_SWITCH_OFF**: `{"T":115}`

### SERVO SETTINGS

- **CMD_SET_SERVO_ID**: `{"T":501,"raw":1,"new":11}`
- **CMD_SET_MIDDLE**: `{"T":502,"id":11}`
- **CMD_SET_SERVO_PID**: `{"T":503,"id":14,"p":16}`

### ESP32 SETTINGS

- **CMD_REBOOT**: `{"T":600}`
- **CMD_FREE_FLASH_SPACE**: `{"T":601}`
- **CMD_BOOT_MISSION_INFO**: `{"T":602}`
- **CMD_RESET_BOOT_MISSION**: `{"T":603}`
- **CMD_NVS_CLEAR**: `{"T":604}`
- **CMD_INFO_PRINT**: `{"T":605,"cmd":1}` 