import { motion, AnimatePresence } from "framer-motion";

export default function JobDetailsModal({ isOpen, onClose, job }) {
    if (!job) return null;

    // v3 Intelligence Logic
    const rs = job.required_skills || {};
    const hasV3Data = rs.languages || rs.web_fundamentals || rs.backend_frameworks || rs.frameworks;

    // Categorized Skills (with aliases for different schema formats)
    const languages = rs.languages || [];
    const web_fundamentals = rs.web_fundamentals || [];
    const frontend_frameworks = rs.frontend_frameworks || [];
    const backend_frameworks = rs.backend_frameworks || rs.frameworks || [];
    const security = rs.security_concepts || [];
    const databases = rs.databases || [];
    const backend_concepts = rs.backend_concepts || rs.concepts || [];
    const infrastructure_concepts = rs.infrastructure_concepts || rs.infrastructure || [];
    const developer_tools = rs.developer_tools || rs.libraries_and_tools || [];

    // Requirements & Philosophy
    const strict = rs.strict_requirements || [];
    const soft = rs.soft_requirements || [];
    const exclusions = rs.excluded_signals || [];
    const philosophy = rs.matching_philosophy || {};

    // Evidence
    const problem_solving = rs.problem_solving || {};
    const evidence = rs.evaluation_signals || {};

    const findings = job.fairness_findings || [];

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[300] flex items-center justify-center p-6 md:p-12">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                    />
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0, y: 20 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.9, opacity: 0, y: 20 }}
                        className="relative w-full max-w-6xl bg-[#E6E6E3] border-4 border-black p-8 md:p-12 overflow-y-auto max-h-[90vh] shadow-[24px_24px_0px_rgba(0,0,0,0.2)]"
                    >
                        <div className="flex justify-between items-start mb-12">
                            <div className="space-y-4">
                                <div className="flex items-center gap-3">
                                    <span className={`inline-block px-4 py-1.5 font-grotesk font-black text-[10px] tracking-[0.2em] uppercase ${job.fairness_status === 'VERIFIED' ? 'bg-[#A7FF2E] text-black' : 'bg-[#FF4D4D] text-white'}`}>
                                        {job.fairness_status || 'AUDIT PENDING'}
                                    </span>
                                    {hasV3Data && (
                                        <span className="inline-block px-4 py-1.5 font-grotesk font-black text-[10px] tracking-[0.2em] uppercase bg-black text-white">
                                            INTEL v3 GOLD
                                        </span>
                                    )}
                                </div>
                                <div className="space-y-1">
                                    <h3 className="font-montreal font-black text-4xl uppercase tracking-tighter">{job.title}</h3>
                                    <p className="font-inter text-sm font-bold opacity-60 uppercase tracking-widest">
                                        ROLE SPECIFICATION • {rs.seniority || 'LEVEL UNKNOWN'} • {rs.seniority_flexibility ? 'FLEXIBLE DEPTH' : 'STRICT LEVEL'}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={onClose}
                                className="flex-shrink-0 whitespace-nowrap font-grotesk font-black text-xs uppercase tracking-[0.3em] bg-black text-white px-6 py-3 hover:bg-white hover:text-black transition-all"
                            >
                                [ CLOSE ]
                            </button>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                            {/* LEFT COL: PHILOSOPHY & EXCLUSIONS */}
                            <div className="lg:col-span-3 space-y-12">
                                <div className="space-y-6">
                                    <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block border-b border-black/5 pb-2">MATCHING PHILOSOPHY</label>
                                    <div className="space-y-4">
                                        <div className={`p-4 border-2 ${philosophy.partial_matches_allowed ? 'border-black bg-white' : 'border-black/5 opacity-30'} space-y-2`}>
                                            <span className="font-grotesk text-[9px] font-black uppercase tracking-widest block">PARTIAL MATCHES</span>
                                            <span className="font-inter text-[10px] font-bold block">{philosophy.partial_matches_allowed ? 'ACCEPTED' : 'DISABLED'}</span>
                                        </div>
                                        <div className={`p-4 border-2 ${philosophy.evidence_over_claims ? 'border-[#A7FF2E] bg-[#A7FF2E]/5' : 'border-black/5 opacity-30'} space-y-2`}>
                                            <span className="font-grotesk text-[9px] font-black uppercase tracking-widest block">EVIDENCE FIRST</span>
                                            <span className="font-inter text-[10px] font-bold block">{philosophy.evidence_over_claims ? 'ACTIVE' : 'INACTIVE'}</span>
                                        </div>
                                    </div>
                                </div>

                                {exclusions.length > 0 && (
                                    <div className="space-y-6">
                                        <label className="font-grotesk text-[10px] font-black uppercase tracking-widest block text-red-600">NULLIFIED SIGNALS</label>
                                        <div className="flex flex-wrap gap-2">
                                            {exclusions.map(ex => (
                                                <span key={ex} className="font-inter text-[9px] font-black bg-red-50 text-red-600 border border-red-100 px-3 py-1 uppercase line-through opacity-50">{ex}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* CENTER COL: SKILL GROUPS */}
                            <div className="lg:col-span-6 border-x-2 border-black/5 px-8 space-y-12">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    {/* LANGUAGES */}
                                    <div className="space-y-4">
                                        <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block">LANGUAGES</label>
                                        <div className="flex flex-wrap gap-2">
                                            {languages.map(l => <span key={l} className="font-inter text-[10px] font-black bg-black text-white px-3 py-1 uppercase">{l}</span>)}
                                        </div>
                                    </div>
                                    {/* WEB FUNDAMENTALS */}
                                    <div className="space-y-4">
                                        <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block">WEB FUNDAMENTALS</label>
                                        <div className="flex flex-wrap gap-2">
                                            {web_fundamentals.map(w => <span key={w} className="font-inter text-[10px] font-black border-2 border-black px-3 py-1 uppercase">{w}</span>)}
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-black/5">
                                    {/* FRAMEWORKS */}
                                    <div className="space-y-4">
                                        <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block">FRONTEND FRAMEWORKS</label>
                                        <div className="flex flex-wrap gap-2">
                                            {frontend_frameworks.map(f => <span key={f} className="font-inter text-[10px] font-bold bg-white border border-black/10 px-3 py-1 uppercase">{f}</span>)}
                                        </div>
                                    </div>
                                    <div className="space-y-4">
                                        <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block">BACKEND FRAMEWORKS</label>
                                        <div className="flex flex-wrap gap-2">
                                            {backend_frameworks.map(b => <span key={b} className="font-inter text-[10px] font-bold bg-white border border-black/10 px-3 py-1 uppercase">{b}</span>)}
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-black/5">
                                    {/* DB / TOOLING */}
                                    <div className="space-y-4">
                                        <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block">DATABASES</label>
                                        <div className="flex flex-wrap gap-2">
                                            {databases.map(db => <span key={db} className="font-inter text-[10px] font-bold opacity-60 uppercase">{db}</span>)}
                                        </div>
                                    </div>
                                    <div className="space-y-4">
                                        <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block">INFRASTRUCTURE CONCEPTS</label>
                                        <div className="flex flex-wrap gap-2">
                                            {infrastructure_concepts.map(i => <span key={i} className="font-inter text-[10px] font-bold opacity-60 uppercase">{i}</span>)}
                                        </div>
                                    </div>
                                    <div className="space-y-4 pt-4 border-t border-black/5">
                                        <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block">DEVELOPER TOOLS</label>
                                        <div className="flex flex-wrap gap-2">
                                            {developer_tools.map(t => <span key={t} className="font-inter text-[10px] font-bold opacity-60 uppercase">{t}</span>)}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* RIGHT COL: EVALUATION & REQUIREMENTS */}
                            <div className="lg:col-span-3 space-y-12">
                                {/* STRICT REQUIREMENTS */}
                                <div className="space-y-6">
                                    <label className="font-grotesk text-[10px] font-black uppercase tracking-widest block bg-black text-white px-3 py-1 w-fit">STRICT REQUIREMENTS</label>
                                    <ul className="space-y-3">
                                        {strict.map((s, i) => (
                                            <li key={i} className="flex gap-3 items-start">
                                                <div className="w-1.5 h-1.5 bg-black rotate-45 mt-1.5 shrink-0" />
                                                <span className="font-inter text-[11px] font-black uppercase leading-tight">{s}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                {/* EVIDENCE */}
                                <div className="space-y-6 pt-12 border-t border-black/5">
                                    <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block">EVALUATION SIGNALS</label>
                                    {evidence.github && (
                                        <div className="bg-black text-white p-4 space-y-2">
                                            <span className="font-grotesk text-[9px] font-black uppercase tracking-widest block opacity-50">GITHUB PLATFORM</span>
                                            <span className="font-inter text-[10px] font-black block text-[#A7FF2E]">{evidence.github.slice(0, 3).join(" • ")}</span>
                                        </div>
                                    )}
                                    {problem_solving.signals && (
                                        <div className={`p-4 space-y-2 border-2 ${problem_solving.required ? 'bg-[#A7FF2E] text-black border-black' : 'bg-white/50 text-black/40 border-black/5'}`}>
                                            <span className="font-grotesk text-[9px] font-black uppercase tracking-widest block opacity-50">
                                                COMPETITIVE PROG {problem_solving.required ? '' : '(OPTIONAL)'}
                                            </span>
                                            <span className="font-inter text-[10px] font-black block">{problem_solving.signals.join(" • ")}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* FAIRNESS FINDINGS (BOTTOM) */}
                        {findings.length > 0 && (
                            <div className="mt-12 pt-12 border-t-4 border-black space-y-8">
                                <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.2em] text-[#FF4D4D] block">BIAS SCAN FINDINGS</label>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {findings.map((finding, idx) => (
                                        <div key={idx} className="bg-white p-6 border-2 border-black space-y-4">
                                            <div className="space-y-1">
                                                <span className="font-grotesk text-[9px] font-black text-red-600 uppercase tracking-widest block">FLAGGED PHRASE</span>
                                                <span className="font-inter text-xs font-bold text-black uppercase">"{finding.phrase}"</span>
                                            </div>
                                            <div className="pt-4 border-t border-black/5">
                                                <span className="font-grotesk text-[9px] font-black text-red-600 uppercase tracking-widest block mb-1">RECOMMENDED FIX</span>
                                                <span className="font-inter text-[10px] font-black bg-[#A7FF2E] border border-black px-3 py-1 text-black uppercase">{finding.fix}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}