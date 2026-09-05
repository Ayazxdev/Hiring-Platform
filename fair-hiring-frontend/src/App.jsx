import { useEffect, useRef, useState, lazy, Suspense, Component } from "react";
import Lenis from "lenis";
import gsap from "gsap";
import { Routes, Route, useNavigate, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error("App ErrorBoundary caught:", error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="fixed inset-0 bg-[#1c1c1c] z-[200] flex flex-col items-center justify-center font-grotesk text-white p-8">
          <h1 className="text-2xl font-black uppercase tracking-widest mb-4">Something went wrong</h1>
          <p className="text-xs opacity-50 max-w-md text-center">{this.state.error?.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-8 border border-white px-6 py-3 text-xs font-black uppercase tracking-widest hover:bg-white hover:text-[#1c1c1c] transition-colors"
          >
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
import Preloader from "./components/Preloader";
import MenuOverlay from "./components/MenuOverlay";
import { AnimatePresence } from "framer-motion";
import "./styles/globals.css";

// Lazy load heavy components
const Hero = lazy(() => import("./components/Hero"));
const ParallaxObject = lazy(() => import("./components/ParallaxObject"));
const SectionVision = lazy(() => import("./components/SectionVision"));
const SectionCapabilities = lazy(
    () => import("./components/SectionCapabilities"),
);
const SectionStudio = lazy(() => import("./components/SectionStudio"));
const ContactSection = lazy(() => import("./components/ContactSection"));
const CompanyHiringFlow = lazy(() => import("./components/CompanyHiringFlow"));
const CompanyDashboard = lazy(() => import("./components/CompanyDashboard"));
const CompanyRolePipeline = lazy(
    () => import("./components/CompanyRolePipeline"),
);
const CompanyCandidateReview = lazy(
    () => import("./components/CompanyCandidateReview"),
);
const CompanySelectedCandidates = lazy(
    () => import("./components/CompanySelectedCandidates"),
);
const CandidateExperience = lazy(
    () => import("./components/CandidateExperience"),
);
const ReviewerExperience = lazy(
    () => import("./components/ReviewerExperience"),
);
const CandidateAuth = lazy(() => import("./components/CandidateAuth"));
const CompanyAuth = lazy(() => import("./components/CompanyAuth"));
const ProtocallApp = lazy(() => import("./components/Protocall/ProtocallApp"));
const SkillPassport = lazy(() => import("./components/SkillPassport"));
const SystemFlow = lazy(() => import("./components/SystemFlow"));

function App() {
    const navigate = useNavigate();
    const location = useLocation();
    const [lenis, setLenis] = useState(null);
    const isPassportRoute = location.pathname.startsWith("/passport/");
    const [isLoading, setIsLoading] = useState(!isPassportRoute);
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    // Company state (can be moved to a context if needed, but keeping for now)
    const [selectedRole, setSelectedRole] = useState(null);
    const [viewingPipeline, setViewingPipeline] = useState(false);
    const [selectedCandidate, setSelectedCandidate] = useState(null);
    const [viewingSelected, setViewingSelected] = useState(false);
    const [isDashboardFromFlow, setIsDashboardFromFlow] = useState(false);
    const [menuInitialView, setMenuInitialView] = useState("main");
    const [isGlobalModalOpen, setIsGlobalModalOpen] = useState(false);

    const cursorRef = useRef(null);

    const isStandaloneProtocol = import.meta.env.VITE_STANDALONE_PROTOCOL === 'true';

    useEffect(() => {
        // Initialize Lenis smooth scroll
        const lenisInstance = new Lenis({
            duration: 1.2,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
            smoothWheel: true,
            wheelMultiplier: 1,
            touchMultiplier: 2,
        });

        setLenis(lenisInstance);

        function raf(time) {
            lenisInstance.raf(time);
            requestAnimationFrame(raf);
        }
        requestAnimationFrame(raf);

        lenisInstance.on("scroll", () => {
            if (window.ScrollTrigger) window.ScrollTrigger.update();
        });

        return () => {
            lenisInstance.destroy();
        };
    }, []);

    useEffect(() => {
        const handleModalChange = (e) => setIsGlobalModalOpen(e.detail.open);
        window.addEventListener('modal-state-change', handleModalChange);
        return () => window.removeEventListener('modal-state-change', handleModalChange);
    }, []);

    useEffect(() => {
        if (!lenis) return;

        const isOverlayActive = (location.pathname !== "/" && !location.pathname.startsWith("/passport/")) || isMenuOpen || isGlobalModalOpen;

        if (isOverlayActive) {
            lenis.stop();
        } else {
            lenis.start();
        }
    }, [lenis, location.pathname, isMenuOpen, isGlobalModalOpen]);

    useEffect(() => {
        // Custom cursor
        const cursor = cursorRef.current;
        if (!cursor) return;

        const xSetter = gsap.quickSetter(cursor, "x", "px");
        const ySetter = gsap.quickSetter(cursor, "y", "px");

        const moveCursor = (e) => {
            xSetter(e.clientX - 4);
            ySetter(e.clientY - 4);
        };

        const handleMouseOver = (e) => {
            const isHoverable =
                e.target.tagName === "BUTTON" ||
                e.target.tagName === "A" ||
                e.target.classList.contains("menu-button") ||
                e.target.classList.contains("group") ||
                e.target.classList.contains("product-label");

            const isMenuItem =
                e.target.closest("button")?.classList.contains("group") && isMenuOpen;

            if (isMenuItem) {
                cursor.classList.add("crosshair");
                cursor.classList.remove("hover");
            } else if (isHoverable) {
                cursor.classList.add("hover");
                cursor.classList.remove("crosshair");
            } else {
                cursor.classList.remove("hover");
                cursor.classList.remove("crosshair");
            }
        };

        window.addEventListener("mousemove", moveCursor);
        window.addEventListener("mouseover", handleMouseOver);

        return () => {
            window.removeEventListener("mousemove", moveCursor);
            window.removeEventListener("mouseover", handleMouseOver);
        };
    }, [isMenuOpen]);

    const handleHomeClick = () => {
        if (location.pathname !== "/") {
            navigate("/");
        } else if (lenis) {
            lenis.scrollTo("#hero", { duration: 2 });
        }
        setIsMenuOpen(false);
    };

    // STANDALONE PROTOCOL MODE: Bypass everything else
    if (isStandaloneProtocol) {
        return (
            <div className="app bg-[#e5e5e5]">
                {/* Custom cursor for consistent branding */}
                <div ref={cursorRef} className="cursor-dot"></div>
                <Suspense fallback={<div className="fixed inset-0 bg-[#1c1c1c] z-[100] flex items-center justify-center font-grotesk text-white text-xs uppercase tracking-widest">Protocol Initializing...</div>}>
                    <ErrorBoundary>
                        <Routes>
                            <Route path="*" element={<ProtocallApp onExit={() => {}} />} />
                        </Routes>
                    </ErrorBoundary>
                </Suspense>
            </div>
        );
    }

    return (
        <div className="app relative bg-[#e5e5e5]">
            {isLoading && <Preloader onComplete={() => setIsLoading(false)} />}

            <MenuOverlay
                isOpen={isMenuOpen}
                onClose={() => setIsMenuOpen(false)}
                lenisInstance={lenis}
                initialView={menuInitialView}
                onSelectCompany={() => {
                    setIsMenuOpen(false);
                    setIsDashboardFromFlow(false);
                    setTimeout(() => navigate("/company"), 600);
                }}
                onSelectDashboard={() => {
                    setIsMenuOpen(false);
                    setIsDashboardFromFlow(true);
                    setTimeout(() => navigate("/company"), 600);
                }}
                onSelectCandidate={() => {
                    setIsMenuOpen(false);
                    setTimeout(() => navigate("/candidate"), 600);
                }}
                onSelectReviewer={() => {
                    setIsMenuOpen(false);
                    setTimeout(() => navigate("/reviewer"), 600);
                }}
            />

            {!location.pathname.startsWith("/passport/") &&
                location.pathname !== "/system-flow" &&
                location.pathname !== "/company" &&
                location.pathname !== "/candidate" && (
                    <Navbar
                        isMenuOpen={isMenuOpen}
                        onToggle={() => {
                            if (!isMenuOpen) setMenuInitialView("main");
                            setIsMenuOpen(!isMenuOpen);
                        }}
                        lenisInstance={lenis}
                        onHomeClick={handleHomeClick}
                    />
                )}

            {/* Custom cursor */}
            <div ref={cursorRef} className="cursor-dot"></div>

            <AnimatePresence mode="wait">
                <Suspense
                    fallback={
                        <div className="fixed inset-0 bg-[#1c1c1c] z-[100] flex items-center justify-center font-grotesk text-white text-xs tracking-widest uppercase">
                            Initializing...
                        </div>
                    }
                >
                    <ErrorBoundary>
                    <Routes location={location} key={location.pathname}>
                        <Route
                            path="/"
                            element={
                                <>
                                    <ParallaxObject
                                        lenisInstance={lenis}
                                        isActive={location.pathname === "/" && !isMenuOpen}
                                    />
                                    <Hero isSiteLoaded={!isLoading} />
                                    <div className="relative z-[50]">
                                        <SectionVision />
                                    </div>
                                    <div className="w-full h-px bg-[#1c1c1c] opacity-20 relative z-[50]"></div>
                                    <div className="relative z-[50]">
                                        <SectionCapabilities />
                                    </div>
                                    <div className="w-full h-px bg-[#1c1c1c] opacity-20 relative z-[50]"></div>
                                    <div className="relative z-[50]">
                                        <SectionStudio
                                            onOpenMenu={() => {
                                                setMenuInitialView("main");
                                                setIsMenuOpen(true);
                                            }}
                                        />
                                    </div>
                                    <div className="w-full h-px bg-[#1c1c1c] opacity-20 relative z-[50]"></div>
                                    <div className="relative z-[50]">
                                        <ContactSection />
                                    </div>
                                </>
                            }
                        />

                        <Route
                            path="/company"
                            element={
                                <div className="overlay-wrapper" data-lenis-prevent>
                                    {localStorage.getItem("fhn_company_id") ? (
                                        !isDashboardFromFlow ? (
                                            <CompanyHiringFlow
                                                onExit={() => {
                                                    navigate("/");
                                                    setMenuInitialView("company");
                                                    setIsMenuOpen(true);
                                                }}
                                                onComplete={() => setIsDashboardFromFlow(true)}
                                            />
                                        ) : !viewingPipeline ? (
                                            <CompanyDashboard
                                                onNavigateToRole={(roleId) => {
                                                    setSelectedRole(roleId);
                                                    setViewingPipeline(true);
                                                }}
                                                onExit={() => {
                                                    navigate("/");
                                                    setMenuInitialView("company");
                                                    setIsMenuOpen(true);
                                                }}
                                            />
                                        ) : !selectedCandidate && !viewingSelected ? (
                                            <CompanyRolePipeline
                                                roleId={selectedRole}
                                                onBack={() => setViewingPipeline(false)}
                                                onSelectCandidate={(candidate) =>
                                                    setSelectedCandidate(candidate)
                                                }
                                                onViewSelected={() => setViewingSelected(true)}
                                            />
                                        ) : selectedCandidate ? (
                                            <CompanyCandidateReview
                                                candidate={selectedCandidate}
                                                onBack={() => setSelectedCandidate(null)}
                                                onAction={(action) => {
                                                    console.log("Agent Action:", action);
                                                    setTimeout(() => setSelectedCandidate(null), 500);
                                                }}
                                            />
                                        ) : (
                                            <CompanySelectedCandidates
                                                roleId={selectedRole}
                                                onBack={() => setViewingSelected(false)}
                                            />
                                        )
                                    ) : (
                                        <CompanyAuth
                                            onExit={() => {
                                                navigate("/");
                                                setIsMenuOpen(true);
                                            }}
                                        />
                                    )}
                                </div>
                            }
                        />

                        <Route
                            path="/candidate"
                            element={
                                <div className="overlay-wrapper" data-lenis-prevent>
                                    {localStorage.getItem("fhn_candidate_anon_id") ? (
                                        <CandidateExperience
                                            onExit={() => {
                                                navigate("/");
                                                setMenuInitialView("main");
                                                setIsMenuOpen(true);
                                            }}
                                        />
                                    ) : (
                                        <CandidateAuth
                                            onExit={() => {
                                                navigate("/");
                                                setIsMenuOpen(true);
                                            }}
                                        />
                                    )}
                                </div>
                            }
                        />

                        <Route
                            path="/reviewer"
                            element={
                                <div className="overlay-wrapper" data-lenis-prevent>
                                    <ReviewerExperience
                                        onExit={() => {
                                            navigate("/");
                                            setIsMenuOpen(true);
                                        }}
                                    />
                                </div>
                            }
                        />

                        <Route
                            path="/candidate/interview"
                            element={
                                <div className="overlay-wrapper" data-lenis-prevent>
                                    <ProtocallApp
                                        onExit={() => {
                                            navigate("/candidate");
                                        }}
                                    />
                                </div>
                            }
                        />

                        <Route
                            path="/protocol"
                            element={
                                <div className="overlay-wrapper" data-lenis-prevent>
                                    <ProtocallApp
                                        onExit={() => {
                                            navigate("/");
                                        }}
                                    />
                                </div>
                            }
                        />

                        <Route
                            path="/passport/:id"
                            element={
                                <SkillPassport isStandalone={true} candidateId={location.pathname.split("/")[2]} />
                            }
                        />

                        <Route
                            path="/system-flow"
                            element={<SystemFlow />}
                        />
                    </Routes>
                    </ErrorBoundary>
                </Suspense>
            </AnimatePresence>
        </div>
    );
}

export default App;
