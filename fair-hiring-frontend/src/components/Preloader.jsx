import { useEffect, useState, useRef } from 'react';
import gsap from 'gsap';

export default function Preloader({ onComplete }) {
    const [counter, setCounter] = useState(0);
    const containerRef = useRef(null);
    const counterRef = useRef(null);

    useEffect(() => {
        let count = 0;
        const interval = setInterval(() => {
            count += Math.floor(Math.random() * 5) + 1;
            if (count >= 100) {
                count = 100;
                setCounter(100);
                clearInterval(interval);

                // Exit animation
                setTimeout(() => {
                    const tl = gsap.timeline({
                        onComplete: () => {
                            if (onComplete) onComplete();
                        }
                    });

                    tl.to(counterRef.current, {
                        y: -100,
                        opacity: 0,
                        duration: 0.8,
                        ease: "power4.inOut"
                    })
                        .to(containerRef.current, {
                            y: "-100%",
                            duration: 1.2,
                            ease: "expo.inOut"
                        }, "-=0.4");
                }, 500);
            } else {
                setCounter(count);
            }
        }, 50);

        return () => clearInterval(interval);
    }, [onComplete]);

    return (
        <div
            ref={containerRef}
            className="fixed inset-0 z-[99999] bg-[#1c1c1c] flex flex-col items-center justify-center overflow-hidden"
        >
            <div ref={counterRef} className="flex flex-col items-center">
                <div className="font-montreal text-8xl md:text-9xl font-bold text-[#e5e5e5] tabular-nums tracking-tighter">
                    {counter.toString().padStart(2, '0')}
                </div>
                <div className="font-grotesk text-[10px] tracking-[0.5em] text-[#9a9a9a] uppercase mt-4">
                    INITIALIZING SYSTEM
                </div>
            </div>

            {/* Grid lines in loader for consistency */}
            <div className="absolute inset-0 pointer-events-none opacity-5">
                <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-white"></div>
                <div className="absolute top-1/2 left-0 right-0 h-[1px] bg-white"></div>
            </div>
        </div>
    );
}
