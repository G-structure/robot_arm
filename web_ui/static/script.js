document.addEventListener('DOMContentLoaded', () => {
    const feedbackBox = document.getElementById('feedback-box');
    const jsonCommandInput = document.getElementById('json-command');

    // --- Command Sending ---
    async function sendCommand(jsonCmd) {
        const jsonString = JSON.stringify(jsonCmd);
        try {
            const response = await fetch(`/api/command?json=${encodeURIComponent(jsonString)}`);
            const data = await response.text();
            feedbackBox.textContent = data;
            updateStatus(); // Refresh data after sending a command
        } catch (error) {
            feedbackBox.textContent = `Error: ${error.message}`;
        }
    }

    async function sendRawJson() {
        const jsonString = jsonCommandInput.value;
        try {
            // Validate if it's a valid JSON object string
            JSON.parse(jsonString);
            const response = await fetch(`/api/command?json=${encodeURIComponent(jsonString)}`);
            const data = await response.text();
            feedbackBox.textContent = data;
            updateStatus();
        } catch (error) {
            feedbackBox.textContent = `Error: Invalid JSON or failed to send. ${error.message}`;
        }
    }

    // --- Status Update ---
    async function updateStatus() {
        const cmd = { "T": 105 }; // CMD_SERVO_RAD_FEEDBACK
        const jsonString = JSON.stringify(cmd);
        try {
            const response = await fetch(`/api/command?json=${encodeURIComponent(jsonString)}`);
            if (!response.ok) return;
            const data = await response.json();

            // Update angle controls
            document.getElementById('angle-b').textContent = data.b?.toFixed(2) ?? 'N/A';
            document.getElementById('angle-s').textContent = data.s?.toFixed(2) ?? 'N/A';
            document.getElementById('angle-e').textContent = data.e?.toFixed(2) ?? 'N/A';
            document.getElementById('angle-h').textContent = data.t?.toFixed(2) ?? 'N/A'; // Note: t is hand

            // Update coordinate controls
            document.getElementById('coord-x').textContent = data.x?.toFixed(2) ?? 'N/A';
            document.getElementById('coord-y').textContent = data.y?.toFixed(2) ?? 'N/A';
            document.getElementById('coord-z').textContent = data.z?.toFixed(2) ?? 'N/A';
            document.getElementById('coord-t').textContent = data.t?.toFixed(2) ?? 'N/A';
            
        } catch (error) {
            // Do not pollute feedback box on silent refresh fails
            console.error("Failed to update status:", error);
        }
    }

    // --- Event Listeners ---
    document.getElementById('send-json').addEventListener('click', sendRawJson);
    jsonCommandInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendRawJson();
        }
    });

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

        button.addEventListener('mousedown', () => sendMoveCommand(true));
        button.addEventListener('mouseup', () => sendMoveCommand(false));
        button.addEventListener('mouseleave', () => sendMoveCommand(false));
        button.addEventListener('touchstart', (e) => {
            e.preventDefault();
            sendMoveCommand(true);
        });
        button.addEventListener('touchend', () => sendMoveCommand(false));
    });
    
    // System buttons
    document.getElementById('btn-init').addEventListener('click', () => sendCommand({"T":102,"base":0,"shoulder":0,"elbow":1.5707965,"hand":3.1415926,"spd":0,"acc":0}));
    document.getElementById('btn-torque-on').addEventListener('click', () => sendCommand({"T":210,"cmd":1}));
    document.getElementById('btn-torque-off').addEventListener('click', () => sendCommand({"T":210,"cmd":0}));
    document.getElementById('btn-led-on').addEventListener('click', () => sendCommand({"T":114,"led":255}));
    document.getElementById('btn-led-off').addEventListener('click', () => sendCommand({"T":114,"led":0}));

    // --- Command Library ---
    const commandList = document.getElementById('command-list');
    const commandSearch = document.getElementById('command-search');
    
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

    function renderCommands(filter = '') {
        commandList.innerHTML = '';
        const filteredCommands = commands.filter(cmd => cmd.name.toLowerCase().includes(filter.toLowerCase()));
        
        filteredCommands.forEach(cmd => {
            const item = document.createElement('div');
            item.className = 'command-item';
            item.innerHTML = `<strong>${cmd.name}</strong><code>${cmd.json}</code>`;
            item.addEventListener('click', () => {
                jsonCommandInput.value = cmd.json;
            });
            commandList.appendChild(item);
        });
    }

    commandSearch.addEventListener('input', (e) => renderCommands(e.target.value));
    
    // Initial setup
    renderCommands();
    updateStatus();
    setInterval(updateStatus, 2000); // Poll for status every 2 seconds
}); 