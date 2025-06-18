// --- Global State ---
let robotIP = '';
let spectrum = null;
let sdrSocket = null;

// --- Three.js 3D Model State ---
let scene, camera, renderer, controls;
let robotModel = {}; // To hold the 3D model parts

// --- DOM Elements ---
const feedbackBox = () => document.getElementById('feedback-box');
const jsonCommandInput = () => document.getElementById('json-command');
const cameraStatusDetail = () => document.getElementById('camera-status-detail');
const robotConnection = () => document.getElementById('robot-connection');
const lastCommand = () => document.getElementById('last-command');
const lastResponse = () => document.getElementById('last-response');

// --- Robot State for 3D Model ---
const robotState = {
    base: 0,     // 0° = facing forward
    shoulder: 2, // ~2° = shoulder pointing straight up (init position)
    elbow: 90,   // 90° = elbow at 90 degrees
    hand: 180,   // 180° = hand closed/facing down (init position)
    gripper: 15,
};

// --- THREE.js Scene Setup ---
async function initThree() {
    // Import Three.js modules dynamically
    const THREE = await import('three');
    const { OrbitControls } = await import("https://cdn.jsdelivr.net/npm/three@0.166.1/examples/jsm/controls/OrbitControls.js");
    
    const container = document.getElementById('robot-container-3d');
    if (!container) return;

    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a2a);
    scene.fog = new THREE.Fog(0x05051f, 10, 50);

    // Camera
    camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(4, 4, 6);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);
    
    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(8, 10, 5);
    dirLight.castShadow = true;
    dirLight.shadow.camera.top = 4;
    dirLight.shadow.camera.bottom = -4;
    dirLight.shadow.camera.left = -4;
    dirLight.shadow.camera.right = 4;
    dirLight.shadow.camera.near = 0.1;
    dirLight.shadow.camera.far = 40;
    scene.add(dirLight);
    
    const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
    fillLight.position.set(-8, 5, -5);
    scene.add(fillLight);

    // Ground Plane
    const ground = new THREE.Mesh(
        new THREE.PlaneGeometry(30, 30),
        new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.8 })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    // Controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 1.5, 0);
    controls.update();
    controls.enableDamping = true;

    // Robot Model
    await createRobotModel(THREE);

    // Resize listener
    window.addEventListener('resize', onWindowResize);
    
    // Start animation loop
    animate();
}

async function createRobotModel(THREE) {
    // --- Materials ---
    const aluminumMaterial = new THREE.MeshStandardMaterial({ color: 0x4B4B4B, roughness: 0.3, metalness: 0.8 });
    const servoMaterial = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.7 });
    const goldMaterial = new THREE.MeshStandardMaterial({ color: 0xdaa520, roughness: 0.3, metalness: 0.8 });
    const pcbMaterial = new THREE.MeshStandardMaterial({ color: 0x004d2b, roughness: 0.8 });
    
    // --- Base Assembly (Static Part) ---
    const baseAssembly = new THREE.Group();
    scene.add(baseAssembly);

    const pcbPlate = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.05, 1.6), pcbMaterial);
    pcbPlate.position.y = 0.025;
    pcbPlate.castShadow = true;
    pcbPlate.receiveShadow = true;
    baseAssembly.add(pcbPlate);

    const standoffHeight = 0.2;
    const standoffRadius = 0.04;
    const standoffPositions = [
        { x: 0.7, z: 0.7 }, { x: -0.7, z: 0.7 },
        { x: 0.7, z: -0.7 }, { x: -0.7, z: -0.7 }
    ];
    standoffPositions.forEach(pos => {
        const standoff = new THREE.Mesh(new THREE.CylinderGeometry(standoffRadius, standoffRadius, standoffHeight, 8), goldMaterial);
        standoff.position.set(pos.x, standoffHeight / 2 + 0.05, pos.z);
        standoff.castShadow = true;
        baseAssembly.add(standoff);
    });

    const midPlate = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.1, 1.5), aluminumMaterial);
    midPlate.position.y = standoffHeight + 0.1;
    midPlate.castShadow = true;
    baseAssembly.add(midPlate);
    
    // --- J1: Base Pivot ---
    robotModel.base_pivot = new THREE.Group();
    robotModel.base_pivot.position.y = midPlate.position.y + 0.05;
    baseAssembly.add(robotModel.base_pivot);

    // Turntable and shoulder servo housing
    const turntable = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.7, 0.2, 64), servoMaterial);
    turntable.position.y = 0.1;
    robotModel.base_pivot.add(turntable);

    const shoulderServoHousing = new THREE.Group();
    shoulderServoHousing.position.y = 0.2;
    robotModel.base_pivot.add(shoulderServoHousing);

    const housingSideGeo = new THREE.BoxGeometry(0.2, 0.8, 0.8);
    const housingSide1 = new THREE.Mesh(housingSideGeo, aluminumMaterial);
    housingSide1.position.set(0.5, 0.4, 0);
    shoulderServoHousing.add(housingSide1);
    const housingSide2 = new THREE.Mesh(housingSideGeo, aluminumMaterial);
    housingSide2.position.set(-0.5, 0.4, 0);
    shoulderServoHousing.add(housingSide2);
    
    const servoBodyGeo = new THREE.BoxGeometry(0.4, 0.6, 0.5);
    const shoulderServo1 = new THREE.Mesh(servoBodyGeo, servoMaterial);
    shoulderServo1.position.set(0.2, 0.4, 0);
    shoulderServoHousing.add(shoulderServo1);
    const shoulderServo2 = new THREE.Mesh(servoBodyGeo, servoMaterial);
    shoulderServo2.position.set(-0.2, 0.4, 0);
    shoulderServoHousing.add(shoulderServo2);

    // --- J2: Shoulder Pivot ---
    robotModel.shoulder_pivot = new THREE.Group();
    robotModel.shoulder_pivot.position.y = 0.4;
    shoulderServoHousing.add(robotModel.shoulder_pivot);
    
    const shoulderHorn = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 1.0, 16), aluminumMaterial);
    shoulderHorn.rotation.x = Math.PI / 2;
    robotModel.shoulder_pivot.add(shoulderHorn);

    // Lower Arm
    const armLength = 2.2;
    const armWidth = 0.4;
    const lowerArm = new THREE.Mesh(new THREE.BoxGeometry(armWidth, armLength, armWidth), aluminumMaterial);
    lowerArm.geometry.translate(0, armLength / 2, 0);
    lowerArm.castShadow = true;
    robotModel.shoulder_pivot.add(lowerArm);
    
    // --- J3: Elbow Pivot ---
    robotModel.elbow_pivot = new THREE.Group();
    robotModel.elbow_pivot.position.y = armLength;
    robotModel.shoulder_pivot.add(robotModel.elbow_pivot);

    const elbowMount = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.5, 0.5), aluminumMaterial);
    robotModel.elbow_pivot.add(elbowMount);
    const elbowServo = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.6, 32), servoMaterial);
    elbowServo.rotation.z = Math.PI / 2;
    elbowMount.add(elbowServo);
    
    // Forearm
    const forearmLength = 2.2;
    const forearm = new THREE.Mesh(
        new THREE.CylinderGeometry(0.18, 0.15, forearmLength, 32),
        aluminumMaterial
    );
    forearm.geometry.translate(0, forearmLength / 2, 0);
    forearm.castShadow = true;
    forearm.position.y = 0.25;
    robotModel.elbow_pivot.add(forearm);

    // --- J4: Hand Pivot ---
    robotModel.hand_pivot = new THREE.Group();
    robotModel.hand_pivot.position.y = forearmLength + 0.25;
    robotModel.elbow_pivot.add(robotModel.hand_pivot);

    const wristServoMount = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.4, 0.4), servoMaterial);
    robotModel.hand_pivot.add(wristServoMount);
    
    // --- Gripper and Light ---
    const gripperAssembly = new THREE.Group();
    gripperAssembly.position.y = 0.2;
    wristServoMount.add(gripperAssembly);

    const gripperBase = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.1, 0.3), aluminumMaterial);
    gripperBase.castShadow = true;
    gripperAssembly.add(gripperBase);

    // Gripper prongs
    robotModel.prong1 = new THREE.Group();
    robotModel.prong2 = new THREE.Group();
    
    const prongGeo = new THREE.BoxGeometry(0.05, 0.2, 0.1);
    const prong1Mesh = new THREE.Mesh(prongGeo, aluminumMaterial);
    prong1Mesh.position.set(0.1, 0.1, 0);
    prong1Mesh.castShadow = true;
    robotModel.prong1.add(prong1Mesh);
    
    const prong2Mesh = new THREE.Mesh(prongGeo, aluminumMaterial);
    prong2Mesh.position.set(-0.1, 0.1, 0);
    prong2Mesh.castShadow = true;
    robotModel.prong2.add(prong2Mesh);
    
    gripperAssembly.add(robotModel.prong1);
    gripperAssembly.add(robotModel.prong2);
}

function onWindowResize() {
    const container = document.getElementById('robot-container-3d');
    if (!container || !camera || !renderer) return;
    
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

function animate() {
    requestAnimationFrame(animate);
    if (controls) controls.update();
    if (renderer && scene && camera) renderer.render(scene, camera);
}

function updateRobotModel() {
    if (!robotModel.base_pivot) return;

    // Import THREE dynamically for math utils
    import('three').then(THREE => {
        // Base rotation (Y-axis yaw) - 0° = facing forward
        robotModel.base_pivot.rotation.y = THREE.MathUtils.degToRad(robotState.base);

        // Shoulder rotation (X-axis pitch) - CORRECTED MAPPING
        // Robot's ~0° = shoulder straight up, but movements are reversed
        robotModel.shoulder_pivot.rotation.x = THREE.MathUtils.degToRad(-robotState.shoulder);
        
        // Elbow rotation (X-axis pitch) - CORRECTED MAPPING  
        // Robot's 90° = elbow bent at 90°, 3D model starts straight
        // So we need to bend the elbow by the robot's elbow angle
        robotModel.elbow_pivot.rotation.x = THREE.MathUtils.degToRad(-robotState.elbow);

        // Hand rotation (Z-axis roll) - CORRECTED MAPPING
        // Robot's 180° = hand closed/down, 0° = hand open/up
        robotModel.hand_pivot.rotation.z = THREE.MathUtils.degToRad(robotState.hand - 180);

        // Gripper open/close
        if (robotModel.prong1 && robotModel.prong2) {
            const gripperAngle = THREE.MathUtils.degToRad(robotState.gripper * 0.5);
            robotModel.prong1.rotation.z = -gripperAngle;
            robotModel.prong2.rotation.z = gripperAngle;
        }
    });
}

function updateRobotStateFromFeedback(data) {
    const RAD2DEG = 180 / Math.PI;
    // Convert radian feedback to degrees
    const radToDeg = (val) => val !== undefined ? (val * RAD2DEG) : undefined;

    // Map robot feedback to 3D model coordinate system
    if (data.b !== undefined) robotState.base = radToDeg(data.b);
    if (data.s !== undefined) robotState.shoulder = radToDeg(data.s);
    if (data.e !== undefined) robotState.elbow = radToDeg(data.e);
    if (data.t !== undefined) robotState.hand = radToDeg(data.t);
    
    // Handle gripper if present (assuming it might be in a different field)
    if (data.T !== undefined && data.T < 500) { // T field might be gripper when < 500
        robotState.gripper = data.T / 10; // Scale as needed
    }

    // Update sliders & feedback boxes
    updateSliderValues();
    
    // Update 3D model
    updateRobotModel();
}

// --- SDR ---
function initializeSDR() {
    const waterfallCanvas = document.getElementById('waterfall');
    if (!waterfallCanvas) return;

    spectrum = new Spectrum('waterfall', {
        spectrumPercent: 50,
    });

    connectSDRWebSocket();

    document.getElementById('sdr-update-settings').addEventListener('click', updateSdrSettings);
    document.getElementById('sdr-pause').addEventListener('click', () => spectrum.togglePaused());
    document.getElementById('sdr-color').addEventListener('click', () => spectrum.toggleColor());
    document.getElementById('sdr-max-hold').addEventListener('click', () => spectrum.toggleMaxHold());
}

function connectSDRWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/sdr`;
    sdrSocket = new WebSocket(url);

    sdrSocket.onopen = () => {
        console.log('SDR WebSocket connected.');
        updateSdrStatus(); // Get initial settings
    };

    sdrSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (spectrum) {
            spectrum.addData(data);
        }
    };

    sdrSocket.onclose = () => {
        console.log('SDR WebSocket disconnected. Retrying in 3 seconds...');
        setTimeout(connectSDRWebSocket, 3000);
    };

    sdrSocket.onerror = (error) => {
        console.error('SDR WebSocket error:', error);
    };
}

async function updateSdrSettings() {
    const center_freq = parseFloat(document.getElementById('sdr-freq').value) * 1e6;
    const sample_rate = parseFloat(document.getElementById('sdr-rate').value) * 1e6;
    const rx_gain = parseInt(document.getElementById('sdr-gain').value, 10);
    const fft_size = parseInt(document.getElementById('sdr-fft-size').value, 10);
    const update_rate = parseInt(document.getElementById('sdr-update-rate').value, 10);
    const baseband_filter_bw = parseInt(document.getElementById('sdr-baseband-bw').value, 10);

    const settings = {
        center_freq,
        sample_rate,
        rx_gain,
        fft_size,
        update_rate,
        baseband_filter_bw,
    };

    try {
        const response = await fetch('/sdr/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        const data = await response.json();
        console.log('SDR settings updated:', data);
        // Also update the spectrum display settings
        spectrum.setCenterHz(center_freq);
        spectrum.setSpanHz(sample_rate);
    } catch (error) {
        console.error("Error updating SDR settings:", error);
    }
}

async function updateSdrStatus() {
     try {
        const response = await fetch('/sdr/status');
        const data = await response.json();
        if (data.is_streaming) {
            document.getElementById('sdr-freq').value = data.center_freq / 1e6;
            document.getElementById('sdr-rate').value = data.sample_rate / 1e6;
            document.getElementById('sdr-gain').value = data.rx_gain;
            document.getElementById('sdr-fft-size').value = data.fft_size;
            document.getElementById('sdr-baseband-bw').value = data.baseband_filter_bw || 0;
            if (spectrum) {
                spectrum.setCenterHz(data.center_freq);
                spectrum.setSpanHz(data.sample_rate);
            }
        }
    } catch (error) {
        console.error("Error getting SDR status:", error);
    }
}

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
        
        // Update robot state from actual robot feedback
        updateRobotStateFromFeedback(data);
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
    const btnSync3D = document.getElementById('btn-sync-3d');
    const btnTorqueOn = document.getElementById('btn-torque-on');
    const btnTorqueOff = document.getElementById('btn-torque-off');
    const btnLedOn = document.getElementById('btn-led-on');
    const btnLedOff = document.getElementById('btn-led-off');

    if(btnInit) btnInit.addEventListener('click', () => {
        sendCommand({"T":102,"base":0,"shoulder":0,"elbow":1.5707965,"hand":3.1415926,"spd":0,"acc":0});
        // Reset robot state for visualization to match actual robot init position
        robotState.base = 0;     // ~0° = facing forward
        robotState.shoulder = 2; // ~2° = shoulder pointing straight up
        robotState.elbow = 90;   // 90° = elbow at 90 degrees
        robotState.hand = 180;   // 180° = hand closed/facing down
        robotState.gripper = 15;
        updateSliderValues();
        updateRobotModel();
    });
    
    if(btnSync3D) btnSync3D.addEventListener('click', async () => {
        // Immediately fetch current robot position and update 3D model
        try {
            const cmd = { "T": 105 }; // CMD_SERVO_RAD_FEEDBACK
            const response = await fetch('/robot/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: JSON.stringify(cmd) })
            });
            if (response.ok) {
                const result = await response.json();
                const data = JSON.parse(result.response);
                updateRobotStateFromFeedback(data);
                if (feedbackBox()) {
                    feedbackBox().textContent = `3D Model synced with robot position: b=${data.b?.toFixed(3)}, s=${data.s?.toFixed(3)}, e=${data.e?.toFixed(3)}, t=${data.t?.toFixed(3)}`;
                }
            }
        } catch (error) {
            console.error("Failed to sync 3D model:", error);
            if (feedbackBox()) {
                feedbackBox().textContent = `Sync failed: ${error.message}`;
            }
        }
    });
    
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


// --- Slider Event Listeners ---
function initializeSliders() {
    const sliders = {
        'angle-b-slider': 'base',
        'angle-s-slider': 'shoulder', 
        'angle-e-slider': 'elbow',
        'angle-h-slider': 'hand',
        'angle-g-slider': 'gripper'
    };

    Object.entries(sliders).forEach(([sliderId, joint]) => {
        const slider = document.getElementById(sliderId);
        if (slider) {
            slider.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                robotState[joint] = value;
                
                // Update feedback display
                const feedbackElement = document.getElementById(joint === 'base' ? 'angle-b' :
                    joint === 'shoulder' ? 'angle-s' :
                    joint === 'elbow' ? 'angle-e' :
                    joint === 'hand' ? 'angle-h' : 'angle-g');
                
                if (feedbackElement) {
                    feedbackElement.textContent = joint === 'gripper' ? value.toFixed(1) : `${value.toFixed(1)}°`;
                }
                
                // Update 3D model
                updateRobotModel();
            });
        }
    });
}

function updateSliderValues() {
    // Update slider values to match robot state
    const sliders = {
        'angle-b-slider': 'base',
        'angle-s-slider': 'shoulder', 
        'angle-e-slider': 'elbow',
        'angle-h-slider': 'hand',
        'angle-g-slider': 'gripper'
    };

    Object.entries(sliders).forEach(([sliderId, joint]) => {
        const slider = document.getElementById(sliderId);
        const feedbackElement = document.getElementById(joint === 'base' ? 'angle-b' :
            joint === 'shoulder' ? 'angle-s' :
            joint === 'elbow' ? 'angle-e' :
            joint === 'hand' ? 'angle-h' : 'angle-g');
        
        if (slider && robotState[joint] !== undefined) {
            slider.value = robotState[joint];
        }
        
        if (feedbackElement && robotState[joint] !== undefined) {
            feedbackElement.textContent = joint === 'gripper' ? 
                robotState[joint].toFixed(1) : `${robotState[joint].toFixed(1)}°`;
        }
    });
}

// --- Chatbot Logic ---
function appendChatbotMessage(text, sender, logprobs) {
    const messagesDiv = document.getElementById('chatbot-messages');
    if (!messagesDiv) return;
    const msg = document.createElement('div');
    msg.className = 'chatbot-message ' + sender;
    msg.textContent = text;
    messagesDiv.appendChild(msg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    // If logprobs are present and sender is bot, update the logprobs window
    if (sender === 'bot' && Array.isArray(logprobs)) {
        const logprobsWindow = document.getElementById('chatbot-logprobs-window');
        if (logprobsWindow) {
            logprobsWindow.textContent = 'logprobs: [' + logprobs.map(x => x.toFixed(3)).join(', ') + ']';
        }
    }
}

async function sendChatbotMessage() {
    const input = document.getElementById('chatbot-input');
    if (!input || !input.value.trim()) return;
    const userMsg = input.value.trim();
    appendChatbotMessage(userMsg, 'user');
    input.value = '';
    try {
        // Step 1: Enqueue the message
        const res = await fetch('/chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMsg })
        });
        const data = await res.json();
        if (!data.job_id) {
            appendChatbotMessage('Error: Could not enqueue message.', 'bot');
            return;
        }
        // Step 2: Poll for result
        pollChatbotResult(data.job_id);
    } catch (err) {
        appendChatbotMessage('Error contacting chatbot.', 'bot');
    }
}

async function pollChatbotResult(job_id, tries = 0) {
    if (tries > 60) { // ~60*1s = 1 minute timeout
        appendChatbotMessage('No response from chatbot (timeout).', 'bot');
        return;
    }
    try {
        const res = await fetch(`/chatbot/result/${job_id}`);
        const data = await res.json();
        if (data.reply) {
            appendChatbotMessage(data.reply, 'bot', data.logprobs);
        } else if (data.status === 'pending') {
            setTimeout(() => pollChatbotResult(job_id, tries + 1), 1000);
        } else {
            appendChatbotMessage('Error: ' + (data.error || 'Unknown error.'), 'bot');
        }
    } catch (err) {
        appendChatbotMessage('Error polling chatbot result.', 'bot');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('chatbot-input');
    const sendBtn = document.getElementById('chatbot-send');
    if (input && sendBtn) {
        sendBtn.addEventListener('click', sendChatbotMessage);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendChatbotMessage();
        });
    }
});

// --- Page Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize 3D model first
    await initThree();
    
    // Initialize event listeners
    initializeEventListeners();
    initializeSliders();

    // Attach camera feed error handler
    const cameraFeed = document.querySelector('.camera-feed');
    const cameraStatusEl = document.getElementById('camera-status');
    if (cameraFeed) {
        const setOffline = () => {
            if (cameraStatusEl) cameraStatusEl.innerHTML = '<span class="blink" style="color:#ff0000">●</span> OFFLINE';
        };

        cameraFeed.addEventListener('error', () => {
            setOffline();
            console.log('Camera feed error - manual refresh required');
        });
        // When it loads successfully, set status to LIVE
        cameraFeed.addEventListener('load', () => {
            if (cameraStatusEl) cameraStatusEl.innerHTML = '<span class="blink">●</span> LIVE';
        });
    }
    
    // Initialize SDR
    initializeSDR();
    
    // Update initial values
    updateSliderValues();
    updateRobotModel();
    
    // Start status updates
    updateStatus();
    setInterval(updateStatus, 2000); // Poll for status every 2 seconds
}); 