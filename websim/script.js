import * as THREE from 'three';
import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.166.1/examples/jsm/controls/OrbitControls.js";

document.addEventListener('DOMContentLoaded', () => {

    // --- THREE.js Scene Setup ---
    let scene, camera, renderer, controls;
    let robotModel = {}; // To hold the 3D model parts

    function initThree() {
        const container = document.getElementById('robot-container-3d');
        if (!container) return;

        // Scene
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf0f0f0); // Brighter background for visibility
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
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.9); // Increased ambient light
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 1.2); // Main light, brighter
        dirLight.position.set(8, 10, 5);
        dirLight.castShadow = true;
        dirLight.shadow.camera.top = 4;
        dirLight.shadow.camera.bottom = -4;
        dirLight.shadow.camera.left = -4;
        dirLight.shadow.camera.right = 4;
        dirLight.shadow.camera.near = 0.1;
        dirLight.shadow.camera.far = 40;
        scene.add(dirLight);
        
        // Add a fill light for softer shadows
        const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
        fillLight.position.set(-8, 5, -5);
        scene.add(fillLight);

        // Ground Plane
        const ground = new THREE.Mesh(
            new THREE.PlaneGeometry(30, 30),
            new THREE.MeshStandardMaterial({ color: 0x999999, roughness: 0.8 }) // Lighter ground
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
        createRobotModel();

        // Resize listener
        window.addEventListener('resize', onWindowResize);
        
        // Start animation loop
        animate();
    }

    function createRobotModel() {
        const textureLoader = new THREE.TextureLoader();
        const carbonFiberTexture = textureLoader.load('/image.png');
        carbonFiberTexture.wrapS = THREE.RepeatWrapping;
        carbonFiberTexture.wrapT = THREE.RepeatWrapping;
        carbonFiberTexture.repeat.set(1, 5);
        
        // --- Materials ---
        const aluminumMaterial = new THREE.MeshStandardMaterial({ color: 0x4B4B4B, roughness: 0.3, metalness: 0.8 });
        const servoMaterial = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.7 });
        const carbonFiberMaterial = new THREE.MeshStandardMaterial({ map: carbonFiberTexture, roughness: 0.4, metalness: 0.2 });
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

        // Lower Arm (More substantial U-Channel like structure)
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
        
        // Forearm (Carbon Fiber)
        const forearmLength = 2.2;
        const forearm = new THREE.Mesh(
            new THREE.CylinderGeometry(0.18, 0.15, forearmLength, 32),
            carbonFiberMaterial
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
        gripperAssembly.position.y = 0.2; // Position relative to the center of the wrist servo
        wristServoMount.add(gripperAssembly);

        const gripperBase = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.1, 0.3), aluminumMaterial);
        gripperBase.castShadow = true;
        gripperAssembly.add(gripperBase);

        const prongGeometry = new THREE.BoxGeometry(0.08, 0.5, 0.15);
        prongGeometry.translate(0, 0.25, 0); // Set pivot point to the base of the prong

        const prong1 = new THREE.Mesh(prongGeometry, aluminumMaterial);
        prong1.position.x = 0.15;
        prong1.castShadow = true;
        gripperBase.add(prong1);

        const prong2 = new THREE.Mesh(prongGeometry, aluminumMaterial);
        prong2.position.x = -0.15;
        prong2.castShadow = true;
        gripperBase.add(prong2);

        // Store references for animation
        robotModel.prong1 = prong1;
        robotModel.prong2 = prong2;

        // Visual representation for the light
        const lightBulbGeo = new THREE.SphereGeometry(0.05, 16, 8);
        const lightBulbMat = new THREE.MeshBasicMaterial({ color: 0xffffee });
        const lightBulb = new THREE.Mesh(lightBulbGeo, lightBulbMat);
        lightBulb.position.set(0, 0.05, 0.2); // Place on top of the gripper base, pointing forward
        gripperBase.add(lightBulb);
        
        // The actual light source
        const workLight = new THREE.SpotLight(0xffffff, 20.0, 10, Math.PI * 0.2, 0.5, 1.5);
        workLight.castShadow = true;
        workLight.shadow.mapSize.width = 512;
        workLight.shadow.mapSize.height = 512;
        workLight.shadow.camera.near = 0.1;
        workLight.shadow.camera.far = 10;
        lightBulb.add(workLight);

        // Target for the spotlight to point down and forward
        const lightTarget = new THREE.Object3D();
        lightTarget.position.set(0, -1, 0.5); // relative to the light bulb
        lightBulb.add(lightTarget);
        workLight.target = lightTarget;
    }
    
    function onWindowResize() {
        const container = document.getElementById('robot-container-3d');
        if (!container) return;
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    }

    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
    }

    const robotState = {
        base: 0,
        shoulder: 45,
        elbow: 90,
        hand: 0,
        gripper: 15,
    };

    const dom = {
        diagram: {}, // SVG diagram is removed
        sliders: {
            base: document.getElementById('angle-b-slider'),
            shoulder: document.getElementById('angle-s-slider'),
            elbow: document.getElementById('angle-e-slider'),
            hand: document.getElementById('angle-h-slider'),
            gripper: document.getElementById('angle-g-slider'),
        },
        feedback: {
            base: document.getElementById('angle-b'),
            shoulder: document.getElementById('angle-s'),
            elbow: document.getElementById('angle-e'),
            hand: document.getElementById('angle-h'),
            gripper: document.getElementById('angle-g'),
            coords: {
                x: document.getElementById('coord-x'),
                y: document.getElementById('coord-y'),
                z: document.getElementById('coord-z'),
            }
        },
        buttons: {
            init: document.getElementById('btn-init'),
        },
        feedbackBox: document.getElementById('feedback-box'),
        jsonCommand: document.getElementById('json-command'),
        sendJson: document.getElementById('send-json'),
        commandList: document.getElementById('command-list'),
        commandSearch: document.getElementById('command-search'),
    };

    const commands = [
        { name: "Get Device ID", cmd: '{"T":1}' },
        { name: "Get Device Serial Number", cmd: '{"T":2}' },
        { name: "Reset Robot", cmd: '{"T":4}' },
        { name: "Torque ON", cmd: '{"T":100}' },
        { name: "Torque OFF", cmd: '{"T":101}' },
        { name: "Brake ON", cmd: '{"T":102}' },
        { name: "Brake OFF", cmd: '{"T":103}' },
        { name: "Initialize Position", cmd: '{"T":104}' },
        { name: "LED ON", cmd: '{"T":105,"V":1}' },
        { name: "LED OFF", cmd: '{"T":105,"V":0}' },
        { name: "Set Base Angle to 30°", cmd: '{"T":200,"A1":3000}' },
        { name: "Set Shoulder Angle to 45°", cmd: '{"T":200,"A2":4500}' },
        { name: "Go to (0, 100, 100)", cmd: '{"T":202,"X":0,"Y":10000,"Z":10000}' }
    ];

    function logFeedback(message, isCommand = false) {
        const timestamp = new Date().toLocaleTimeString();
        const prefix = isCommand ? ">>" : "<<";
        dom.feedbackBox.textContent = `[${timestamp}] ${prefix} ${message}\n` + dom.feedbackBox.textContent;
        // Keep it from getting too long
        const lines = dom.feedbackBox.textContent.split('\n');
        if (lines.length > 50) {
            dom.feedbackBox.textContent = lines.slice(0, 50).join('\n');
        }
    }

    function updateRobotModel() {
        if (!robotModel.base_pivot) return;

        // Base rotation (Y-axis yaw)
        robotModel.base_pivot.rotation.y = THREE.MathUtils.degToRad(robotState.base);

        // Shoulder rotation (X-axis pitch)
        // UI: 0=forward, 45=up-forward, 90=straight up
        robotModel.shoulder_pivot.rotation.x = THREE.MathUtils.degToRad(robotState.shoulder - 90);
        
        // Elbow rotation (X-axis pitch)
        // UI: 90=straight, 0=bent 90deg
        robotModel.elbow_pivot.rotation.x = THREE.MathUtils.degToRad(robotState.elbow - 90);

        // Hand rotation (Y-axis roll)
        robotModel.hand_pivot.rotation.y = THREE.MathUtils.degToRad(robotState.hand);

        // Gripper open/close
        if (robotModel.prong1 && robotModel.prong2) {
            const gripperAngle = THREE.MathUtils.degToRad(robotState.gripper);
            robotModel.prong1.rotation.z = -gripperAngle;
            robotModel.prong2.rotation.z = gripperAngle;
        }
    }

    function updateUI() {
        for (const joint in robotState) {
            if (dom.sliders[joint]) {
                dom.sliders[joint].value = robotState[joint];
                const value = parseFloat(robotState[joint]).toFixed(1);
                dom.feedback[joint].textContent = joint === 'gripper' ? value : `${value}°`;
            }
        }
        updateRobotModel();
        // In a real scenario, you'd calculate FK here to update XYZ
    }

    function setJointAngle(joint, angle, fromSlider = false) {
        const min = parseFloat(dom.sliders[joint].min);
        const max = parseFloat(dom.sliders[joint].max);
        angle = Math.max(min, Math.min(max, angle));
        
        robotState[joint] = angle;
        
        if (!fromSlider) {
            dom.sliders[joint].value = angle;
        }
        
        let command;
        if (joint === 'gripper') {
            // Assuming a different command for gripper, e.g., setting tool value
            command = `{"T":110, "V":${Math.round(angle)}}`;
        } else {
            const jointIdMap = { base: 1, shoulder: 2, elbow: 3, hand: 4 };
            command = `{"T":200, "A${jointIdMap[joint]}":${Math.round(angle*100)}}`;
        }
        logFeedback(command, true);
        
        updateUI();
    }
    
    function init() {
        // Init 3D Scene
        initThree();

        // Sliders
        Object.values(dom.sliders).forEach(slider => {
            slider.addEventListener('input', (e) => {
                const joint = e.target.dataset.joint;
                setJointAngle(joint, parseFloat(e.target.value), true);
            });
        });

        // System Buttons
        dom.buttons.init.addEventListener('click', () => {
            logFeedback('{"T":104}', true);
            robotState.base = 0;
            robotState.shoulder = 45;
            robotState.elbow = 90;
            robotState.hand = 0;
            robotState.gripper = 15;
            updateUI();
            logFeedback("Robot initialized to default position.", false);
        });

        document.getElementById('btn-torque-on').addEventListener('click', () => logFeedback('{"T":100}', true));
        document.getElementById('btn-torque-off').addEventListener('click', () => logFeedback('{"T":101}', true));
        document.getElementById('btn-led-on').addEventListener('click', () => logFeedback('{"T":105,"V":1}', true));
        document.getElementById('btn-led-off').addEventListener('click', () => logFeedback('{"T":105,"V":0}', true));

        // Manual Command
        dom.sendJson.addEventListener('click', () => {
            const cmd = dom.jsonCommand.value.trim();
            if (cmd) {
                logFeedback(cmd, true);
            }
        });
        
        // Command Library
        renderCommandList(commands);
        dom.commandSearch.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const filteredCommands = commands.filter(c => 
                c.name.toLowerCase().includes(searchTerm) || 
                c.cmd.toLowerCase().includes(searchTerm)
            );
            renderCommandList(filteredCommands);
        });
        
        // Initial state
        logFeedback("SYSTEM ONLINE. AWAITING INPUT...", false);
        updateUI();
    }

    function renderCommandList(commandList) {
        dom.commandList.innerHTML = '';
        commandList.forEach(c => {
            const item = document.createElement('div');
            item.className = 'command-item';
            item.innerHTML = `<strong>${c.name}</strong><code>${c.cmd}</code>`;
            item.addEventListener('click', () => {
                dom.jsonCommand.value = c.cmd;
                logFeedback(`Loaded command: ${c.name}`, false);
            });
            dom.commandList.appendChild(item);
        });
    }

    init();
});