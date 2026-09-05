import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import GridPlus from './GridPlus';

gsap.registerPlugin(ScrollTrigger);

export default function SectionCapabilities() {
    const sectionRef = useRef(null);
    const introRef = useRef(null);
    const videoRef = useRef(null);
    const capabilitiesRef = useRef(null);

    const capabilities = [
        { id: '01', name: 'Multi-Source Skill Verification' },
        { id: '02', name: 'Blind Bias Detection & Anonymization' },
        { id: '03', name: 'Cryptographic Credential Passport' },
        { id: '04', name: 'Multimodal AI Interview Simulation' },
        { id: '05', name: 'Deterministic Merit Matching' },
        { id: '06', name: 'Adversarial Defense & Human Review' },
    ];

    useEffect(() => {
        const ctx = gsap.context(() => {
            // Intro paragraph fade in
            gsap.fromTo(introRef.current,
                { y: 30, opacity: 0 },
                {
                    y: 0,
                    opacity: 1,
                    duration: 1,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: introRef.current,
                        start: 'top 80%',
                        toggleActions: 'play none none reverse',
                    }
                }
            );

            // Video container fade in
            gsap.fromTo(videoRef.current,
                { y: 40, opacity: 0 },
                {
                    y: 0,
                    opacity: 1,
                    duration: 1.2,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: videoRef.current,
                        start: 'top 85%',
                        toggleActions: 'play none none reverse',
                    }
                }
            );

            // Capabilities items reveal
            const items = capabilitiesRef.current.querySelectorAll('.capability-item');
            gsap.fromTo(items,
                { y: 30, opacity: 0 },
                {
                    y: 0,
                    opacity: 1,
                    duration: 1.2,
                    stagger: 0.15,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: capabilitiesRef.current,
                        start: 'top 85%',
                        toggleActions: 'play none none reverse',
                    }
                }
            );

            // NAVBAR COLOR TOGGLE
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
            className="section-capabilities relative min-h-screen bg-[#e5e5e5] pt-16 pb-24 px-6 md:px-12"
        >
            {/* Grid markers */}
            <GridPlus className="left-6 top-12" />
            <GridPlus className="right-6 top-12 translate-x-1/2" />

            <div className="max-w-[1440px] mx-auto h-full flex flex-col justify-between">

                {/* 1. TOP SECTION: Editorial Text */}
                <div ref={introRef} className="max-w-[90%] lg:max-w-[75%] mb-32 pt-12">
                    <p className="text-[#1c1c1c] text-3xl md:text-4xl lg:text-[2.75rem] leading-[1.15] font-normal tracking-[-0.02em] font-montreal">
                        Our platform is built as a system, not a tool. We help companies make sense of hiring data and turn it into clear, purposeful decisions that stay true to their values.
                        <br />
                        <br />
                        Everything we create is built in close collaboration with ethical standards and human insight, working together to bring fairness to life with clarity and intention.
                    </p>
                </div>

                {/* 2. BOTTOM SECTION: 3-Column Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-y-12 lg:gap-8 items-start relative z-10">

                    {/* COL 1: Image/Video (Span 4) */}
                    <div ref={videoRef} className="col-span-12 lg:col-span-4 pr-12">
                        <div className="aspect-[4/3] bg-[#111111] rounded-sm overflow-hidden w-full max-w-[280px] shadow-2xl relative">
                            <video
                                className="w-full h-full object-cover"
                                autoPlay
                                loop
                                muted
                                playsInline
                                src="/media/video/capability.mp4"
                            />
                            {/* Technical Overlay */}
                            <div className="absolute inset-0 border border-white/5 pointer-events-none p-4">
                                <span className="text-[8px] text-white/30 uppercase tracking-widest font-grotesk">CAP_PROC_V3</span>
                            </div>
                        </div>
                    </div>

                    {/* COL 2: Title (Span 4) */}
                    <div className="col-span-12 lg:col-span-3 pt-4">
                        <h3 className="text-black text-sm font-black font-grotesk uppercase tracking-wide">
                            CAPABILITIES
                        </h3>
                    </div>

                    {/* COL 3: List (Span 4) */}
                    <div ref={capabilitiesRef} className="col-span-12 lg:col-span-5 pt-2">
                        <div className="flex flex-col w-full">
                            {capabilities.map((capability, index) => (
                                <div
                                    key={capability.id}
                                    className="capability-item group cursor-pointer flex items-baseline justify-between py-6 border-t border-black/80 relative"
                                    style={{
                                        borderBottom: index === capabilities.length - 1 ? '1px solid rgba(0,0,0,0.8)' : 'none'
                                    }}
                                >
                                    {/* Text container for underline effect */}
                                    <div className="relative overflow-hidden">
                                        <span className="text-[#1c1c1c] text-base md:text-lg font-inter font-normal transition-all duration-300 group-hover:font-medium relative z-10 block">
                                            {capability.name}
                                        </span>
                                        {/* Animated Underline */}
                                        <span className="absolute left-0 bottom-0 w-full h-[1px] bg-black transform scale-x-0 origin-left transition-transform duration-500 ease-out group-hover:scale-x-100"></span>
                                    </div>

                                    {/* ID */}
                                    <span className="text-black text-[10px] font-grotesk font-bold tracking-widest opacity-100">
                                        [ {capability.id} ]
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>
            </div>
        </section>
    );
}
