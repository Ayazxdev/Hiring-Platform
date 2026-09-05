import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { InterviewStatus } from './types';
import { InterviewSetup } from './InterviewSetup';
import { InterviewSession } from './InterviewSession';
import { AnalysisReport } from './AnalysisReport';
import { generateEvaluation } from './analysisService';
import { Icons } from './constants';

const INITIAL_STATS = {
    totalSessions: 0,
    currentStreak: 0,
    lastSessionDate: null,
    scoreHistory: [],
    averageScore: 0
};

const FairHiringInterview = ({ onExit }) => {
    const navigate = useNavigate();
    const [state, setState] = useState({
        status: InterviewStatus.IDLE,
        config: null,
        analysis: null,
        history: [],
        stats: INITIAL_STATS
    });

    const [loading, setLoading] = useState(false);
    const [hasKey, setHasKey] = useState(true);
    const [customKey, setCustomKey] = useState('');
    const [showKeyModal, setShowKeyModal] = useState(false);

    const checkKeyStatus = () => {
        const apiKey =
            import.meta.env.VITE_GEMINI_API_KEY ||
            import.meta.env.GEMINI_API_KEY ||
            import.meta.env.VITE_API_KEY ||
            localStorage.getItem('fhn_gemini_api_key');
        setHasKey(!!apiKey);
        if (localStorage.getItem('fhn_gemini_api_key')) {
            setCustomKey(localStorage.getItem('fhn_gemini_api_key'));
        }
    };

    // Load stats and verify API key on mount
    useEffect(() => {
        const savedStats = localStorage.getItem('fair_hiring_interview_stats');
        if (savedStats) {
            try {
                setState(prev => ({ ...prev, stats: JSON.parse(savedStats) }));
            } catch (e) {
                console.error("Failed to parse saved stats", e);
            }
        }

        checkKeyStatus();
    }, []);

    const handleSaveKey = (e) => {
        if (e) e.preventDefault();
        if (customKey.trim()) {
            localStorage.setItem('fhn_gemini_api_key', customKey.trim());
            setHasKey(true);
            setShowKeyModal(false);
        }
    };

    const updateStats = (newScore) => {
        const now = new Date();
        const today = now.toISOString().split('T')[0];

        setState(prev => {
            const oldStats = prev.stats;
            const lastDate = oldStats.lastSessionDate;

            let newStreak = oldStats.currentStreak;

            if (!lastDate) {
                newStreak = 1;
            } else {
                const lastDateObj = new Date(lastDate);
                const diffTime = Math.abs(now.getTime() - lastDateObj.getTime());
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

                if (diffDays === 1) {
                    newStreak += 1;
                } else if (diffDays > 1) {
                    newStreak = 1;
                }
            }

            const newHistory = [...oldStats.scoreHistory, newScore];
            const newAverage = Math.round(newHistory.reduce((a, b) => a + b, 0) / newHistory.length);

            const updatedStats = {
                totalSessions: oldStats.totalSessions + 1,
                currentStreak: newStreak,
                lastSessionDate: today,
                scoreHistory: newHistory,
                averageScore: newAverage
            };

            localStorage.setItem('fair_hiring_interview_stats', JSON.stringify(updatedStats));
            return { ...prev, stats: updatedStats };
        });
    };

    const handleStartInterview = (config) => {
        setState(prev => ({ ...prev, config, status: InterviewStatus.INTERVIEWING }));
    };

    const handleInterviewComplete = async (history, duration) => {
        if (!state.config) return;

        setLoading(true);
        try {
            const evaluation = await generateEvaluation(state.config, history);
            evaluation.duration = duration;
            updateStats(evaluation.overallScore);
            setState(prev => ({
                ...prev,
                history,
                analysis: evaluation,
                status: InterviewStatus.COMPLETED
            }));
        } catch (err) {
            console.error('Evaluation failed:', err);
            alert(`API Error: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const isStandalone = import.meta.env.VITE_STANDALONE_PROTOCOL === 'true';

    const handleExit = () => {
        if (onExit && !isStandalone) {
            onExit();
        } else if (!isStandalone) {
            navigate('/candidate');
        } else {
            // In standalone, just return to IDLE
            setState(prev => ({ ...prev, status: InterviewStatus.IDLE, analysis: null, config: null }));
        }
    };

    const handleBack = () => {
        if (state.status === InterviewStatus.SETUP) {
            setState(prev => ({ ...prev, status: InterviewStatus.IDLE }));
        } else if (state.status === InterviewStatus.INTERVIEWING) {
            if (confirm("Are you sure you want to leave the interview? Progress will be lost.")) {
                setState(prev => ({ ...prev, status: InterviewStatus.SETUP }));
            }
        } else if (state.status === InterviewStatus.COMPLETED) {
            setState(prev => ({ ...prev, status: InterviewStatus.IDLE, analysis: null, config: null }));
        } else {
            handleExit();
        }
    };

    const renderContent = () => {
        if (loading) {
            return (
                <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-12">
                    <div className="relative">
                        <div className="w-40 h-40 border-[3px] border-[#1c1c1c]/10 border-t-[#1c1c1c] rounded-full animate-spin" />
                        <div className="absolute inset-0 flex items-center justify-center">
                            <Icons.Sparkles className="w-12 h-12 text-[#1c1c1c] animate-pulse" />
                        </div>
                    </div>
                    <div className="space-y-4">
                        <h2 className="text-5xl font-black text-[#1c1c1c] tracking-tighter uppercase font-montreal">Analyzing Performance</h2>
                        <p className="text-sm font-black tracking-widest uppercase opacity-50 font-grotesk">Synthesizing behavioral intelligence feed...</p>
                    </div>
                </div>
            );
        }

        switch (state.status) {
            case InterviewStatus.IDLE:
                const improvement = state.stats.scoreHistory.length > 1
                    ? state.stats.scoreHistory[state.stats.scoreHistory.length - 1] - state.stats.scoreHistory[0]
                    : 0;

                return (
                    <div className="flex flex-col max-w-[1440px] mx-auto py-2 min-h-[60vh] justify-start text-center">
                        <div className="space-y-4 md:space-y-6">
                            {/* Badges */}
                            <div className="flex justify-center gap-4">
                                <div className="inline-flex items-center gap-3 px-3.5 py-1 border-[2px] border-[#1c1c1c] text-[#1c1c1c] text-[9px] font-black tracking-[0.25em] uppercase">
                                    <Icons.Sparkles className="w-3 h-3" />
                                    AI_INTELLIGENCE_CORE
                                </div>
                                {state.stats.totalSessions > 0 && (
                                    <div className="inline-flex items-center gap-2.5 px-3.5 py-1 bg-[#1c1c1c] text-white text-[9px] font-black tracking-[0.25em] uppercase">
                                        <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                                        {state.stats.currentStreak}D CONSISTENCY
                                    </div>
                                )}
                            </div>

                            {/* Main Title */}
                            <div className="space-y-1">
                                <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tighter text-[#1c1c1c] leading-[0.88] font-montreal uppercase block w-full">
                                    FAIR HIRING
                                </h1>
                                <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black tracking-tighter text-[#1c1c1c] leading-[0.88] font-montreal uppercase block w-full opacity-70">
                                    INTERVIEW
                                </h1>
                            </div>

                            {/* Description & Action */}
                            <div className="max-w-2xl mx-auto space-y-4">
                                <p className="text-xs md:text-sm text-[#1c1c1c]/60 font-black font-grotesk leading-normal uppercase tracking-widest">
                                    Multimodal interview simulation. Master your delivery through real-time expression analysis and adaptive agent inquiry.
                                </p>

                                <div className="pt-1 flex flex-col items-center gap-3">
                                    <div className="flex items-center justify-center">
                                        {hasKey ? (
                                            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-white border-2 border-black text-[#1c1c1c] font-grotesk text-[9px] font-black tracking-widest uppercase shadow-[2px_2px_0px_#000]">
                                                <span className="w-2 h-2 rounded-full bg-[#A7FF2E] inline-block animate-pulse" />
                                                <span>GEMINI ENGINE READY</span>
                                                <button
                                                    onClick={() => setShowKeyModal(true)}
                                                    className="ml-2 px-1.5 py-0.5 border border-black/20 text-[8px] hover:bg-black hover:text-white transition-all uppercase"
                                                >
                                                    SETTINGS
                                                </button>
                                            </div>
                                        ) : (
                                            <div className="flex flex-col sm:flex-row items-center gap-2 p-3 bg-white border-2 border-black shadow-[3px_3px_0px_#000]">
                                                <input
                                                    type="password"
                                                    placeholder="Paste Gemini API Key (AIzaSy...)"
                                                    value={customKey}
                                                    onChange={(e) => setCustomKey(e.target.value)}
                                                    className="px-3 py-1.5 border-2 border-black font-mono text-xs w-64 focus:outline-none"
                                                />
                                                <button
                                                    onClick={handleSaveKey}
                                                    className="px-4 py-1.5 bg-[#A7FF2E] text-black font-grotesk font-black text-[9px] tracking-widest uppercase border-2 border-black hover:bg-black hover:text-[#A7FF2E] transition-all shadow-[2px_2px_0px_#000]"
                                                >
                                                    SAVE KEY
                                                </button>
                                            </div>
                                        )}
                                    </div>

                                    <button
                                        onClick={() => setState(prev => ({ ...prev, status: InterviewStatus.SETUP }))}
                                        className="px-12 py-4 bg-black text-white border-[3px] border-black font-grotesk font-black text-base tracking-[0.25em] uppercase transition-all shadow-[5px_5px_0px_#ccc] hover:bg-white hover:text-black hover:-translate-y-0.5 hover:shadow-[8px_8px_0px_#bbb] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
                                    >
                                        {state.stats.totalSessions > 0 ? 'RESUME_TRAINING' : 'START_SIMULATION'}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Features Minimal Horizontal Bar */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 py-12 border-t-[3px] border-[#1c1c1c]/10 mt-12">
                            {[
                                { label: 'BEHAVIORAL SYNC', icon: <Icons.Sparkles className="w-8 h-8" />, text: 'Visual and auditory performance analysis.' },
                                { label: 'ADAPTIVE AGENT', icon: <Icons.Microphone className="w-8 h-8" />, text: 'Dynamic context-aware questioning.' },
                                { label: 'SKILL MAPPING', icon: <Icons.ChartBar className="w-8 h-8" />, text: 'Detailed intelligence breakdown.' },
                            ].map((f, i) => (
                                <div key={i} className="flex flex-col items-center gap-6">
                                    <div className="w-20 h-20 border-[3px] border-[#1c1c1c] flex items-center justify-center text-[#1c1c1c] shrink-0 shadow-[6px_6px_0px_#ccc]">
                                        {f.icon}
                                    </div>
                                    <div className="space-y-3">
                                        <h3 className="font-montreal font-black text-xs md:text-sm uppercase tracking-[0.4em] leading-none text-[#1c1c1c]">{f.label}</h3>
                                        <p className="text-[#1c1c1c]/70 text-[10px] md:text-[11px] font-black uppercase tracking-[0.15em] font-grotesk max-w-[200px] mx-auto leading-relaxed">{f.text}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                );
            case InterviewStatus.SETUP:
                return <InterviewSetup onStart={handleStartInterview} />;
            case InterviewStatus.INTERVIEWING:
                return state.config ? (
                    <InterviewSession config={state.config} onComplete={handleInterviewComplete} />
                ) : null;
            case InterviewStatus.COMPLETED:
                return state.analysis ? (
                    <AnalysisReport
                        analysis={state.analysis}
                        config={state.config}
                        onReset={() => setState(prev => ({ ...prev, status: InterviewStatus.IDLE, analysis: null, config: null }))}
                    />
                ) : null;
            default:
                return null;
        }
    };

    return (
        <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
            className="fixed inset-0 z-[150] bg-[#E6E6E3] text-[#1c1c1c] overflow-y-auto selection:bg-black selection:text-white"
            style={{ willChange: 'transform' }}
            data-lenis-prevent
        >
            {/* STICKY HEADER */}
            <header className="sticky top-0 left-0 w-full bg-[#E6E6E3] border-b-[3px] border-[#1c1c1c] z-50 px-6 md:px-12 py-6 flex justify-between items-center bg-opacity-95 backdrop-blur-sm">
                <div className="flex items-center gap-6">
                    {state.status !== InterviewStatus.COMPLETED && (
                        <button
                            onClick={handleBack}
                            className="px-6 py-3 border-[2px] border-[#1c1c1c] font-grotesk text-[11px] font-black uppercase tracking-[0.2em] hover:bg-[#1c1c1c] hover:text-[#E6E6E3] transition-all flex items-center gap-2 group"
                        >
                            <span className="group-hover:-translate-x-1 transition-transform inline-block">←</span> BACK
                        </button>
                    )}
                    {state.status !== InterviewStatus.COMPLETED && <div className="h-10 w-[2px] bg-[#1c1c1c]/10 hidden md:block"></div>}
                    <span
                        className="font-montreal font-black text-sm md:text-base tracking-[0.2em] uppercase text-[#1c1c1c] cursor-pointer"
                        onClick={() => setState(prev => ({ ...prev, status: InterviewStatus.IDLE, analysis: null, config: null }))}
                    >
                        FAIR HIRING INTERVIEW
                    </span>
                </div>
                <div className="font-grotesk text-[11px] font-black tracking-[0.1em] uppercase opacity-100 text-[#1c1c1c]">
                    SESSION_V1
                </div>
            </header>

            <main className="max-w-[1280px] mx-auto px-6 md:px-12 py-6 md:py-8 min-h-[80vh]">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={state.status + (loading ? '_loading' : '')}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
                    >
                        {renderContent()}
                    </motion.div>
                </AnimatePresence>
            </main>

            <footer className="max-w-[1280px] mx-auto px-6 md:px-12 py-12 border-t border-[#1c1c1c]/10 text-center">
                <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                    <p className="font-grotesk text-[10px] font-black tracking-[0.3em] uppercase opacity-50">
                        © 2026 FAIR HIRING NETWORK
                    </p>
                    <div className="flex items-center gap-8 font-grotesk text-[10px] font-black tracking-[0.3em] uppercase">
                        <div className="flex items-center gap-2">
                            <span className="opacity-40">CURRENT CONSISTENCY</span>
                            <span className="text-[#1c1c1c]">{state.stats.currentStreak} DAYS</span>
                        </div>
                        <div className="h-4 w-[2px] bg-[#1c1c1c]/10" />
                        <div className="flex items-center gap-2">
                            <span className="opacity-40">SYSTEM STATUS</span>
                            <span className="text-green-600">ACTIVE</span>
                        </div>
                    </div>
                </div>
            </footer>

            {/* API KEY CONFIG MODAL */}
            {showKeyModal && (
                <div
                    className="fixed inset-0 z-[200] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
                    onClick={() => setShowKeyModal(false)}
                >
                    <div
                        className="bg-white border-4 border-black p-8 max-w-md w-full shadow-[8px_8px_0px_#000] space-y-6"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex justify-between items-start border-b-2 border-black pb-4">
                            <div>
                                <span className="px-2.5 py-1 bg-[#A7FF2E] text-black font-grotesk text-[9px] font-black uppercase tracking-wider">
                                    ENGINE CONFIG
                                </span>
                                <h3 className="font-montreal font-black text-2xl uppercase tracking-tight mt-2">
                                    Gemini API Key
                                </h3>
                            </div>
                            <button
                                onClick={() => setShowKeyModal(false)}
                                className="text-xl font-bold hover:opacity-50"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="space-y-4 font-mono text-xs">
                            <p className="font-inter text-xs text-black/70 font-medium">
                                Configure your Google Gemini Live API key for multimodal audio and visual analysis.
                            </p>
                            <input
                                type="password"
                                placeholder="Paste Gemini API Key (e.g. AIzaSy...)"
                                value={customKey}
                                onChange={(e) => setCustomKey(e.target.value)}
                                className="w-full px-4 py-3 border-2 border-black font-mono text-xs focus:outline-none"
                            />
                        </div>

                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={handleSaveKey}
                                className="flex-1 py-3 bg-[#A7FF2E] text-black border-2 border-black font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-black hover:text-[#A7FF2E] transition-all shadow-[3px_3px_0px_#000]"
                            >
                                SAVE KEY ✓
                            </button>
                            {localStorage.getItem('fhn_gemini_api_key') && (
                                <button
                                    onClick={() => {
                                        localStorage.removeItem('fhn_gemini_api_key');
                                        setCustomKey('');
                                        checkKeyStatus();
                                        setShowKeyModal(false);
                                    }}
                                    className="py-3 px-4 bg-transparent text-red-600 border-2 border-red-600 font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-red-600 hover:text-white transition-all"
                                >
                                    CLEAR
                                </button>
                            )}
                            <button
                                onClick={() => setShowKeyModal(false)}
                                className="py-3 px-4 border-2 border-black font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-black hover:text-white transition-all"
                            >
                                CANCEL
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <style>{`
                .no-scrollbar::-webkit-scrollbar { display: none; }
                .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
            `}</style>
        </motion.div>
    );
};

export default FairHiringInterview;
