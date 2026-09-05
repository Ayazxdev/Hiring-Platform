import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

export default function Navbar({ isMenuOpen, onToggle, lenisInstance, onHomeClick }) {
    const navRef = useRef(null);

    useEffect(() => {
        // Entrance animation
        gsap.fromTo(navRef.current,
            { y: -20, opacity: 0 },
            { y: 0, opacity: 1, duration: 1, ease: 'power3.out', delay: 0.5 }
        );
    }, []);

    const handleLogoClick = () => {
        if (onHomeClick) {
            onHomeClick();
        } else {
            if (isMenuOpen) onToggle(); // Close menu if open
            if (lenisInstance) {
                lenisInstance.scrollTo('#hero', { duration: 2 });
            }
        }
    };

    return (
        <nav
            ref={navRef}
            className={`fixed top-0 left-0 w-full z-[120] px-6 md:px-8 py-1 md:py-2 flex justify-between items-center transition-colors duration-500 ${isMenuOpen ? 'text-[#EDEDED]' : ''}`}
        >
            {/* Left: Product name (Logo) */}
            <button
                onClick={handleLogoClick}
                className={`nav-product-name product-label font-montreal ${isMenuOpen ? 'opacity-100' : ''} text-left pointer-events-auto`}
            >
                FAIR HIRING NETWORK
            </button>

            {/* Right: Menu button */}
            <button
                onClick={onToggle}
                className={`nav-menu-button menu-button font-grotesk pointer-events-auto ${isMenuOpen ? '!border-[#EDEDED] !text-[#EDEDED] hover:!bg-[#EDEDED] hover:!text-[#1A1A1A]' : ''}`}
            >
                {isMenuOpen ? '[ CLOSE ]' : '[ MENU ]'}
            </button>
        </nav>
    );
}
