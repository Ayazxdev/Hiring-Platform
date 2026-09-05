import { useEffect, useRef } from 'react';
import { initScene } from '../three/scene';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

export default function ParallaxObject({ lenisInstance, isActive = true }) {
    const canvasRef = useRef(null);
    const sceneRef = useRef(null);
    const containerRef = useRef(null);
    const scrollCleanupRef = useRef(null);

    useEffect(() => {
        if (!canvasRef.current) return;

        // Initialize Three.js scene
        const sceneObjects = initScene(canvasRef.current);
        sceneRef.current = sceneObjects;

        // Wait for model to load before setting up scroll animations
        const checkModelLoaded = setInterval(() => {
            const model = sceneObjects.model();
            if (model) {
                clearInterval(checkModelLoaded);
                scrollCleanupRef.current = setupScrollAnimation(model, sceneObjects);
            }
        }, 100);

        return () => {
            clearInterval(checkModelLoaded);
            if (scrollCleanupRef.current) {
                scrollCleanupRef.current();
            }
            if (sceneRef.current) {
                sceneRef.current.dispose();
            }
        };
    }, []);

    // Toggle rendering/visibility based on activity
    useEffect(() => {
        if (containerRef.current) {
            containerRef.current.style.display = isActive ? 'block' : 'none';
            containerRef.current.style.visibility = isActive ? 'visible' : 'hidden';

            // Pause the 3D render loop when hidden to save massive GPU resources
            if (sceneRef.current) {
                if (isActive) {
                    sceneRef.current.start();
                } else {
                    sceneRef.current.stop();
                }
            }
        }
    }, [isActive]);

    const setupScrollAnimation = (model, sceneObjects) => {
        const { controls } = sceneObjects;

        // Disable user controls during scroll phase
        controls.enabled = false;

        const ctx = gsap.context(() => {
            // Create a continuous scroll-based animation
            const masterTimeline = gsap.timeline({
                scrollTrigger: {
                    trigger: '.hero-section',
                    start: 'top top',
                    end: 'bottom+=200vh top',
                    scrub: 1.5,
                    onLeave: () => {
                        if (sceneRef.current) sceneRef.current.stop();
                    },
                    onEnterBack: () => {
                        if (sceneRef.current && isActive) sceneRef.current.start();
                    },
                    onEnter: () => {
                        if (sceneRef.current && isActive) sceneRef.current.start();
                    },
                },
            });

            // Set initial state
            gsap.set(containerRef.current, {
                y: '30vh',
                opacity: 1,
                willChange: 'transform, opacity'
            });

            // Set initial rotation offset
            gsap.set(model.rotation, {
                y: -Math.PI / 2.5, // Rotated anti-clockwise relative to before
                x: -0.1 // Reversed tilt as well for consistency
            });

            // Single continuous animation
            masterTimeline
                .to(containerRef.current, {
                    y: '0vh',
                    ease: 'none',
                    duration: 2.5,
                }, 0)
                .to(model.rotation, {
                    y: 0,
                    ease: 'none',
                    duration: 3,
                }, 0)
                // Hold phase from 3 to 8 (implicit)
                .to(containerRef.current, {
                    opacity: 0,
                    y: '-20vh',
                    ease: 'power2.in',
                    duration: 2,
                }, 8);
        }, containerRef);

        return () => ctx.revert();
    };

    return (
        <div
            ref={containerRef}
            className="parallax-canvas fixed top-0 right-0 w-1/2 h-screen pointer-events-none z-30 transition-opacity duration-500"
            style={{ willChange: 'transform, opacity' }}
        >
            <canvas ref={canvasRef} className="webgl w-full h-full"></canvas>
        </div>
    );
}
