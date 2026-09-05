import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import GridPlus from './GridPlus';

gsap.registerPlugin(ScrollTrigger);

/**
 * SectionVision - Merged Vision and Technology into one large continuous section
 * Updated with vertical technical video centered between editorial blocks.
 */
export default function SectionVision() {
    const navigate = useNavigate();
    const sectionRef = useRef(null);
    const headingRef = useRef(null);
    const bodyRef = useRef(null);
    const ctaRef = useRef(null);
    const techHeadlineRef = useRef(null);

    useEffect(() => {
        const ctx = gsap.context(() => {
            // 1. VISION REVEAL LOGIC
            const words = headingRef.current.querySelectorAll('.heading-line');
            gsap.fromTo(words,
                { y: 100, opacity: 0 },
                {
                    y: 0,
                    opacity: 1,
                    duration: 1,
                    stagger: 0.2,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: headingRef.current,
                        start: 'top 75%',
                        toggleActions: 'play none none reverse',
                    }
                }
            );

            // Body text fade in
            gsap.fromTo(bodyRef.current,
                { y: 30, opacity: 0 },
                {
                    y: 0,
                    opacity: 1,
                    duration: 0.8,
                    ease: 'power2.out',
                    scrollTrigger: {
                        trigger: bodyRef.current,
                        start: 'top 80%',
                        toggleActions: 'play none none reverse',
                    }
                }
            );

            // CTA fade in
            gsap.fromTo(ctaRef.current,
                { y: 20, opacity: 0 },
                {
                    y: 0,
                    opacity: 1,
                    duration: 0.6,
                    ease: 'power2.out',
                    scrollTrigger: {
                        trigger: ctaRef.current,
                        start: 'top 85%',
                        toggleActions: 'play none none reverse',
                    }
                }
            );
            // 2. NAVBAR COLOR TOGGLE
            ScrollTrigger.create({
                trigger: sectionRef.current,
                start: 'top 60px',
                end: 'bottom 60px',
                toggleClass: { targets: 'nav', className: 'navbar-dark' },
            });
        }, sectionRef);

        return () => ctx.revert();
    }, []);

    return (
        <section
            ref={sectionRef}
            className="section-vision relative bg-[#e5e5e5] px-6 md:px-8 overflow-hidden"
        >
            {/* Grid markers */}
            <GridPlus className="left-6 top-12 md:left-16" />
            <GridPlus className="right-6 top-12 md:right-16 translate-x-1/2" />

            <div className="max-w-[1440px] mx-auto pt-20 pb-16 md:pt-32 md:pb-24">

                {/* 12-column Grid wrapper - Centered to place video in the middle of text blocks */}
                <div className="grid grid-cols-12 gap-8 items-center min-h-[100vh]">

                    {/* LEFT SIDE: Content Column */}
                    <div className="col-span-12 lg:col-span-7">

                        {/* PART 1: INTERSECTING FAIRNESS */}
                        <div className="mb-24 md:mb-32">
                            <h2
                                ref={headingRef}
                                className="font-montreal font-extrabold uppercase leading-[0.9] text-[#1c1c1c] text-[clamp(4rem,10vw,11vw)] mb-24 md:mb-32"
                                style={{ willChange: 'transform, opacity' }}
                            >
                                <div className="heading-line">INTERSECTING</div>
                                <div className="heading-line">FAIRNESS</div>
                            </h2>

                            <div ref={bodyRef} className="space-y-6 text-[#1c1c1c] text-base md:text-lg font-inter leading-relaxed font-medium mb-12 max-w-[500px]">
                                <p>
                                    We build hiring systems where technology, ethics,
                                    and human judgment intersect.
                                </p>
                                <p>
                                    Our agent-driven infrastructure verifies real skills,
                                    detects bias before it impacts decisions, and creates
                                    transparent hiring experiences that companies and
                                    candidates can trust.
                                </p>
                            </div>

                            <div ref={ctaRef} className="group cursor-pointer" onClick={() => navigate('/system-flow')}>
                                <span className="font-grotesk uppercase tracking-[0.12em] text-[#1c1c1c] text-xs md:text-sm inline-block pb-1 relative">
                                    VIEW SYSTEM FLOW →
                                    <span className="absolute bottom-0 left-0 w-full h-[1px] bg-[#1c1c1c] scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left"></span>
                                </span>
                            </div>
                        </div>

                        {/* PART 2: & TECHNOLOGY */}
                        <div className="z-10">
                            <h2
                                ref={techHeadlineRef}
                                className="font-montreal font-extrabold uppercase leading-[0.85] text-[#000000] text-[clamp(4rem,12vw,14vw)]"
                                style={{ willChange: 'transform, opacity' }}
                            >
                                <div>&</div>
                                <div>TECHNOLOGY</div>
                            </h2>
                        </div>

                    </div>

                    {/* RIGHT SIDE: VERTICAL VIDEO CONTAINER (4 columns) */}
                    {/* Positioned with self-center to sit in the gap between the two left blocks */}
                    <div className="col-span-12 lg:col-span-4 lg:col-start-9 flex flex-col items-center">
                        <div
                            className="relative w-full aspect-[9/16] bg-[#111111] overflow-hidden rounded-sm shadow-2xl"
                        >
                            <video
                                className="w-full h-full object-cover grayscale opacity-100"
                                autoPlay
                                loop
                                muted
                                playsInline
                                src="/media/video/2nd%20sec.mp4"
                            />
                            {/* Technical Overlay */}
                            <div className="absolute inset-x-8 bottom-8 flex justify-between items-end border-t border-white/10 pt-4 opacity-70">
                                <span className="text-white text-[10px] uppercase tracking-[0.2em] font-grotesk">Infrastructure Protocol</span>
                                <span className="text-white text-[10px] uppercase tracking-[0.2em] font-grotesk">9:16 / 4K</span>
                            </div>
                            <div className="absolute top-8 right-8 flex items-center gap-2 opacity-80">
                                <div className="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse"></div>
                                <span className="text-white text-[8px] uppercase tracking-[0.3em] font-grotesk">LIVE_SCRIBE</span>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </section>
    );
}
