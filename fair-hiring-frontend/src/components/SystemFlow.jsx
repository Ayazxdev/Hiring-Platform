import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const FLOW_COLORS = {
    skill: '#FFFFFF',
    bias: '#FFFFFF',
    credential: '#FFFFFF',
    default: 'rgba(255, 255, 255, 0.1)'
};

const ICONS = {
    resume: <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />,
    github: <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />,
    coding: <><polyline points="4 17 10 11 4 5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><line x1="12" y1="19" x2="20" y2="19" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></>,
    tests: <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />,
    metadata: <><rect x="2" y="2" width="20" height="8" rx="2" ry="2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><rect x="2" y="14" width="20" height="8" rx="2" ry="2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><line x1="6" y1="6" x2="6.01" y2="6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><line x1="6" y1="18" x2="6.01" y2="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></>,
    parser: <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />,
    analyzer: <><circle cx="11" cy="11" r="8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><line x1="21" y1="21" x2="16.65" y2="16.65" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></>,
    evaluator: <><path d="M21.21 15.89A10 10 0 1 1 8 2.83" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><path d="M22 12A10 10 0 0 0 12 2v10z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></>,
    logic_validator: <path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.41 11.41A2 2 0 1 0 11 16H2m12-7.41A2 2 0 1 1 15.41 6H22M15.41 18A2 2 0 1 0 14 14H22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />,
    skill_agent: <><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><path d="M12 8l-4 8h8l-4-8z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></>,
    bias_agent: <path d="M3 6h18M7 12h10M10 18h4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />,
    transparency_agent: <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></>,
    match_agent: <><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><line x1="12" y1="8" x2="12" y2="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><line x1="8" y1="12" x2="16" y2="12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></>,
    passport_agent: <><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><circle cx="12" cy="7" r="4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></>,
    output: <><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><polyline points="16 6 12 2 8 6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><line x1="12" y1="2" x2="12" y2="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></>
};

const DATA = {
    columns: [
        {
            id: 'inputs',
            title: 'INPUT SOURCES',
            nodes: [
                { id: 'resume', label: 'Resume Data', icon: 'resume', description: 'Raw experience data extracted and normalized.' },
                { id: 'github', label: 'Repo Signals', icon: 'github', description: 'Technical signatures and code impact analysis.' },
                { id: 'coding', label: 'Coding Perf', icon: 'coding', description: 'Ranking and competitive signal processing.' },
                { id: 'tests', label: 'Tech Tests', icon: 'tests', description: 'Direct logic and problem-solving assessment signals.' },
                { id: 'metadata', label: 'Activity Metadata', icon: 'metadata', description: 'Subtle interaction signals for behavioral consistency.' },
            ]
        },
        {
            id: 'processing',
            title: 'AI PROCESSING',
            nodes: [
                { id: 'parser', label: 'Data Parser', icon: 'parser', description: 'Structural normalization of unstructured inputs.' },
                { id: 'analyzer', label: 'Skill Analysis', icon: 'analyzer', description: 'Deep technical reasoning and signal extraction.' },
                { id: 'evaluator', label: 'Test Evaluator', icon: 'evaluator', description: 'Performance benchmarking against role depth.' },
                { id: 'logic_validator', label: 'Logic Validation', icon: 'logic_validator', description: 'Verifies reasoning patterns and solved logic blocks.' },
            ]
        },
        {
            id: 'actions',
            title: 'ACTION LAYER',
            nodes: [
                { id: 'skill_agent', label: 'Verification', icon: 'skill_agent', description: 'Validates architectural judgment and depth.' },
                { id: 'bias_agent', label: 'Bias Audit', icon: 'bias_agent', description: 'Audits distributions for systemic equity.' },
                { id: 'transparency_agent', label: 'Transparency', icon: 'transparency_agent', description: 'Ensures reasoning behind decisions is logged and traceable.' },
                { id: 'match_agent', label: 'Matching Agent', icon: 'match_agent', description: 'Calculates precise role-candidate alignment.' },
                { id: 'passport_agent', label: 'Passport Agent', icon: 'passport_agent', description: 'Issues verifiable on-chain credentials.' },
            ]
        },
        {
            id: 'outputs',
            title: 'OUTPUT',
            nodes: [
                { id: 'skill_conf', label: 'Skill Confidence', icon: 'output', description: 'Verified depth for each technical domain.' },
                { id: 'credential', label: 'Skill Passport', icon: 'passport_agent', description: 'Secure on-chain record of validated skills.' },
                { id: 'feedback', label: 'Growth Insights', icon: 'output', description: 'Personalized developmental feedback for candidates.' },
                { id: 'anon_view', label: 'Anonymous View', icon: 'transparency_agent', description: 'Pre-screening profile with identity masking.' },
                { id: 'ranking', label: 'Equitable Ranking', icon: 'bias_agent', description: 'Equitable placement in the talent pipeline.' },
            ]
        }
    ],
    connections: [
        // Input -> Processing
        { from: 'resume', to: 'parser' },
        { from: 'github', to: 'analyzer' },
        { from: 'coding', to: 'parser' },
        { from: 'tests', to: 'evaluator' },
        { from: 'metadata', to: 'logic_validator' },

        // Processing -> Action Layer (Verification backbone)
        { from: 'parser', to: 'skill_agent' },
        { from: 'analyzer', to: 'skill_agent' },
        { from: 'evaluator', to: 'skill_agent' },
        { from: 'logic_validator', to: 'skill_agent' },

        // Action Layer (Sequential Pipeline)
        { from: 'skill_agent', to: 'bias_agent' },
        { from: 'bias_agent', to: 'transparency_agent' },
        { from: 'transparency_agent', to: 'match_agent' },
        { from: 'match_agent', to: 'passport_agent' },

        // Action Layer -> Output
        { from: 'match_agent', to: 'skill_conf' },
        { from: 'passport_agent', to: 'credential' },
        { from: 'transparency_agent', to: 'feedback' },
        { from: 'bias_agent', to: 'anon_view' },
        { from: 'match_agent', to: 'ranking' },
    ]
};

const ConnectionNode = ({ start, end, isActive }) => {
    if (!start || !end) return null;

    const dx = end.x - start.x;
    const dy = end.y - start.y;

    // Check if the connection is perfectly vertical (intra-column)
    const isVertical = Math.abs(dx) < 2;

    const controlPointOffset = Math.min(Math.abs(dx) * 0.5, 100);
    const path = isVertical
        ? `M ${start.x} ${start.y} L ${end.x} ${end.y}`
        : `M ${start.x} ${start.y} C ${start.x + controlPointOffset} ${start.y}, ${end.x - controlPointOffset} ${end.y}, ${end.x} ${end.y}`;

    return (
        <g>
            <path
                pathLength="1"
                d={path}
                fill="none"
                stroke="rgba(255, 255, 255, 0.15)"
                strokeWidth="2"
            />
            {isActive && (
                <>
                    <motion.path
                        d={path}
                        fill="none"
                        stroke="rgba(255, 255, 255, 0.4)"
                        strokeWidth="2"
                        initial={{ pathLength: 0, opacity: 0 }}
                        animate={{ pathLength: 1, opacity: 1 }}
                        transition={{ duration: 1.5, ease: "easeInOut" }}
                    />
                    {[0, 1].map((i) => (
                        <motion.circle key={i} r="2" fill="#FFFFFF" filter="blur(1px)">
                            <animateMotion
                                dur={`${2 + i * 0.8}s`}
                                repeatCount="indefinite"
                                path={path}
                                begin={`${i * 1}s`}
                            />
                        </motion.circle>
                    ))}
                    <motion.circle r="3" fill="#FFFFFF" className="drop-shadow-[0_0_8px_white]">
                        <animateMotion
                            dur="3s"
                            repeatCount="indefinite"
                            path={path}
                        />
                    </motion.circle>
                </>
            )}
        </g>
    );
};

export default function SystemFlow() {
    const navigate = useNavigate();
    const [activeStep, setActiveStep] = useState(0);
    const [hoveredNode, setHoveredNode] = useState(null);
    const containerRef = useRef(null);
    const nodeRefs = useRef({});
    const [coords, setCoords] = useState({});

    useEffect(() => {
        const updateCoords = () => {
            const container = containerRef.current;
            if (!container) return;
            const containerRect = container.getBoundingClientRect();

            // Calculate current visual scale relative to untransformed state
            // offsetWidth gives untransformed width, getBoundingClientRect gives transformed
            const scaleX = containerRect.width / container.offsetWidth;
            const scaleY = containerRect.height / container.offsetHeight;

            const newCoords = {};
            Object.entries(nodeRefs.current).forEach(([id, element]) => {
                if (element) {
                    const rect = element.getBoundingClientRect();
                    // Divide viewport pixels by visual scale to map back to SVG coordinate space
                    const centerX = (rect.left + rect.width / 2 - containerRect.left) / scaleX;
                    const centerY = (rect.top + rect.height / 2 - containerRect.top) / scaleY;
                    const radius = (rect.width / 2) / scaleX;

                    newCoords[id] = { x: centerX, y: centerY };
                    newCoords[`${id}_right`] = { x: centerX + radius, y: centerY };
                    newCoords[`${id}_left`] = { x: centerX - radius, y: centerY };
                    newCoords[`${id}_top`] = { x: centerX, y: centerY - radius };
                    newCoords[`${id}_bottom`] = { x: centerX, y: centerY + radius };
                }
            });
            setCoords(newCoords);
        };

        updateCoords();
        const timer = setTimeout(updateCoords, 800); // Wait for animations to settle
        window.addEventListener('resize', updateCoords);
        return () => {
            window.removeEventListener('resize', updateCoords);
            clearTimeout(timer);
        };
    }, []);

    const getPort = (nodeId, side) => {
        return coords[`${nodeId}_${side}`] || coords[nodeId];
    };

    const getConnectionPorts = (fromId, toId) => {
        let fromColIdx = -1;
        let toColIdx = -1;
        DATA.columns.forEach((col, idx) => {
            if (col.nodes.find(n => n.id === fromId)) fromColIdx = idx;
            if (col.nodes.find(n => n.id === toId)) toColIdx = idx;
        });

        // Vertical connection (inside same column)
        if (fromColIdx === toColIdx) {
            return { start: getPort(fromId, 'bottom'), end: getPort(toId, 'top') };
        }

        // Horizontal connection (between columns)
        if (fromColIdx < toColIdx) {
            return { start: getPort(fromId, 'right'), end: getPort(toId, 'left') };
        }

        return { start: coords[fromId], end: coords[toId] };
    };

    useEffect(() => {
        const interval = setInterval(() => {
            setActiveStep((prev) => (prev + 1) % 5);
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    const hoveredNodeData = useMemo(() => {
        if (!hoveredNode) return null;
        for (const col of DATA.columns) {
            const node = col.nodes.find(n => n.id === hoveredNode);
            if (node) return node;
        }
        return null;
    }, [hoveredNode]);

    return (
        <div className="h-screen bg-[#0a0a0a] text-white flex flex-col relative overflow-hidden selection:bg-white selection:text-black font-montreal">
            <header className="sticky top-0 left-0 w-full border-b border-white/20 z-[100] px-6 md:px-12 py-3 flex justify-between items-center bg-black/90 backdrop-blur-xl">
                <div className="flex items-center gap-6">
                    <button
                        onClick={() => navigate('/')}
                        className="px-6 py-2 border border-white/60 font-grotesk text-[10px] font-black uppercase tracking-[0.2em] hover:bg-white hover:text-black transition-all flex items-center gap-2 text-white"
                    >
                        ← EXIT SYSTEM
                    </button>
                    <div className="h-6 w-[1px] bg-white/30"></div>
                    <span className="font-montreal font-black text-sm tracking-[0.3em] uppercase text-white">
                        Agent Orchestration Pipeline
                    </span>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 bg-white/15 px-4 py-1.5 rounded-full border border-white/20">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-400 shadow-[0_0_12px_#4ade80] animate-pulse"></div>
                        <span className="font-grotesk text-[9px] font-black uppercase tracking-widest text-white shadow-sm">Agent Status: Active</span>
                    </div>
                </div>
            </header>

            <main className="flex-1 overflow-hidden flex flex-col items-center justify-center p-2 relative">
                <div ref={containerRef} className="w-full h-full max-w-[1500px] flex items-stretch justify-between px-2 md:px-6 py-6 relative scale-[0.75] lg:scale-[0.85] xl:scale-95 origin-center transition-transform duration-500">
                    <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
                        <defs>
                            <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
                                <feGaussianBlur stdDeviation="6" result="coloredBlur" />
                                <feMerge>
                                    <feMergeNode in="coloredBlur" />
                                    <feMergeNode in="SourceGraphic" />
                                </feMerge>
                            </filter>
                        </defs>
                        {DATA.connections.map((conn, idx) => {
                            const ports = getConnectionPorts(conn.from, conn.to);
                            if (!ports.start || !ports.end) return null;
                            return (
                                <ConnectionNode
                                    key={idx}
                                    start={ports.start}
                                    end={ports.end}
                                    isActive={true}
                                />
                            );
                        })}
                    </svg>

                    {DATA.columns.map((col, colIdx) => (
                        <div key={col.id} className="relative flex-1 flex flex-col items-center px-1">
                            <div className="absolute -inset-y-8 inset-x-0.5 border-2 border-dashed border-white/50 rounded-[2.5rem] bg-white/[0.05] -z-10 pointer-events-none" />

                            <h2 className="font-grotesk text-[10px] md:text-[14px] font-black uppercase tracking-[0.4em] mb-2 mt-6 text-white">
                                {col.title}
                            </h2>

                            <div className="flex flex-col items-center justify-center gap-4 lg:gap-8 flex-1 w-full py-1">
                                {col.nodes.map(node => (
                                    <div
                                        key={node.id}
                                        className="flex flex-col items-center gap-1 relative w-full"
                                        onMouseEnter={() => setHoveredNode(node.id)}
                                        onMouseLeave={() => setHoveredNode(null)}
                                    >
                                        <div
                                            ref={el => nodeRefs.current[node.id] = el}
                                            className={`
                                                w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center transition-all duration-500 relative cursor-pointer
                                                ${hoveredNode === node.id ? 'bg-white text-black scale-110 shadow-[0_0_50px_rgba(255,255,255,1)]' : 'bg-[#1c1c1c] text-white border-2 border-white/60 hover:border-white hover:bg-[#252525] shadow-[0_0_15px_rgba(255,255,255,0.2)]'}
                                            `}
                                        >
                                            <svg width="24" height="24" viewBox="0 0 24 24" className="w-5 h-5 md:w-6 md:h-6" filter={hoveredNode === node.id ? 'none' : 'url(#glow)'}>
                                                {ICONS[node.icon] || ICONS.output}
                                            </svg>

                                            {activeStep === colIdx && (
                                                <motion.div
                                                    initial={{ scale: 0.8, opacity: 0 }}
                                                    animate={{ scale: 1.8, opacity: 0 }}
                                                    transition={{ repeat: Infinity, duration: 2 }}
                                                    className="absolute inset-0 rounded-full border-2 border-white/80 pointer-events-none"
                                                />
                                            )}
                                        </div>
                                        <span className={`
                                            font-montreal font-black text-[7px] md:text-[10px] uppercase tracking-wider text-center max-w-[80px] transition-all duration-300 text-white
                                            ${hoveredNode === node.id ? 'opacity-100 translate-y-0.5' : 'opacity-90'}
                                        `}>
                                            {node.label}
                                        </span>

                                        <AnimatePresence>
                                            {hoveredNode === node.id && (
                                                <motion.div
                                                    initial={{ opacity: 0, scale: 0.9, y: 10 }}
                                                    animate={{ opacity: 1, scale: 1, y: 0 }}
                                                    exit={{ opacity: 0, scale: 0.9, y: 10 }}
                                                    className="absolute -top-28 left-1/2 -translate-x-1/2 w-52 p-4 bg-white text-black rounded-2xl text-center shadow-[0_30px_60px_rgba(255,255,255,0.2)] z-[200]"
                                                >
                                                    <div className="font-grotesk text-[8px] font-black uppercase tracking-widest opacity-40 mb-1">Agent Detail</div>
                                                    <p className="font-inter text-[11px] font-bold leading-tight uppercase">{node.description}</p>
                                                    <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-white rotate-45" />
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </main>

            <div className="fixed inset-0 pointer-events-none opacity-[0.03] bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] z-0" />

            <style>{`
                @font-face {
                    font-family: 'Montreal';
                    src: url('https://fonts.cdnfonts.com/s/73916/PPNeueMontreal-Bold.woff');
                }
                @font-face {
                    font-family: 'Grotesk';
                    src: url('https://fonts.cdnfonts.com/s/73916/PPNeueMontreal-Book.woff');
                }
            `}</style>
        </div>
    );
}
