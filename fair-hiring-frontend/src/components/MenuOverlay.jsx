import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import GridPlus from './GridPlus';

export default function MenuOverlay({ isOpen, onClose, lenisInstance, onSelectCompany, onSelectDashboard, onSelectCandidate, onSelectReviewer, initialView = 'main' }) {
    const overlayRef = useRef(null);
    const contentRef = useRef(null);
    const gridLinesRef = useRef(null);
    const menuItemsRef = useRef([]);
    const [view, setView] = useState(initialView); // 'main' or 'company'

    useEffect(() => {
        if (isOpen) {
            setView(initialView);
        }
    }, [isOpen, initialView]);

    useEffect(() => {
        if (isOpen) {
            // Lock body scroll and Lenis
            document.body.style.overflow = 'hidden';
            if (lenisInstance) lenisInstance.stop();

            // Animation sequence
            const tl = gsap.timeline();

            // 1. Overlay slides in from right
            tl.fromTo(overlayRef.current,
                { x: '100%', pointerEvents: 'none' },
                { x: '0%', duration: 0.8, ease: "cubic-bezier(0.77, 0, 0.175, 1)", pointerEvents: 'auto' }
            );

            // 2. Grid lines reveal
            tl.fromTo(gridLinesRef.current,
                { opacity: 0 },
                { opacity: 1, duration: 0.5 },
                "-=0.4"
            );

            // 3. Menu items reveal (staggered slide up)
            tl.fromTo(menuItemsRef.current,
                { y: 80, opacity: 0 },
                { y: 0, opacity: 1, duration: 0.8, stagger: 0.1, ease: "expo.out", clearProps: "all" },
                "-=0.5"
            );

        } else {
            // Restore body scroll and Lenis
            document.body.style.overflow = '';
            if (lenisInstance) lenisInstance.start();

            // Exit animation
            gsap.to(overlayRef.current, {
                x: '100%',
                duration: 0.6,
                ease: "power3.inOut",
                pointerEvents: 'none'
            });
        }
    }, [isOpen, lenisInstance]);

    const handleItemClick = (role, index) => {
        if (role === "COMPANY") {
            setView('company');
            return;
        }

        if (role === "BACK") {
            setView('main');
            return;
        }

        // Selected item brightens, others fade
        const tl = gsap.timeline();

        // Disable pointer events during transition
        gsap.set(menuItemsRef.current, { pointerEvents: 'none' });

        tl.to(menuItemsRef.current, {
            opacity: 0.2,
            duration: 0.4,
            ease: "power2.out"
        })
            .to(menuItemsRef.current[index], {
                opacity: 1,
                duration: 0.4,
                ease: "power2.out"
            }, "-=0.4")
            .to(overlayRef.current, {
                x: '100%',
                duration: 0.8,
                ease: "expo.inOut",
                delay: 0.5,
                onComplete: () => {
                    if (role === "CREATE ROLE" && onSelectCompany) {
                        onSelectCompany();
                    } else if (role === "DASHBOARD" && onSelectDashboard) {
                        onSelectDashboard();
                    } else if (role === "CANDIDATE" && onSelectCandidate) {
                        onSelectCandidate();
                    } else if (role === "REVIEWER" && onSelectReviewer) {
                        onSelectReviewer();
                    } else if (role === "CONTACT") {
                        onClose();
                        if (lenisInstance) {
                            setTimeout(() => {
                                lenisInstance.scrollTo('#contact', { duration: 2 });
                            }, 600);
                        }
                    } else {
                        onClose();
                    }
                    // Important: Reset pointer events for next time it opens
                    gsap.set(menuItemsRef.current, { pointerEvents: 'auto' });
                    console.log(`Routing to /${role.toLowerCase().replace(' ', '-')}`);
                }
            });
    };

    if (!isOpen && !overlayRef.current) return null;

    const menuItems = {
        main: ["CANDIDATE", "COMPANY", "REVIEWER", "CONTACT"],
        company: ["CREATE ROLE", "DASHBOARD", "BACK"]
    };

    const currentItems = menuItems[view];

    return (
        <div
            ref={overlayRef}
            className="fixed inset-0 z-[110] bg-[#1A1A1A] text-[#EDEDED] flex items-center justify-end px-[8vw] transform translate-x-full overflow-hidden"
        >
            {/* Editorial Grid Lines */}
            <div ref={gridLinesRef} className="absolute inset-0 pointer-events-none z-0 opacity-10">
                <div className="absolute left-[33.33%] top-0 bottom-0 w-[1px] bg-[#333]"></div>
                <div className="absolute left-[66.66%] top-0 bottom-0 w-[1px] bg-[#333]"></div>
                <div className="absolute top-[33.33%] left-0 right-0 h-[1px] bg-[#333]"></div>
                <div className="absolute top-[66.66%] left-0 right-0 h-[1px] bg-[#333]"></div>

                {/* Plus markers at intersections */}
                <GridPlus className="left-[33.33%] top-[33.33%] opacity-20 text-[#EDEDED]" />
                <GridPlus className="left-[66.66%] top-[33.33%] opacity-20 text-[#EDEDED]" />
                <GridPlus className="left-[33.33%] top-[66.66%] opacity-20 text-[#EDEDED]" />
                <GridPlus className="left-[66.66%] top-[66.66%] opacity-20 text-[#EDEDED]" />
            </div>

            {/* Menu Content */}
            <div ref={contentRef} className="relative z-10 text-right min-w-[300px] md:min-w-[400px] pl-20">
                <div className="flex flex-col gap-4 md:gap-6">
                    {currentItems.map((item, i) => (
                        <div key={item} className="menu-item-wrapper">
                            <button
                                ref={el => menuItemsRef.current[i] = el}
                                onClick={() => handleItemClick(item, i)}
                                className="group relative block w-full text-right outline-none"
                            >
                                <span className={`font-montreal font-black leading-[0.95] tracking-[-0.03em] uppercase transition-all duration-500 group-hover:translate-x-[-1.5rem] group-hover:text-white inline-block pr-6 ${view === 'company' ? 'text-[clamp(2rem,5vw,6rem)]' : 'text-[clamp(2.5rem,8vw,10rem)]'} ${item === 'BACK' ? 'opacity-30 text-sm tracking-[0.4em] font-grotesk' : ''}`}>
                                    {item === 'BACK' ? '← ' + item : item}
                                </span>
                                {item !== 'BACK' && (
                                    <div className="absolute bottom-0 right-0 w-0 h-[2px] bg-[#FFFFFF] group-hover:w-full transition-all duration-700 ease-out origin-right"></div>
                                )}
                            </button>
                        </div>
                    ))}
                </div>
            </div>

        </div>
    );
}
