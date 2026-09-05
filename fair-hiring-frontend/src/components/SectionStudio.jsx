import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import GridPlus from './GridPlus';

gsap.registerPlugin(ScrollTrigger);

/**
 * SectionStudio component - A design studio editorial layout
 * Updated with Infinite Auto-Marquee, specialized Studio video, and "LET'S START" button.
 */
export default function SectionStudio({ onOpenMenu }) {
    const containerRef = useRef(null);
    const marqueeContainerRef = useRef(null);
    const marqueeTrackRef = useRef(null);
    const studioSectionRef = useRef(null);
    const mediaContainerRef = useRef(null);
    const textColumnRef = useRef(null);
    const buttonRef = useRef(null);

    useEffect(() => {
        const ctx = gsap.context(() => {
            // 1. INFINITE AUTO-MARQUEE
            const marquee = marqueeTrackRef.current;
            const totalWidth = marquee.scrollWidth / 2;

            gsap.to(marquee, {
                x: -totalWidth,
                duration: 20,
                ease: 'none',
                repeat: -1,
            });

            // 2. SECTION 2 — MEDIA + TEXT SPLIT
            // Media Parallax
            gsap.to(mediaContainerRef.current, {
                y: -40,
                ease: 'none',
                scrollTrigger: {
                    trigger: mediaContainerRef.current,
                    start: 'top bottom',
                    end: 'bottom top',
                    scrub: true,
                }
            });

            // Text Motion (Fade-in + slight Y translate)
            const textLines = textColumnRef.current.querySelectorAll('.text-reveal-line');
            gsap.fromTo(textLines,
                { opacity: 0, y: 10 },
                {
                    opacity: 1,
                    y: 0,
                    duration: 1,
                    stagger: 0.15,
                    ease: 'power2.out',
                    scrollTrigger: {
                        trigger: textColumnRef.current,
                        start: 'top 80%',
                        toggleActions: 'play none none reverse',
                    }
                }
            );
            // 4. NAVBAR COLOR TOGGLE
            ScrollTrigger.create({
                trigger: containerRef.current,
                start: 'top 60px',
                end: 'bottom 60px',
                toggleClass: { targets: 'nav', className: 'navbar-dark' },
            });
        }, containerRef);

        return () => ctx.revert();
    }, []);

    const handleButtonHover = (e, isEnter) => {
        const chars = e.currentTarget.querySelectorAll('.btn-char');
        if (isEnter) {
            // Character jitter/glitch effect
            gsap.to(chars, {
                y: -2,
                opacity: 0.7,
                stagger: {
                    each: 0.01,
                    from: "random"
                },
                duration: 0.05,
                overwrite: true,
                onComplete: () => {
                    gsap.to(chars, {
                        y: 0,
                        opacity: 1,
                        stagger: {
                            each: 0.01,
                            from: "random"
                        },
                        duration: 0.1
                    });
                }
            });
        }
    };

    const marqueePhrases = [
        "FAIR HIRING NETWORK",
        "VERIFIED SKILLS",
        "TRANSPARENT MATCHING",
        "BIAS-AWARE SYSTEMS",
        "HUMAN-IN-THE-LOOP",
        "CREDENTIAL INTEGRITY"
    ];

    return (
        <div ref={containerRef} className="section-studio relative bg-[#E6E6E4] text-[#111111] overflow-hidden">
            <GridPlus className="left-8 top-12 md:left-16" />
            <GridPlus className="right-8 top-12 md:right-16 translate-x-1/2" />

            {/* 🧾 SECTION 1 — MOVING MARQUEE (TOP — CONTINUOUS) */}
            <div ref={marqueeContainerRef} className="SectionMarquee w-full border-b border-[#1c1c1c] bg-[#E6E6E4] z-50 overflow-hidden py-12">
                <div
                    ref={marqueeTrackRef}
                    className="flex items-center whitespace-nowrap"
                    style={{ transform: 'translate3d(0, 0, 0)' }}
                >
                    {[...Array(2)].map((_, groupIdx) => (
                        <div key={groupIdx} className="flex items-center">
                            {marqueePhrases.map((phrase, idx) => (
                                <div key={idx} className="flex items-center">
                                    <h2 className="font-['Druk_Wide'] text-4xl lg:text-5xl font-black uppercase tracking-[-0.02em]">
                                        {phrase}
                                    </h2>
                                    <span className="mx-12 text-4xl lg:text-5xl font-black opacity-30">·</span>
                                </div>
                            ))}
                        </div>
                    ))}
                </div>
            </div>

            {/* 🖼 SECTION 2 — MEDIA + TEXT SPLIT (STUDIO STYLE) */}
            <div ref={studioSectionRef} className="StudioSection max-w-[1440px] mx-auto px-6 md:px-16 pt-24 pb-12 lg:pt-32 lg:pb-20">

                <div className="grid grid-cols-12 gap-8 items-start lg:items-center">

                    {/* LEFT SIDE — MEDIA CONTAINER (7 columns) */}
                    <div
                        ref={mediaContainerRef}
                        className="StudioMedia col-span-12 lg:col-span-7 flex flex-col items-start gap-12"
                    >
                        <div className="VideoContainer relative w-full aspect-video bg-[#111111] rounded-[2px] overflow-hidden shadow-xl"
                            style={{ maxWidth: '840px' }}>
                            <video
                                className="w-full h-full object-cover opacity-80"
                                autoPlay
                                loop
                                muted
                                playsInline
                                src="/media/video/section%20studio.mp4"
                            />
                            <div className="absolute inset-0 border border-white/5 pointer-events-none"></div>
                        </div>

                        {/* LET'S START BUTTON - Under Video */}
                        <div className="pl-2">
                            <button
                                ref={buttonRef}
                                onClick={onOpenMenu}
                                onMouseEnter={(e) => handleButtonHover(e, true)}
                                className="group relative py-4 bg-transparent text-[#111111] overflow-hidden rounded-sm transition-all duration-300 cursor-pointer"
                            >
                                <span className="relative z-10 font-grotesk font-extrabold text-base tracking-[0.4em] flex gap-[2px]">
                                    {"LET'S START".split("").map((char, i) => (
                                        <span key={i} className="btn-char inline-block">{char === " " ? "\u00A0" : char}</span>
                                    ))}
                                </span>

                                {/* Mechanical sweep line effect */}
                                <div className="absolute bottom-0 left-0 w-full h-[2px] bg-[#111111] scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left"></div>

                                {/* Subtle light sweep */}
                                <div className="absolute inset-x-0 top-0 h-[1px] bg-black/10 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
                            </button>
                        </div>
                    </div>

                    {/* RIGHT SIDE — TEXT COLUMN (4 columns) */}
                    <div
                        ref={textColumnRef}
                        className="StudioText col-span-12 lg:col-span-4 lg:col-start-9 space-y-10"
                    >
                        <div className="text-reveal-line">
                            <span className="font-['Neue_Montreal'] text-[10px] tracking-[0.25em] font-bold text-black uppercase opacity-100">
                                THE SYSTEM
                            </span>
                        </div>

                        <div className="text-reveal-line">
                            <h3 className="font-['Druk_Wide'] text-4xl lg:text-5xl font-black uppercase leading-[0.9] tracking-[-0.03em]">
                                ART,<br />TECHNOLOGY,<br />FAIRNESS.
                            </h3>
                        </div>

                        <div className="space-y-6">
                            <div className="text-reveal-line">
                                <p className="font-['Neue_Montreal'] text-base md:text-lg leading-relaxed max-w-[480px] font-normal opacity-90">
                                    Our infrastructure is designed where engineering rigor, ethical constraints, and human judgment meet.
                                    <br /><br />
                                    We build hiring systems that treat candidate data as evidence — not assumptions — and make every decision traceable, reviewable, and accountable.
                                </p>
                            </div>

                            <div className="text-reveal-line">
                                <p className="font-['Neue_Montreal'] text-base md:text-lg leading-relaxed max-w-[480px] font-normal opacity-90">
                                    By combining agent-based verification, bias detection, and transparent scoring, we replace opaque hiring pipelines with systems companies and candidates can understand and trust.
                                </p>
                            </div>
                        </div>

                        <div className="text-reveal-line pt-2 border-t border-[#111111]/10">
                            <p className="font-['Neue_Montreal'] text-[11px] leading-relaxed max-w-[480px] font-medium opacity-60">
                                We don’t optimize for speed alone. We optimize for correctness, fairness, and long-term trust.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
