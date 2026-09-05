import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import GridPlus from './GridPlus';

gsap.registerPlugin(ScrollTrigger);

export default function Hero({ isSiteLoaded }) {
    const containerRef = useRef(null);
    const markersContainerRef = useRef(null);
    const titlesContainerRef = useRef(null);
    const subtextRef = useRef(null);
    const titleLinesRef = useRef([]);

    useEffect(() => {
        if (!isSiteLoaded) return;

        const ctx = gsap.context(() => {
            // Masked reveal for title lines and subtext
            const tl = gsap.timeline();

            // Split titles for masked reveal
            titleLinesRef.current.forEach((line, i) => {
                if (line) gsap.set(line, { y: '100%' });
            });

            tl.to(titleLinesRef.current, {
                y: '0%',
                duration: 1.2,
                stagger: 0.1,
                ease: "expo.out",
                delay: 0.2
            })
                .fromTo(subtextRef.current,
                    { opacity: 0, y: 10 },
                    { opacity: 1, y: 0, duration: 1, ease: "power2.out" },
                    "-=0.6"
                );

            // Fade and blur title text as user scrolls
            const textScrollTl = gsap.timeline({
                scrollTrigger: {
                    trigger: '.hero-section',
                    start: 'top top',
                    end: '100% top',
                    scrub: true,
                }
            });

            textScrollTl
                .to(titlesContainerRef.current, {
                    opacity: 0,
                    filter: 'blur(10px)',
                    scale: 0.98,
                    ease: 'power2.in',
                    duration: 2.5
                }, 7)
                .set(titlesContainerRef.current, { display: 'none' }, 10);

            // Parallax animation for info markers
            const markers = containerRef.current.querySelectorAll('.hero-info-marker');
            const markerTimeline = gsap.timeline({
                scrollTrigger: {
                    trigger: '.hero-section',
                    start: 'top top',
                    end: 'bottom+=200vh top',
                    scrub: 1.5,
                },
            });

            gsap.set(markersContainerRef.current, { y: '0vh' });
            gsap.set(markers, { opacity: 1, x: 0, scale: 1 });

            markerTimeline
                .to(markersContainerRef.current, { y: '-10vh', ease: 'none', duration: 4 }, 0)
                .to(markersContainerRef.current, { opacity: 0, ease: 'power2.in', duration: 2 }, 3);

            markers.forEach((marker, index) => {
                gsap.to(marker, {
                    scrollTrigger: {
                        trigger: '.hero-section',
                        start: `${5 + (index * 5)}% top`,
                        end: `${15 + (index * 5)}% top`,
                        scrub: 1,
                    },
                    opacity: 0,
                    y: -30,
                    filter: 'blur(8px)',
                    scale: 0.8,
                    ease: 'power2.in'
                });
            });
        }, containerRef);

        return () => ctx.revert();
    }, [isSiteLoaded]);

    return (
        <section id="hero" ref={containerRef} className="hero-section relative w-full h-[300vh] bg-[#1c1c1c] text-white">
            {/* Grid markers */}
            <GridPlus className="left-8 top-12 md:left-16" />
            <GridPlus className="right-8 top-12 md:right-16 translate-x-1/2" />

            {/* Fixed text content - Slightly higher to avoid cutting off at bottom */}
            <div className="hero-text-container fixed left-0 top-[53%] -translate-y-1/2 w-full md:w-1/2 pl-8 md:pl-16 pr-8 z-[40] pointer-events-none">
                <div className="flex flex-col items-start gap-8 md:gap-12">
                    <div ref={titlesContainerRef} className="flex flex-col items-start">
                        {['FAIR', 'HIRING', 'VERIFIED', 'SKILLS'].map((word, i) => (
                            <div key={word} className="overflow-hidden">
                                <h1
                                    ref={el => titleLinesRef.current[i] = el}
                                    className="hero-title-word text-[clamp(4rem,9.5vw,11rem)] leading-[0.85]"
                                    style={{ transform: 'translateY(100%)' }}
                                >
                                    {word}
                                </h1>
                            </div>
                        ))}
                    </div>

                    <div className="relative" ref={subtextRef} style={{ opacity: 0 }}>
                        <p className="hero-badge transition-transform duration-700">NO BIAS • ONLY SKILL</p>
                    </div>
                </div>
            </div>

            {/* Right side - Data cloud in the top-right black space */}
            <div
                ref={markersContainerRef}
                className="hero-data-markers fixed right-0 top-0 w-[65%] h-[80vh] pointer-events-none z-[20]"
            >
                {/* WIDELY DISPERSED MARKERS */}

                {/* 1. Far Top Right */}
                <div className="absolute top-[15%] right-[20%] hero-info-marker font-mono text-[10px] md:text-xs opacity-50 text-right">
                    [ GITHUB.ANALYSIS.V2 ]
                </div>

                {/* 2. Top Center-Left (Near Title) */}
                <div className="absolute top-[18%] right-[65%] hero-info-marker font-mono text-[10px] md:text-xs opacity-30 text-right">
                    [ SKILL.PASSPORT: ACTIVE ]
                </div>

                {/* 3. Middle Right (Wide gap) */}
                <div className="absolute top-[40%] right-[12%] hero-info-marker font-mono text-[10px] md:text-xs opacity-40 text-right">
                    [ BIAS.ZERO: CONFIRMED ]
                </div>

                {/* 4. Upper Middle (Floating high) */}
                <div className="absolute top-[40%] right-[50%] hero-info-marker font-mono text-[10px] md:text-xs opacity-30 text-right">
                    [ AGENT.SCORING: 98% ]
                </div>

                {/* 5. Bottom Center (Deep spacing) */}
                <div className="absolute top-[65%] right-[45%] hero-info-marker font-mono text-[10px] md:text-xs opacity-30 text-right">
                    [ LEETCODE.METRICS: SYNCED ]
                </div>

                {/* 6. Bottom Right (Corner anchor) */}
                <div className="absolute top-[75%] right-[8%] hero-info-marker font-mono text-[10px] md:text-xs opacity-20 text-right">
                    [ ARCHITECTURE.VALIDATED ]
                </div>
            </div>
        </section>
    );
}
