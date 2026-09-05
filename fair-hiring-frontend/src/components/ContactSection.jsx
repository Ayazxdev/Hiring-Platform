import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import GridPlus from './GridPlus';

gsap.registerPlugin(ScrollTrigger);

export default function ContactSection() {
    const navigate = useNavigate();
    const canvasRef = useRef(null);
    const containerRef = useRef(null);

    useEffect(() => {
        // Toggle navbar theme when scrolling through this section
        const navSt = ScrollTrigger.create({
            trigger: containerRef.current,
            start: 'top 60px',
            end: 'bottom 60px',
            toggleClass: { targets: 'nav', className: 'navbar-dark' },
        });

        if (!canvasRef.current) return;

        let scene, camera, renderer, shape, myArray;
        let mouseX = 0, mouseY = 0;
        let animationId;
        let isInitialized = false;

        const init = () => {
            if (isInitialized || !canvasRef.current) return;

            scene = new THREE.Scene();

            // Camera
            const aspect = window.innerWidth / window.innerHeight;
            const d = 500;
            camera = new THREE.OrthographicCamera(-d * aspect, d * aspect, d, -d, 1, 1000);
            camera.position.set(500, 500, 500);
            camera.lookAt(scene.position);

            // Renderer
            renderer = new THREE.WebGLRenderer({
                canvas: canvasRef.current,
                antialias: true,
                alpha: true
            });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;

            // Lights
            const shadowLight = new THREE.DirectionalLight(0xffffff, 1.8);
            shadowLight.position.set(0, 50, 0);
            shadowLight.castShadow = true;
            scene.add(shadowLight);

            const light = new THREE.DirectionalLight(0xffffff, 1.8);
            light.position.set(60, 100, 20);
            scene.add(light);

            const backLight = new THREE.DirectionalLight(0xffffff, 1);
            backLight.position.set(-40, 100, 20);
            scene.add(backLight);

            // Floor
            const floorGeo = new THREE.PlaneGeometry(500, 500, 1, 1);
            const floorMat = new THREE.MeshBasicMaterial({
                color: 0xE6E6E2,
                transparent: true,
                opacity: 0
            });
            const floor = new THREE.Mesh(floorGeo, floorMat);
            floor.rotation.x = -Math.PI / 2;
            floor.position.y = -150;
            floor.receiveShadow = true;
            scene.add(floor);

            // Shape
            myArray = new THREE.Group();
            scene.add(myArray);

            const geometry = new THREE.BoxGeometry(50, 50, 50);
            const material = new THREE.MeshLambertMaterial({
                color: 0xF9F8ED,
            });
            shape = new THREE.Mesh(geometry, material);
            shape.castShadow = true;
            shape.receiveShadow = false;
            myArray.add(shape);

            isInitialized = true;
            render();
        };

        const render = () => {
            if (!isInitialized) return;
            const time = Date.now() * 0.001;

            const scaleBase = 1.0;
            const breathing = Math.sin(time * 0.8) * 0.15;
            shape.scale.set(scaleBase + breathing, scaleBase + breathing, scaleBase + breathing);

            shape.rotation.y += 0.003;
            shape.rotation.z += 0.001;

            const targetRotationY = (mouseX / window.innerWidth) * Math.PI * 0.5;
            const targetRotationX = (mouseY / window.innerHeight) * Math.PI * 0.5;

            myArray.rotation.y += (targetRotationY - myArray.rotation.y) * 0.08;
            myArray.rotation.x += (targetRotationX - myArray.rotation.x) * 0.08;

            renderer.render(scene, camera);
            animationId = requestAnimationFrame(render);
        };

        const handleMouseMove = (event) => {
            mouseX = (event.clientX - window.innerWidth / 2);
            mouseY = (event.clientY - window.innerHeight / 2);
        };

        const handleResize = () => {
            if (!isInitialized || !camera || !renderer) return;
            const aspect = window.innerWidth / window.innerHeight;
            const d = 500;
            camera.left = -d * aspect;
            camera.right = d * aspect;
            camera.top = d;
            camera.bottom = -d;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        };

        const observer = new IntersectionObserver(
            (entries) => {
                const entry = entries[0];
                if (entry.isIntersecting) {
                    if (!isInitialized) {
                        init();
                    }
                    if (animationId) cancelAnimationFrame(animationId);
                    animationId = requestAnimationFrame(render);
                } else {
                    if (animationId) cancelAnimationFrame(animationId);
                }
            },
            { rootMargin: '200px' }
        );

        if (containerRef.current) {
            observer.observe(containerRef.current);
        }

        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('resize', handleResize);

        return () => {
            navSt.kill();
            observer.disconnect();
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationId);

            // Dispose Three.js resources
            if (renderer) {
                renderer.dispose();
            }
            if (scene) {
                scene.traverse((object) => {
                    if (object.geometry) object.geometry.dispose();
                    if (object.material) {
                        if (Array.isArray(object.material)) {
                            object.material.forEach(m => m.dispose());
                        } else {
                            object.material.dispose();
                        }
                    }
                });
            }
            isInitialized = false;
        };
    }, []);

    return (
        <section
            id="contact"
            ref={containerRef}
            className="section-contact relative min-h-screen bg-[#E6E6E2] text-[#1c1c1c] overflow-hidden flex flex-col justify-between pt-0 pb-8 px-8 md:px-16"
        >
            {/* Soft vertical fade behind object */}
            <div className="absolute inset-0 z-0 bg-gradient-to-b from-transparent via-[#dfdfda] to-transparent opacity-40"></div>

            {/* Grid Lines */}
            <div className="absolute inset-0 pointer-events-none opacity-10">
                <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-black"></div>
                <div className="absolute top-1/2 left-0 right-0 h-[1px] bg-black"></div>

                {/* Plus markers at intersections */}
                <GridPlus className="left-1/2 top-1/2" />
                <GridPlus className="left-8 top-1/2 md:left-16" />
                <GridPlus className="right-8 top-1/2 md:right-16 translate-x-1/2" />
                <GridPlus className="left-1/2 top-24" />
                <GridPlus className="left-1/2 bottom-24 translate-y-1/2" />
            </div>

            {/* Three.js Canvas */}
            <div className="absolute inset-0 z-10 pointer-events-none flex items-center justify-center">
                <canvas ref={canvasRef} className="w-full h-full" />
            </div>

            <div className="relative z-20 flex-grow grid grid-cols-1 md:grid-cols-2 gap-12 items-center">

                {/* Left Column: Metadata */}
                <div className="flex flex-col gap-12 self-start md:self-center">
                    <div className="metadata-block">
                        <h4 className="text-[10px] tracking-[0.3em] font-grotesk font-bold text-black uppercase mb-4 opacity-100">FIND US</h4>
                        <p className="text-sm font-montreal font-medium">HONG KONG</p>
                    </div>

                    <div className="metadata-block">
                        <h4 className="text-[10px] tracking-[0.3em] font-grotesk font-bold text-black uppercase mb-4 opacity-100">INTERNAL</h4>
                        <ul className="flex flex-col gap-2 text-sm font-montreal">
                            <li>
                                <button
                                    onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                                    className="hover:opacity-50 transition-opacity text-left cursor-pointer"
                                >
                                    Home
                                </button>
                            </li>
                            <li>
                                <button
                                    onClick={() => navigate('/system-flow')}
                                    className="hover:opacity-50 transition-opacity text-left cursor-pointer"
                                >
                                    System Flow
                                </button>
                            </li>
                            <li><a href="#" className="hover:opacity-50 transition-opacity">Fairness Protocols</a></li>
                            <li><a href="#" className="hover:opacity-50 transition-opacity">Privacy</a></li>
                        </ul>
                    </div>

                    <div className="metadata-block">
                        <h4 className="text-[10px] tracking-[0.3em] font-grotesk font-bold text-black uppercase mb-4 opacity-100">EXTERNAL</h4>
                        <ul className="flex flex-col gap-2 text-sm font-montreal">
                            <li>
                                <a
                                    href="https://linkedin.com/in/ayazahmd"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="hover:opacity-50 transition-opacity inline-flex items-center gap-1"
                                >
                                    <span>LinkedIn</span>
                                    <span className="text-[10px]">↗</span>
                                </a>
                            </li>
                            <li>
                                <a
                                    href="https://github.com/ayazxdev"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="hover:opacity-50 transition-opacity inline-flex items-center gap-1"
                                >
                                    <span>GitHub</span>
                                    <span className="text-[10px]">↗</span>
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>

                {/* Right Column: Primary CTA */}
                <div className="flex flex-col gap-4 text-right md:text-left">
                    <a
                        href="mailto:hello@fairhiring.network"
                        className="email-cta group inline-block"
                    >
                        <h2 className="text-[clamp(2rem,4vw,5rem)] font-montreal font-bold leading-none tracking-tighter break-all">
                            HELLO@<br />
                            FAIRHIRING.NETWORK
                        </h2>
                        <div className="h-1 w-0 bg-[#D4D478] group-hover:w-full transition-all duration-700 ease-out mt-4"></div>
                    </a>

                    <p className="text-xs md:text-sm font-grotesk font-bold text-black tracking-[0.2em] uppercase opacity-100 mt-8">
                        LET’S BUILD FAIR HIRING SYSTEMS
                    </p>
                </div>
            </div>

            {/* Footer */}
            <div className="relative z-20 w-full flex justify-between items-end border-t border-black/10 pt-4 mt-12 pb-2">
                <div className="text-[10px] md:text-xs font-grotesk font-bold text-black tracking-widest opacity-100 uppercase">
                    Fair Hiring Network
                </div>
                <div className="text-[10px] md:text-xs font-grotesk font-bold text-black tracking-widest opacity-100 uppercase">
                    All rights reserved © 2026
                </div>
            </div>
        </section>
    );
}
