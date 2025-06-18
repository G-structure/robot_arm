// --- Global State ---
let robotIP = '';

// --- DOM Elements ---
const feedbackBox = () => document.getElementById('feedback-box');
const jsonCommandInput = () => document.getElementById('json-command');
const cameraStatusDetail = () => document.getElementById('camera-status-detail');
const robotConnection = () => document.getElementById('robot-connection');
const lastCommand = () => document.getElementById('last-command');
const lastResponse = () => document.getElementById('last-response');

// --- Command Sending ---
async function sendCommand(jsonCmd) {
    const jsonString = typeof jsonCmd === 'string' ? jsonCmd : JSON.stringify(jsonCmd);
    try {
        const response = await fetch('/robot/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: jsonString })
        });
        const data = await response.json();
        if (feedbackBox()) {
            feedbackBox().textContent = data.response || JSON.stringify(data);
        }
        updateStatus();
    } catch (error) {
        if (feedbackBox()) {
            feedbackBox().textContent = `Error: ${error.message}`;
        }
        console.error("Command error:", error);
    }
}

async function sendRawJson() {
    const jsonString = jsonCommandInput().value;
    if (!jsonString) {
        alert("Please enter a JSON command.");
        return;
    }
    try {
        JSON.parse(jsonString); // Validate
        sendCommand(jsonString);
    } catch (error) {
        alert(`Invalid JSON: ${error.message}`);
    }
}


// --- Status Update ---
async function updateStatus() {
    // Update robot status from its own endpoint
    try {
        const response = await fetch('/robot/status');
        const data = await response.json();
        robotIP = data.robot_ip;
        if (robotConnection()) robotConnection().textContent = data.robot_ip ? `Connected to ${data.robot_ip}` : 'Not connected';
        if (lastCommand()) lastCommand().textContent = data.last_command || 'None';
        if (lastResponse()) lastResponse().textContent = data.last_response || 'None';
    } catch (error) {
        if (robotConnection()) robotConnection().textContent = 'Error getting robot status';
        console.error("Robot status error:", error);
    }

    // Get camera info
    try {
        const response = await fetch('/camera/info');
        const data = await response.json();
        if (cameraStatusDetail()) cameraStatusDetail().textContent = `${data.status} - ${data.resolution} @ ${data.fps}fps`;
    } catch (error) {
        if (cameraStatusDetail()) cameraStatusDetail().textContent = 'Error getting camera info';
        console.error("Camera status error:", error);
    }
    
    // Get robot joint/coord feedback
    const cmd = { "T": 105 }; // CMD_SERVO_RAD_FEEDBACK
    const jsonString = JSON.stringify(cmd);
     try {
        const response = await fetch(`/robot/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: jsonString })
        });
        if (!response.ok) return;
        const result = await response.json();
        const data = JSON.parse(result.response); // The actual feedback is a string within the response

        // Update angle controls
        const angleB = document.getElementById('angle-b');
        const angleS = document.getElementById('angle-s');
        const angleE = document.getElementById('angle-e');
        const angleH = document.getElementById('angle-h');
        if (angleB) angleB.textContent = data.b?.toFixed(2) ?? 'N/A';
        if (angleS) angleS.textContent = data.s?.toFixed(2) ?? 'N/A';
        if (angleE) angleE.textContent = data.e?.toFixed(2) ?? 'N/A';
        if (angleH) angleH.textContent = data.t?.toFixed(2) ?? 'N/A';

        // Update coordinate controls
        const coordX = document.getElementById('coord-x');
        const coordY = document.getElementById('coord-y');
        const coordZ = document.getElementById('coord-z');
        const coordT = document.getElementById('coord-t');
        if (coordX) coordX.textContent = data.x?.toFixed(2) ?? 'N/A';
        if (coordY) coordY.textContent = data.y?.toFixed(2) ?? 'N/A';
        if (coordZ) coordZ.textContent = data.z?.toFixed(2) ?? 'N/A';
        if (coordT) coordT.textContent = data.t?.toFixed(2) ?? 'N/A';
        
    } catch (error) {
        console.error("Failed to update status from robot:", error);
    }
}


// --- Event Listeners ---
function initializeEventListeners() {
    const sendJsonBtn = document.getElementById('send-json');
    if (sendJsonBtn) {
        sendJsonBtn.addEventListener('click', sendRawJson);
    }

    if (jsonCommandInput()) {
        jsonCommandInput().addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendRawJson();
            }
        });
    }

    // Direct control buttons
    document.querySelectorAll('.control-btn').forEach(button => {
        const mode = button.dataset.mode === 'angle' ? 0 : 1;
        const axis = parseInt(button.dataset.axis);
        const cmdVal = parseInt(button.dataset.cmd);

        const sendMoveCommand = (start) => {
            const cmd = {
                "T": 123, // CMD_CONSTANT_CTRL
                "m": mode,
                "axis": axis,
                "cmd": start ? cmdVal : 0, // 0 to stop
                "spd": 10
            };
            sendCommand(cmd);
        };

        let pressTimer;
        const startAction = (e) => {
            e.preventDefault();
            sendMoveCommand(true);
            pressTimer = setInterval(() => sendMoveCommand(true), 100);
        };
        const stopAction = () => {
            clearInterval(pressTimer);
            sendMoveCommand(false);
        };

        button.addEventListener('mousedown', startAction);
        button.addEventListener('mouseup', stopAction);
        button.addEventListener('mouseleave', stopAction);
        button.addEventListener('touchstart', startAction);
        button.addEventListener('touchend', stopAction);
    });
    
    // System buttons
    const btnInit = document.getElementById('btn-init');
    const btnTorqueOn = document.getElementById('btn-torque-on');
    const btnTorqueOff = document.getElementById('btn-torque-off');
    const btnLedOn = document.getElementById('btn-led-on');
    const btnLedOff = document.getElementById('btn-led-off');

    if(btnInit) btnInit.addEventListener('click', () => sendCommand({"T":102,"base":0,"shoulder":0,"elbow":1.5707965,"hand":3.1415926,"spd":0,"acc":0}));
    if(btnTorqueOn) btnTorqueOn.addEventListener('click', () => sendCommand({"T":210,"cmd":1}));
    if(btnTorqueOff) btnTorqueOff.addEventListener('click', () => sendCommand({"T":210,"cmd":0}));
    if(btnLedOn) btnLedOn.addEventListener('click', () => sendCommand({"T":114,"led":255}));
    if(btnLedOff) btnLedOff.addEventListener('click', () => sendCommand({"T":114,"led":0}));

    // Command Library
    const commandList = document.getElementById('command-list');
    const commandSearch = document.getElementById('command-search');
    
    if (commandList && commandSearch) {
        const commands = [
            { name: "CMD_WIFI_ON_BOOT", json: '{"T":401,"cmd":3}' },
            { name: "CMD_SET_AP", json: '{"T":402,"ssid":"RoArm-M2","password":"12345678"}' },
            { name: "CMD_SET_STA", json: '{"T":403,"ssid":"yourWifi","password":"yourPassword"}' },
            { name: "CMD_WIFI_INFO", json: '{"T":405}' },
            { name: "CMD_GET_MAC_ADDRESS", json: '{"T":302}' },
            { name: "CMD_MOVE_INIT", json: '{"T":100}' },
            { name: "CMD_JOINTS_RAD_CTRL", json: '{"T":102,"base":0,"shoulder":0,"elbow":1.57,"hand":1.57,"spd":0,"acc":10}' },
            { name: "CMD_XYZT_GOAL_CTRL", json: '{"T":104,"x":235,"y":0,"z":234,"t":3.14,"spd":0.25}' },
            { name: "CMD_SERVO_RAD_FEEDBACK", json: '{"T":105}' },
            { name: "CMD_JOINTS_ANGLE_CTRL", json: '{"T":122,"b":0,"s":0,"e":90,"h":180,"spd":10,"acc":10}' },
            { name: "CMD_SCAN_FILES", json: '{"T":200}' },
            { name: "CMD_REBOOT", json: '{"T":600}' },
            { name: "CMD_FREE_FLASH_SPACE", json: '{"T":601}' },
        ];

        const renderCommands = (filter = '') => {
            commandList.innerHTML = '';
            const filteredCommands = commands.filter(cmd => cmd.name.toLowerCase().includes(filter.toLowerCase()));
            
            filteredCommands.forEach(cmd => {
                const item = document.createElement('div');
                item.className = 'command-item';
                item.innerHTML = `<strong>${cmd.name}</strong><code>${cmd.json}</code>`;
                item.addEventListener('click', () => {
                    if (jsonCommandInput()) jsonCommandInput().value = cmd.json;
                });
                commandList.appendChild(item);
            });
        }

        commandSearch.addEventListener('input', (e) => renderCommands(e.target.value));
        renderCommands();
    }
}


// --- Page Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    updateStatus();
    setInterval(updateStatus, 2000); // Poll for status every 2 seconds
}); 