import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export function initScene(canvas) {
    const loading = document.querySelector('#loader');
    const scene = new THREE.Scene();
    const textureLoader = new THREE.TextureLoader();

    const sizes = {
        width: window.innerWidth / 2, // Half width since canvas is on right side
        height: window.innerHeight
    };

    // Base camera - Widened FOV to 22 to allow for larger model size
    const camera = new THREE.PerspectiveCamera(22, sizes.width / sizes.height, 0.1, 100);
    camera.position.set(0, 4, 15);
    scene.add(camera);

    // Controls
    const controls = new OrbitControls(camera, canvas);
    controls.enableDamping = true;
    controls.enableZoom = true;
    controls.enablePan = true;
    controls.minDistance = 21;
    controls.maxDistance = 50;
    controls.minPolarAngle = Math.PI / 5;
    controls.maxPolarAngle = Math.PI / 2;

    // Renderer
    const renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        antialias: true,
        alpha: true
    });
    renderer.setSize(sizes.width, sizes.height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;

    // Materials
    const bakedTexture = textureLoader.load('/models/baked.jpg');
    bakedTexture.flipY = false;
    bakedTexture.encoding = THREE.sRGBEncoding;
    const bakedMaterial = new THREE.MeshBasicMaterial({ map: bakedTexture });

    // Model reference for rotation
    let model = null;

    // Loader
    const loader = new GLTFLoader();
    loader.load(
        '/models/model.glb',
        (gltf) => {
            model = gltf.scene;
            model.traverse(child => child.material = bakedMaterial);
            model.position.set(0.4, 0.2, 0); // Shifted slightly right to align better
            model.scale.set(1.8, 1.8, 1.8); // Increased size further 
            // Initial rotation: face left with front visible
            model.rotation.y = -Math.PI / 2; // -90 degrees, facing left
            scene.add(model);

            // Set controls to target the handle the new position
            controls.target.set(0.4, 0.2, 0);

            if (loading) {
                loading.style.display = 'none';
            }
        },
        (xhr) => {
            console.log((xhr.loaded / xhr.total * 100) + '% loaded');
        }
    );

    // Resize handler
    const handleResize = () => {
        sizes.width = window.innerWidth / 2;
        sizes.height = window.innerHeight;
        camera.aspect = sizes.width / sizes.height;
        camera.updateProjectionMatrix();
        renderer.setSize(sizes.width, sizes.height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    };
    window.addEventListener('resize', handleResize);

    // Animation
    // Animation loop management
    let animationId = null;
    let isRunning = true;

    const minPan = new THREE.Vector3(-2, -0.5, -2);
    const maxPan = new THREE.Vector3(2, 0.5, 2);

    const tick = () => {
        if (!isRunning) return;

        controls.update();
        controls.target.clamp(minPan, maxPan);
        renderer.render(scene, camera);
        animationId = window.requestAnimationFrame(tick);
    };

    tick();

    // Return necessary objects and controls
    return {
        scene,
        camera,
        renderer,
        controls,
        model: () => model,
        stop: () => {
            isRunning = false;
            if (animationId) window.cancelAnimationFrame(animationId);
        },
        start: () => {
            if (!isRunning) {
                isRunning = true;
                tick();
            }
        },
        dispose: () => {
            isRunning = false;
            if (animationId) window.cancelAnimationFrame(animationId);
            window.removeEventListener('resize', handleResize);
            renderer.dispose();
            scene.traverse(object => {
                if (object.geometry) object.geometry.dispose();
                if (object.material) {
                    if (Array.isArray(object.material)) {
                        object.material.forEach(material => material.dispose());
                    } else {
                        object.material.dispose();
                    }
                }
            });
        }
    };
}
