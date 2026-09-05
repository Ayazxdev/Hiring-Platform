import { useState } from 'react';
import { motion } from 'framer-motion';
import GridPlus from './GridPlus';

export default function CompanyCandidateReview({ candidate, onBack, onAction }) {
    if (!candidate) return null;

    // Safe derivation from candidate prop
    const details = {
        ...candidate,
        skills: candidate.skills || candidate.verified_skills?.slice(0, 5) || [],
        insights: candidate.insights || [
            { label: 'Evaluation', value: candidate.status || 'Pending' },
            { label: 'Score', value: `${candidate.confidence || 0}%` }
        ],
        agentNotes: candidate.agent_notes || candidate.feedback || "No automated notes available for this candidate.",
        biasStatus: candidate.bias_status || "Standard bias checks passed.",
        reviewTrigger: candidate.review_trigger || (candidate.confidence < 70 ? "Low confidence score detected." : null)
    };

    return (
        <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
            className="fixed inset-0 z-[170] bg-[#E6E6E3] text-[#1c1c1c] overflow-y-auto flex flex-col"
            style={{ willChange: 'transform' }}
            data-lenis-prevent
        >
            {/* STICKY HEADER */}
            <header className="sticky top-0 left-0 w-full bg-[#E6E6E3] border-b-[3px] border-[#1c1c1c] z-50 px-6 md:px-12 py-6 flex justify-between items-center bg-opacity-95 backdrop-blur-sm flex-shrink-0">
                <div className="flex items-center gap-6">
                    <button
                        onClick={onBack}
                        className="px-6 py-3 border-[2px] border-[#1c1c1c] font-grotesk text-[11px] font-black uppercase tracking-[0.2em] hover:bg-[#1c1c1c] hover:text-[#E6E6E3] transition-all flex items-center gap-2 group"
                    >
                        <span className="group-hover:-translate-x-1 transition-transform inline-block">←</span> BACK TO PIPELINE
                    </button>
                    <div className="h-10 w-[2px] bg-[#1c1c1c]/10 hidden md:block"></div>
                    <span className="font-montreal font-black text-sm md:text-base tracking-[0.2em] uppercase text-[#1c1c1c]">
                        CANDIDATE REVIEW
                    </span>
                </div>
                <div className="font-mono text-[11px] font-black opacity-100 uppercase tracking-widest">
                    ID: {candidate.id}
                </div>
            </header>

            <main className="flex-1 overflow-y-auto custom-scrollbar-light">
                <div className="max-w-[1440px] mx-auto grid grid-cols-1 lg:grid-cols-12 min-h-0">

                    {/* LEFT: CANDIDATE SUMMARY */}
                    <div className="lg:col-span-5 border-r border-[#1c1c1c]/5 p-6 md:p-12 space-y-16">
                        <div className="space-y-6">
                            <label className="font-grotesk text-[10px] uppercase opacity-100 font-extrabold tracking-widest text-[#1c1c1c]">CANDIDATE ID</label>
                            <h1 className="font-montreal font-black text-6xl md:text-8xl uppercase tracking-tighter leading-none opacity-100 text-[#1c1c1c]">
                                {candidate.id}
                            </h1>
                        </div>

                        <div className="space-y-8">
                            <label className="font-grotesk text-[11px] uppercase font-black tracking-widest text-[#1c1c1c]">VERIFIED SKILLSET</label>
                            <div className="flex flex-wrap gap-3">
                                {details.skills.map(skill => (
                                    <span key={skill} className="px-5 py-2.5 bg-[#1c1c1c] text-white rounded-sm font-grotesk text-[10px] font-black uppercase tracking-widest">
                                        {skill}
                                    </span>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-8">
                            <label className="font-grotesk text-[10px] uppercase opacity-80 font-bold tracking-widest">SKILL CONFIDENCE</label>
                            <div className="flex items-end gap-4">
                                <span className="font-montreal font-bold text-6xl leading-none">{details.confidence}%</span>
                                <span className="font-inter text-xs opacity-40 mb-2">Agent Confidence Score</span>
                            </div>
                            <div className="w-full h-1 bg-[#1c1c1c]/10 mt-4">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${details.confidence}%` }}
                                    transition={{ duration: 1, delay: 0.3 }}
                                    className="h-full bg-[#1c1c1c]"
                                />
                            </div>
                        </div>
                    </div>

                    {/* RIGHT: AGENT INSIGHTS */}
                    <div className="lg:col-span-7 p-6 md:p-12 space-y-16 bg-[#F2F2EE]/50">
                        <div className="space-y-8">
                            <label className="font-grotesk text-[10px] uppercase font-black tracking-widest text-[#1c1c1c]">AGENT ANALYSIS</label>
                            <p className="font-inter text-xl font-bold leading-relaxed text-[#1c1c1c] max-w-2xl">
                                {details.agentNotes}
                            </p>
                        </div>

                        <div className="space-y-8">
                            <label className="font-grotesk text-[10px] uppercase font-black tracking-widest text-[#1c1c1c]">BIAS CHECK STATUS</label>
                            <div className="p-6 border-[2px] border-[#1c1c1c] bg-white flex items-start gap-4">
                                <div className="w-2.5 h-2.5 rounded-full bg-green-600 mt-1.5 flex-shrink-0"></div>
                                <div className="space-y-2">
                                    <div className="font-montreal font-black uppercase text-xl text-[#1c1c1c]">Verified Neutral</div>
                                    <p className="font-inter text-sm font-bold text-[#1c1c1c]/70 leading-relaxed">{details.biasStatus}</p>
                                </div>
                            </div>
                        </div>

                        {/* Integrity signal (Anti-cheat) */}
                        <div className="space-y-8">
                            <div className="flex justify-between items-baseline">
                                <label className="font-grotesk text-[10px] uppercase opacity-80 font-bold tracking-widest text-[#1c1c1c]">INTEGRITY SIGNAL</label>
                                <span className="font-grotesk text-[10px] uppercase opacity-40 font-bold tracking-widest text-right">Beta · Ethics First</span>
                            </div>

                            {/* Integrity Card */}
                            <div className="p-6 border border-[#1c1c1c]/10 bg-white/50 flex flex-col gap-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-3 h-3 rounded-full ${(details.integrity?.riskScore || 0) < 0.3 ? 'bg-green-500' :
                                            (details.integrity?.riskScore || 0) < 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                                            }`} />
                                        <div className="space-y-1">
                                            <div className="font-montreal font-bold uppercase text-lg">
                                                {(details.integrity?.riskScore || 0) < 0.3 ? 'Low Risk Confidence' :
                                                    (details.integrity?.riskScore || 0) < 0.7 ? 'Review Recommended' : 'High Anomaly Detected'}
                                            </div>
                                            <div className="font-inter text-xs opacity-60">
                                                Risk Score: {(details.integrity?.riskScore || 0).toFixed(2)} / 1.0
                                            </div>
                                        </div>
                                    </div>

                                    {/* Tooltip trigger (Visual only for now) */}
                                    <div className="group relative">
                                        <div className="w-6 h-6 rounded-full border border-black/20 flex items-center justify-center text-[10px] font-mono cursor-help">?</div>
                                        <div className="absolute right-0 top-8 w-64 p-4 bg-[#1c1c1c] text-[#E6E6E3] text-xs font-inter z-10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                                            This score includes confidence signals (time patterns, answer coherence), not a definitive judgment of cheating. Usage should be auditable.
                                        </div>
                                    </div>
                                </div>

                                {/* Active Signals List */}
                                {details.integrity?.signals?.length > 0 && (
                                    <div className="pt-4 border-t border-[#1c1c1c]/5 space-y-2">
                                        <label className="font-grotesk text-[9px] uppercase opacity-40 font-bold tracking-widest">DETECTED SIGNALS</label>
                                        {details.integrity.signals.map((sig, idx) => (
                                            <div key={idx} className="flex items-center gap-2 font-inter text-xs opacity-80">
                                                <span className="text-orange-600 font-bold">⚠</span>
                                                <span className="uppercase font-bold text-[10px]">{sig.type.replace('_', ' ')}:</span>
                                                <span>{sig.details}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {details.stage === 'human_review' && (
                            <div className="space-y-8 p-8 bg-orange-600/5 border-2 border-orange-600/20 rounded-sm">
                                <div className="flex items-center gap-3">
                                    <span className="text-xl">⚠</span>
                                    <label className="font-grotesk text-[11px] uppercase font-black tracking-[0.2em] text-orange-600">UNCERTAIN PARAMETER DETECTED</label>
                                </div>
                                <div className="space-y-4">
                                    <p className="font-inter text-base font-bold text-[#1c1c1c] leading-relaxed">
                                        System flagged an anomaly in skill evidence consistency. Human intervention required to validate authentic capability vs. pattern mismatch.
                                    </p>
                                    <div className="flex flex-col gap-2 p-4 bg-orange-600/10 border border-orange-600/10">
                                        <span className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-60 text-orange-800">STATED PROBLEM</span>
                                        <span className="font-inter text-xs font-black text-orange-950 uppercase italic">Atypical time-to-solution vs. complexity curve</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {details.reviewTrigger && details.stage !== 'human_review' && (
                            <div className="space-y-8">
                                <label className="font-grotesk text-[11px] uppercase font-black tracking-widest text-[#1c1c1c]">SYSTEM TRIGGER</label>
                                <p className="font-inter text-sm font-bold opacity-80 border-l-4 border-[#1c1c1c] pl-6 py-2 bg-white/40">
                                    {details.reviewTrigger}
                                </p>
                            </div>
                        )}

                        {/* ACTION AREA - Only show actions for specific columns if we had column context, but for now show generic flow actions */}
                        {/* ACTION AREA - RESTRICTED BY AGENT AUTHORITY */}
                        {/* ACTION AREA - RESTRICTED BY STAGE AUTHORITY */}
                        <div className="pt-16 border-t-[3px] border-[#1c1c1c] flex flex-col gap-8 w-full">
                            {/* CASE 1: EVALUATED CANDIDATES */}
                            {details.stage === 'evaluated' && (
                                <div className="space-y-6 w-full">
                                    <div className="flex flex-col gap-2">
                                        <span className="font-grotesk text-[10px] font-black uppercase tracking-[0.3em] text-green-700">✓ VERIFICATION COMPLETE</span>
                                        <h3 className="font-montreal font-black text-2xl uppercase text-[#1c1c1c]">Ready for Direct Engagement</h3>
                                    </div>
                                    <div className="flex flex-col sm:flex-row gap-4 w-full">
                                        <button
                                            onClick={() => onAction('reverify')}
                                            className="grow px-8 py-6 border-[2px] border-[#1c1c1c] text-[#1c1c1c] font-grotesk font-black text-xs tracking-[0.2em] uppercase hover:bg-[#1c1c1c] hover:text-[#E6E6E3] transition-all"
                                        >
                                            REQUEST RE-VALIDATION
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* CASE 2: HUMAN REVIEW PENDING - BLOCKED (REMOVED VISUAL BLOCK AS PER REQUEST) */}
                            {details.stage === 'human_review' && null}

                            {/* CASE 3: SYSTEM CONTROLLED */}
                            {(details.stage === 'applied' || details.stage === 'verified') && (
                                <div className="w-full p-8 bg-[#1c1c1c]/5 border-[2px] border-[#1c1c1c]/10 text-center">
                                    <span className="font-grotesk text-[10px] uppercase tracking-[0.3em] font-black text-[#1c1c1c]/40">
                                        SYSTEM-MANAGED STAGE
                                    </span>
                                    <div className="font-montreal font-black text-xl uppercase mt-2">
                                        Verification in Progress
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>

            <GridPlus className="fixed inset-0 pointer-events-none opacity-5 z-0" />
        </motion.div>
    );
}
