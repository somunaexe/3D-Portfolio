import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const canvas = document.getElementById('canvas');

// Create the scene
const scene = new THREE.Scene();
scene.background = new THREE.Color('#F0F0F0');

// Create the camera
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 5;

// Create a dodecahedron
const dodGeometry = new THREE.DodecahedronGeometry();
const dodMaterial = new THREE.MeshBasicMaterial({ color: '#468585', emissive: '#468585' });
const dohed = new THREE.Mesh(dodGeometry, dodMaterial);

// Create a box
const boxGeometry = new THREE.BoxGeometry(2, 0.1, 2);
const boxMaterial = new THREE.MeshBasicMaterial({color: '#808080', emissive: '#808080' })
const box = new THREE.Mesh(boxGeometry, boxMaterial);
box.position.y = -1.5;

scene.add(dohed);
scene.add(box);

// Light
const light = new THREE.SpotLight(0x006769, 100);
light.position.set(1, 1, 1);
scene.add(light);

// Renderer
const renderer = new THREE.WebGLRenderer({ canvas });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);

renderer.render(scene, camera);

//Add OrbitControls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.enableZoom = true;
controls.enablePan = true;

// Add Animations
function animate() {
    requestAnimationFrame(animate);

    dohed.rotation.x += 0.01;
    dohed.rotation.y += 0.01;

    box.rotation.y += 0.005;

    controls.update();

    renderer.render(scene, camera);
}

animate();