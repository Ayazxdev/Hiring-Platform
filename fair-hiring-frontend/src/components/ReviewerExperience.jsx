import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import GridPlus from './GridPlus';
import { api } from '../api/backend';

// Preview data — used when no company session or no real cases exist
const PREVIEW_QUEUE = [
    {
        id: 'PRV-1',
        application_id: 101,
        job_id: 5,
        role: 'Senior Frontend Engineer',
        candidate_anon_id: 'ANON-X7F29A3B1C',
        severity: 'high',
        reason: 'Bias loop stuck after 4 re-evaluations — GitHub evidence conflicts with resume claims on React expertise',
        status: 'pending',
        triggered_by: 'bias_agent',
        created_at: new Date().toISOString(),
        skills: ['React', 'TypeScript', 'Node.js', 'GraphQL', 'AWS'],
        evidence_sources: ['GITHUB', 'ATS', 'RESUME'],
        confidence: 72,
        match_score: 68,
        evidence_json: {
            manipulation: { severity: 'medium', flags: ['commit_frequency_spike', 'repo_freshness_anomaly'] },
            integrity_check: { discrepancy_detected: true, type: 'skill_inflation' },
            ats_semantic_flags: ['keyword_stuffing_detected']
        },
        feedback: { message: 'Under review' }
    },
    {
        id: 'PRV-2',
        application_id: 102,
        job_id: 5,
        role: 'Backend Systems Engineer',
        candidate_anon_id: 'ANON-B2K8Z4M1P',
        severity: 'critical',
        reason: 'Resume manipulation detected — claimed contributions to open-source repos do not exist',
        status: 'pending',
        triggered_by: 'skill_agent',
        created_at: new Date(Date.now() - 3600000).toISOString(),
        skills: ['Python', 'Django', 'PostgreSQL', 'Docker'],
        evidence_sources: ['GITHUB', 'LINKEDIN', 'ATS'],
        confidence: 34,
        match_score: 41,
        evidence_json: {
            manipulation: { severity: 'critical', flags: ['fabricated_repos', 'identity_mismatch'] },
            integrity_check: { discrepancy_detected: true, type: 'fabricated_evidence' },
            ats_semantic_flags: ['experience_inflation', 'role_mismatch']
        },
        feedback: { message: 'Under review' }
    },
    {
        id: 'PRV-3',
        application_id: 103,
        job_id: 8,
        role: 'ML / Data Engineer',
        candidate_anon_id: 'ANON-C9D4E7F2Q',
        severity: 'medium',
        reason: 'Skill verification ambiguity — TensorFlow usage claimed but only tutorial-level repos found',
        status: 'pending',
        triggered_by: 'bias_agent',
        created_at: new Date(Date.now() - 7200000).toISOString(),
        skills: ['Python', 'TensorFlow', 'SQL', 'Pandas', 'NumPy'],
        evidence_sources: ['GITHUB', 'RESUME'],
        confidence: 55,
        match_score: 52,
        evidence_json: {
            manipulation: { severity: 'low', flags: ['skill_depth_uncertain'] },
            integrity_check: { discrepancy_detected: false },
            ats_semantic_flags: []
        },
        feedback: { message: 'Under review' }
    }
];

export default function ReviewerExperience({ onExit }) {
    const [queue, setQueue] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isPreview, setIsPreview] = useState(false);
    const [activePage, setActivePage] = useState('dashboard');
    const [selectedCase, setSelectedCase] = useState(null);
    const [actionLoading, setActionLoading] = useState(null);
    const [activeDetailTab, setActiveDetailTab] = useState('resume');

    const companyId = localStorage.getItem("fhn_company_id") || "";

    useEffect(() => {
        (async () => {
            try {
                // companyId is optional — global reviewer queue works without it
                const data = await api.reviewQueue(companyId || null);
                setQueue(Array.isArray(data) ? data : []);
                setIsPreview(false);
            } catch (e) {
                console.warn("Failed to load review queue", e);
                setQueue([]);
                setIsPreview(false);
            } finally {
                setIsLoading(false);
            }
        })();
    }, [companyId]);

    const handleReview = (item) => {
        setSelectedCase(item);
        setActivePage('review');
    };

    const handleAction = async (action) => {
        if (!selectedCase) return;
        setActionLoading(action);
        try {
            if (isPreview) {
                // Preview mode: simulate action locally
                await new Promise(r => setTimeout(r, 800));
                setQueue(prev => prev.filter(c => c.id !== selectedCase.id));
            } else {
                await api.reviewAction(companyId || null, selectedCase.id, {
                    action,
                    note: `${action === 'clear' ? 'Cleared' : 'Blacklisted'} by reviewer via UI`
                });
                const data = await api.reviewQueue(companyId || null);
                setQueue(Array.isArray(data) ? data : []);
            }
            setSelectedCase(null);
            setActivePage('dashboard');
        } catch (e) {
            console.error("Review action failed:", e);
            alert("Action failed. Check console.");
        } finally {
            setActionLoading(null);
        }
    };

    const getSeverityColor = (severity) => {
        if (severity === 'critical') return 'bg-red-600';
        if (severity === 'high') return 'bg-orange-600';
        if (severity === 'medium') return 'bg-yellow-600';
        return 'bg-blue-600';
    };

    const pageTransition = {
        initial: { x: 20, opacity: 0 },
        animate: { x: 0, opacity: 1 },
        exit: { x: -20, opacity: 0 },
        transition: { duration: 0.5, ease: [0.4, 0, 0.2, 1] }
    };

    return (
        <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
            className="fixed inset-0 z-[160] bg-[#E6E6E3] text-[#1c1c1c] overflow-y-auto selection:bg-black selection:text-white custom-scrollbar-reviewer"
            style={{ willChange: 'transform' }}
            data-lenis-prevent
        >
            {/* STICKY HEADER */}
            <header className="sticky top-0 left-0 w-full bg-[#E6E6E3] border-b-[3px] border-[#1c1c1c] z-50 px-6 md:px-12 py-5 flex justify-between items-center bg-opacity-95 backdrop-blur-sm">
                <div className="flex items-center gap-6">
                    <button
                        onClick={activePage === 'review' ? () => { setActivePage('dashboard'); setSelectedCase(null); } : onExit}
                        className="px-6 py-2.5 border-[2px] border-[#1c1c1c] font-grotesk text-[10px] font-black uppercase tracking-[0.2em] hover:bg-[#1c1c1c] hover:text-[#E6E6E3] transition-all flex items-center gap-2 group"
                    >
                        <span className="group-hover:-translate-x-1 transition-transform inline-block">←</span>
                        {activePage === 'review' ? 'BACK' : 'EXIT'}
                    </button>
                    <div className="h-10 w-[2px] bg-[#1c1c1c]/10 hidden md:block"></div>
                    <span className="font-montreal font-black text-sm tracking-[0.2em] uppercase text-[#1c1c1c]">
                        REVIEW TERMINAL
                    </span>
                </div>
                <div className="font-grotesk text-[11px] font-black tracking-[0.1em] uppercase opacity-100 text-[#1c1c1c]">
                    AUTH: HUMAN_VERIFIER
                </div>
            </header>

            <main className="max-w-[1280px] mx-auto px-6 md:px-12 py-16 min-h-[90vh]">
                <AnimatePresence mode="wait">
                    {/* Queue list view */}
                    {activePage === 'dashboard' && (
                        <motion.div key="dashboard" {...pageTransition} className="space-y-16">
                            <div className="space-y-4">
                                <h1 className="font-montreal font-black text-5xl md:text-8xl uppercase tracking-tighter leading-none">
                                    PENDING <br />QUEUE
                                </h1>
                                <p className="font-inter text-[11px] font-black opacity-40 uppercase tracking-[0.2em]">
                                    {isLoading ? 'LOADING...' : `${queue.length} ANOMALIES ESCALATED FOR HUMAN VERIFICATION`}
                                </p>
                            </div>

                            {isPreview && (
                                <div className="px-6 py-4 bg-[#1c1c1c] text-white flex items-center gap-4 rounded-sm">
                                    <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse shrink-0" />
                                    <span className="font-grotesk text-[10px] font-black uppercase tracking-[0.2em]">
                                        PREVIEW MODE — Showing simulated review cases. Real cases appear when the bias agent escalates anomalies.
                                    </span>
                                </div>
                            )}

                            {isLoading ? (
                                <div className="py-24 text-center">
                                    <div className="font-grotesk text-[10px] font-black uppercase tracking-[0.5em] animate-pulse">
                                        CONNECTING TO REVIEW PIPELINE...
                                    </div>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 gap-6">
                                    {queue.map((item) => (
                                        <div
                                            key={item.id}
                                            className="group bg-white border-[2px] border-[#1c1c1c] p-8 flex flex-col md:flex-row md:items-center justify-between gap-8 hover:shadow-[12px_12px_0px_rgba(0,0,0,0.03)] transition-all duration-300 rounded-sm"
                                        >
                                            <div className="space-y-6">
                                                <div className="space-y-2">
                                                    <div className="flex items-center gap-4 flex-wrap">
                                                        <span className="font-montreal font-black text-2xl md:text-4xl uppercase tracking-tight text-[#1c1c1c]">
                                                            {item.candidate_name || 'Anonymous Candidate'}
                                                        </span>
                                                        <span className={`px-3 py-1 ${getSeverityColor(item.severity)} text-white text-[9px] font-grotesk font-black uppercase tracking-widest rounded-sm`}>
                                                            {item.severity === 'critical' ? 'BLACKLISTED' : (item.severity || 'NEEDS REVIEW')}
                                                        </span>
                                                        <span className="px-3 py-1 bg-[#1c1c1c] text-white border border-[#1c1c1c] text-[10px] font-grotesk font-black uppercase tracking-widest rounded-sm">
                                                            {item.candidate_anon_id}
                                                        </span>
                                                    </div>
                                                    <div className="font-inter text-xs font-bold text-orange-700 uppercase tracking-widest flex items-center gap-2">
                                                        <span className="w-1.5 h-1.5 bg-orange-600 rounded-full animate-pulse" />
                                                        {item.reason || 'Anomaly detected by pipeline'}
                                                    </div>
                                                    {item.triggered_by && (
                                                        <div className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-30">
                                                            TRIGGERED BY: {item.triggered_by}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => handleReview(item)}
                                                className="px-10 py-5 bg-[#1c1c1c] text-white font-grotesk text-[11px] tracking-[0.3em] font-black uppercase hover:bg-black hover:scale-[1.02] transition-all flex items-center gap-3 group/btn shrink-0"
                                            >
                                                REVIEW <span className="text-xl group-hover/btn:translate-x-1 transition-transform">→</span>
                                            </button>
                                        </div>
                                    ))}

                                    {queue.length === 0 && (
                                        <div className="py-24 text-center space-y-4">
                                            <div className="font-montreal font-black text-4xl opacity-20 italic">QUEUE DEPLETED</div>
                                            <p className="font-inter text-[10px] font-black uppercase tracking-widest opacity-40">
                                                {companyId ? 'All system anomalies have been verified.' : 'No company session. Log in as a company first.'}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </motion.div>
                    )}

                    {/* Case details and actions */}
                    {selectedCase && (
                        <motion.div
                            key="detail"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="space-y-12"
                        >
                            <div className="flex flex-col gap-6 border-b-[2px] border-[#1c1c1c] pb-8">
                                <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
                                    <div className="space-y-3">
                                        <div className="flex items-center gap-4">
                                            <span className="font-grotesk text-[10px] uppercase font-black tracking-widest opacity-40">FORENSIC AUDIT SESSION</span>
                                            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                                            <span className={`px-3 py-1 ${getSeverityColor(selectedCase.severity)} text-white text-[9px] font-grotesk font-black uppercase tracking-widest rounded-sm`}>
                                                {selectedCase.severity === 'critical' ? 'BLACKLISTED' : selectedCase.severity}
                                            </span>
                                            {selectedCase.company_name && (
                                                <span className="px-3 py-1 bg-black/5 border border-black/20 text-[#1c1c1c] text-[9px] font-grotesk font-black uppercase tracking-widest">
                                                    COMPANY: {selectedCase.company_name}
                                                </span>
                                            )}
                                        </div>
                                        <h2 className="font-montreal font-black text-4xl md:text-6xl uppercase tracking-tighter leading-none">
                                            {selectedCase.candidate_name || selectedCase.candidate_anon_id}
                                        </h2>
                                        <p className="font-inter text-xs font-bold uppercase tracking-widest opacity-50">
                                            {selectedCase.candidate_email} · {selectedCase.role || 'Technical Role'} · Case #{selectedCase.id} · ID: {selectedCase.candidate_anon_id}
                                        </p>
                                    </div>
                                </div>

                                {/* CANDIDATE DOSSIER & PROFILE LINKS BAR */}
                                <div className="p-4 bg-white border-2 border-[#1c1c1c] shadow-[4px_4px_0px_#000] flex flex-wrap items-center justify-between gap-4">
                                    <div className="flex items-center gap-2">
                                        <span className="font-grotesk text-[10px] font-black uppercase tracking-[0.2em] text-[#1c1c1c]/60">
                                            VERIFICATION DOSSIER:
                                        </span>
                                    </div>
                                    <div className="flex flex-wrap items-center gap-3">
                                        {selectedCase.github_url && (
                                            <a
                                                href={selectedCase.github_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="px-4 py-2 bg-black text-white font-grotesk text-[10px] font-black uppercase tracking-wider hover:bg-[#A7FF2E] hover:text-black transition-all flex items-center gap-2 shadow-[2px_2px_0px_#A7FF2E] cursor-pointer"
                                                title="Open verified GitHub profile in new tab"
                                            >
                                                <span>GITHUB ↗</span>
                                                <span className="opacity-40 font-mono text-[9px] hidden sm:inline">({selectedCase.github_url.replace('https://github.com/', '')})</span>
                                            </a>
                                        )}
                                        {selectedCase.linkedin_url && (
                                            <a
                                                href={selectedCase.linkedin_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="px-4 py-2 bg-white text-black border-2 border-black font-grotesk text-[10px] font-black uppercase tracking-wider hover:bg-black hover:text-white transition-all flex items-center gap-1.5 shadow-[2px_2px_0px_#000] cursor-pointer"
                                                title="Open candidate LinkedIn profile in new tab"
                                            >
                                                <span>LINKEDIN ↗</span>
                                            </a>
                                        )}
                                        {selectedCase.leetcode_url && (
                                            <a
                                                href={selectedCase.leetcode_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="px-4 py-2 bg-white text-[#d48806] border-2 border-black font-grotesk text-[10px] font-black uppercase tracking-wider hover:bg-[#FFA116] hover:text-black transition-all flex items-center gap-1.5 shadow-[2px_2px_0px_#000] cursor-pointer"
                                                title="Open LeetCode benchmark profile"
                                            >
                                                <span>LEETCODE ↗</span>
                                            </a>
                                        )}
                                        {selectedCase.codeforces_url && (
                                            <a
                                                href={selectedCase.codeforces_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="px-4 py-2 bg-white text-[#096dd9] border-2 border-black font-grotesk text-[10px] font-black uppercase tracking-wider hover:bg-[#1F8ACB] hover:text-white transition-all flex items-center gap-1.5 shadow-[2px_2px_0px_#000] cursor-pointer"
                                                title="Open Codeforces rating profile"
                                            >
                                                <span>CODEFORCES ↗</span>
                                            </a>
                                        )}
                                        {selectedCase.college && (
                                            <span className="px-3 py-1.5 bg-[#F9F9F7] border border-black/20 text-[#1c1c1c] font-grotesk text-[9px] font-black uppercase tracking-widest">
                                                CAMPUS: {selectedCase.college}
                                            </span>
                                        )}
                                        {selectedCase.engineer_level && (
                                            <span className="px-3 py-1.5 bg-[#F9F9F7] border border-black/20 text-[#1c1c1c] font-grotesk text-[9px] font-black uppercase tracking-widest">
                                                TIER: {selectedCase.engineer_level}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                                {/* LEFT: EVIDENCE SIGNALS & METRICS */}
                                <div className="lg:col-span-5 space-y-12">
                                    {/* Skills */}
                                    <div className="space-y-6">
                                        <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.3em] text-[#1c1c1c]/40">VERIFIED SKILLS</label>
                                        <div className="flex flex-wrap gap-2">
                                            {(selectedCase.skills || []).length > 0 ? (
                                                selectedCase.skills.map(skill => (
                                                    <span key={skill} className="px-4 py-2 bg-white border-[2px] border-[#1c1c1c] font-grotesk text-[10px] font-black uppercase tracking-widest shadow-[4px_4px_0px_rgba(0,0,0,0.05)]">
                                                        {skill}
                                                    </span>
                                                ))
                                            ) : (
                                                <span className="font-inter text-xs opacity-40 italic">No skills data available</span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Evidence Sources */}
                                    <div className="p-8 bg-white border-[2px] border-[#1c1c1c] space-y-8 shadow-[8px_8px_0px_rgba(0,0,0,0.02)]">
                                        <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.3em] text-[#1c1c1c]/40">EVIDENCE CHANNELS</label>
                                        <div className="space-y-4">
                                            {(selectedCase.evidence_sources || ['ATS', 'GITHUB', 'RESUME']).map(source => (
                                                <div key={source} className="p-5 bg-[#F9F9F7] border border-[#1c1c1c]/10 flex items-center justify-between group cursor-pointer hover:border-[#1c1c1c] transition-all">
                                                    <span className="font-grotesk text-[11px] font-black uppercase tracking-widest text-[#1c1c1c]">{source}</span>
                                                    <span className="font-mono text-[9px] text-green-700 font-bold">VERIFIED CHANNEL</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Stats */}
                                    <div className="grid grid-cols-2 gap-6">
                                        <div className="p-6 bg-white border-[2px] border-[#1c1c1c] space-y-2">
                                            <label className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-40">CONFIDENCE</label>
                                            <div className="font-montreal font-black text-3xl">{selectedCase.confidence || 0}%</div>
                                        </div>
                                        <div className="p-6 bg-white border-[2px] border-[#1c1c1c] space-y-2">
                                            <label className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-40">MATCH SCORE</label>
                                            <div className="font-montreal font-black text-3xl">{selectedCase.match_score || 0}%</div>
                                        </div>
                                    </div>
                                </div>

                                {/* RIGHT: ANOMALY ANALYSIS & FORENSIC PAYLOADS */}
                                <div className="lg:col-span-7 space-y-8 bg-white border-[2px] border-[#1c1c1c] p-8 md:p-12 shadow-[12px_12px_0px_rgba(0,0,0,0.03)]">
                                    <div className="space-y-8">
                                        {/* Reason / Anomaly */}
                                        <div className="space-y-3">
                                            <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.3em] text-orange-600">ESCALATION REASON</label>
                                            <div className="flex gap-4 items-start p-4 bg-orange-50 border-l-4 border-orange-600">
                                                <p className="font-inter text-sm md:text-base font-bold leading-relaxed text-[#1c1c1c]">
                                                    {selectedCase.reason}
                                                </p>
                                            </div>
                                        </div>

                                        {/* SPECIALIZED FORENSIC PAYLOAD ALERTS */}
                                        {selectedCase.evidence_json && (
                                            <div className="space-y-6">
                                                <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.3em] text-[#1c1c1c]/40">INTERCEPTED FORENSICS</label>

                                                {/* 1. Prompt Injection Payload */}
                                                {selectedCase.evidence_json.injection_payload && (
                                                    <div className="p-5 bg-[#120303] text-red-200 border-2 border-red-600 font-mono text-xs space-y-3 shadow-[4px_4px_0px_#000]">
                                                        <div className="flex items-center justify-between text-red-400 font-bold uppercase tracking-wider text-[10px] border-b border-red-900 pb-2">
                                                            <span className="flex items-center gap-2">
                                                                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                                                                INTERCEPTED PROMPT INJECTION PAYLOAD
                                                            </span>
                                                            <span className="px-2 py-0.5 bg-red-600 text-white text-[9px]">CRITICAL</span>
                                                        </div>
                                                        <pre className="bg-black/60 p-3 rounded text-red-200 select-all whitespace-pre-wrap font-mono text-[11px] leading-relaxed border border-red-900/40">
                                                            {selectedCase.evidence_json.injection_payload}
                                                        </pre>
                                                    </div>
                                                )}

                                                {/* 2. Hidden White-Text Keywords */}
                                                {selectedCase.evidence_json.hidden_keywords?.length > 0 && (
                                                    <div className="p-5 bg-[#140e02] text-amber-200 border-2 border-amber-600 font-mono text-xs space-y-3 shadow-[4px_4px_0px_#000]">
                                                        <div className="flex items-center justify-between text-amber-400 font-bold uppercase tracking-wider text-[10px] border-b border-amber-900 pb-2">
                                                            <span>CONCEALED ZERO-OPACITY (WHITE TEXT) KEYWORDS</span>
                                                            <span className="px-2 py-0.5 bg-amber-600 text-black font-bold text-[9px]">ATS FRAUD</span>
                                                        </div>
                                                        <p className="text-amber-200/80 text-[11px]">
                                                            The OCR layer detected {selectedCase.evidence_json.hidden_keywords.length} keywords styled with 0-pt font or matching background color:
                                                        </p>
                                                        <div className="flex flex-wrap gap-1.5 pt-1">
                                                            {selectedCase.evidence_json.hidden_keywords.map((kw, i) => (
                                                                <span key={i} className="px-2.5 py-1 bg-black/60 text-amber-300 border border-amber-500/40 text-[10px] font-bold">
                                                                    {kw}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* 3. GitHub Author Audit Discrepancy */}
                                                {selectedCase.evidence_json.github_audit && (
                                                    <div className="p-5 bg-[#030e1c] text-blue-200 border-2 border-blue-600 font-mono text-xs space-y-3 shadow-[4px_4px_0px_#000]">
                                                        <div className="flex items-center justify-between text-blue-400 font-bold uppercase tracking-wider text-[10px] border-b border-blue-900 pb-2">
                                                            <span>GITHUB AUTHOR AUDIT DISCREPANCY</span>
                                                            <span className="px-2 py-0.5 bg-blue-600 text-white text-[9px]">AUTHORSHIP MISMATCH</span>
                                                        </div>
                                                        <div className="grid grid-cols-2 gap-3 text-[11px] pt-1">
                                                            <div>Target Repo: <strong className="text-white font-mono">{selectedCase.evidence_json.github_audit.claimed_repo}</strong></div>
                                                            <div>Claimed Commits: <strong className="text-white font-mono">{selectedCase.evidence_json.github_audit.claimed_contributions}</strong></div>
                                                            <div>Verified Signed Commits: <strong className="text-red-400 font-mono">{selectedCase.evidence_json.github_audit.verified_contributions}</strong></div>
                                                            <div>Email GPG Match: <strong className="text-red-400 font-mono">{String(selectedCase.evidence_json.github_audit.author_email_match).toUpperCase()}</strong></div>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* 4. Bias Metrics */}
                                                {selectedCase.evidence_json.bias_metrics && (
                                                    <div className="p-5 bg-[#12051c] text-purple-200 border-2 border-purple-600 font-mono text-xs space-y-3 shadow-[4px_4px_0px_#000]">
                                                        <div className="flex items-center justify-between text-purple-400 font-bold uppercase tracking-wider text-[10px] border-b border-purple-900 pb-2">
                                                            <span>ALGORITHMIC BIAS PARITY DEADLOCK</span>
                                                            <span className="px-2 py-0.5 bg-purple-600 text-white text-[9px]">FAIRNESS THRESHOLD</span>
                                                        </div>
                                                        <div className="grid grid-cols-2 gap-3 text-[11px] pt-1">
                                                            <div>Disparate Impact: <strong className="text-red-400 font-mono">{selectedCase.evidence_json.bias_metrics.disparate_impact_ratio}</strong> (Req: {selectedCase.evidence_json.bias_metrics.threshold})</div>
                                                            <div>Automated Iterations: <strong className="text-white font-mono">{selectedCase.evidence_json.bias_metrics.re_evaluation_attempts}</strong></div>
                                                            <div>Convergence Status: <strong className="text-orange-400 font-mono uppercase">{selectedCase.evidence_json.bias_metrics.convergence_status}</strong></div>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* 5. Skill Depth Discrepancy */}
                                                {selectedCase.evidence_json.skill_depth_audit && (
                                                    <div className="p-5 bg-[#1a0c02] text-orange-200 border-2 border-orange-600 font-mono text-xs space-y-3 shadow-[4px_4px_0px_#000]">
                                                        <div className="flex items-center justify-between text-orange-400 font-bold uppercase tracking-wider text-[10px] border-b border-orange-900 pb-2">
                                                            <span>CODE COMPLEXITY (AST) VS. RESUME CLAIM</span>
                                                            <span className="px-2 py-0.5 bg-orange-600 text-white text-[9px]">DEPTH GAP</span>
                                                        </div>
                                                        <div className="grid grid-cols-2 gap-3 text-[11px] pt-1">
                                                            <div>Claimed Seniority: <strong className="text-white font-mono">{selectedCase.evidence_json.skill_depth_audit.claimed_experience}</strong></div>
                                                            <div>Verified Code AST: <strong className="text-orange-400 font-mono">{selectedCase.evidence_json.skill_depth_audit.verified_code_depth}</strong></div>
                                                            <div>Complexity Index: <strong className="text-white font-mono">{selectedCase.evidence_json.skill_depth_audit.ast_complexity_index}</strong></div>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Telemetry Summary */}
                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                                                    {selectedCase.evidence_json.manipulation && (
                                                        <div className="p-4 bg-[#F9F9F7] border border-black/10">
                                                            <span className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-40 block mb-1">MANIPULATION SEVERITY</span>
                                                            <span className="font-mono text-xs font-bold text-red-600 uppercase">
                                                                {selectedCase.evidence_json.manipulation.severity}
                                                            </span>
                                                            {selectedCase.evidence_json.manipulation.flags?.length > 0 && (
                                                                <p className="font-mono text-[10px] opacity-70 mt-1">
                                                                    {selectedCase.evidence_json.manipulation.flags.join(', ')}
                                                                </p>
                                                            )}
                                                        </div>
                                                    )}
                                                    {selectedCase.evidence_json.integrity_check && (
                                                        <div className="p-4 bg-[#F9F9F7] border border-black/10">
                                                            <span className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-40 block mb-1">INTEGRITY STATUS</span>
                                                            <span className={`font-mono text-xs font-bold ${selectedCase.evidence_json.integrity_check.discrepancy_detected ? 'text-orange-600' : 'text-green-600'}`}>
                                                                {selectedCase.evidence_json.integrity_check.discrepancy_detected ? 'DISCREPANCY FLAGGED' : 'CLEAN'}
                                                            </span>
                                                            <p className="font-mono text-[10px] opacity-70 mt-1">
                                                                Type: {selectedCase.evidence_json.integrity_check.type || 'Standard'}
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        )}

                                        {/* Triggered By & Escalated At */}
                                        <div className="grid grid-cols-2 gap-8 pt-6 border-t-[2px] border-[#1c1c1c]/10">
                                            <div className="space-y-1">
                                                <label className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-40">TRIGGERING AGENT</label>
                                                <div className="font-montreal font-black text-lg uppercase">{selectedCase.triggered_by || 'PIPELINE'}</div>
                                            </div>
                                            <div className="space-y-1">
                                                <label className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-40">ESCALATED AT</label>
                                                <div className="font-inter text-xs font-bold">
                                                    {selectedCase.created_at ? new Date(selectedCase.created_at).toLocaleString() : '—'}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Human Protocol Message */}
                                        <div className="p-6 bg-[#1c1c1c] text-white space-y-2">
                                            <span className="font-grotesk text-[9px] font-black uppercase tracking-[0.3em] opacity-40">REVIEWER DIRECTIVE</span>
                                            <p className="font-inter text-xs leading-relaxed font-medium opacity-80">
                                                Examine the candidate profiles, full resume text, and telemetry below. If this anomaly is an adversarial exploit or evidence tampering, click <strong>CONFIRM FRAUD & BLACKLIST</strong>. If it is a benign false positive or acceptable variance, click <strong>CLEAR EVIDENCE & APPROVE</strong> to restore the candidate.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Forensic documents and telemetry */}
                            <div className="bg-white border-2 border-black shadow-[8px_8px_0px_#000] p-6 md:p-10 space-y-6">
                                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b-2 border-black pb-4 gap-4">
                                    <div>
                                        <span className="px-2.5 py-1 bg-[#A7FF2E] text-black font-grotesk text-[9px] font-black uppercase tracking-wider">
                                            PRIMARY EVIDENCE REPOSITORY
                                        </span>
                                        <h3 className="font-montreal font-black text-2xl uppercase tracking-tight mt-1">
                                            Document & Telemetry Inspector
                                        </h3>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => setActiveDetailTab('resume')}
                                            className={`px-4 py-2 font-grotesk text-[10px] font-black uppercase tracking-widest transition-all cursor-pointer ${
                                                activeDetailTab === 'resume'
                                                    ? 'bg-black text-white'
                                                    : 'bg-white text-black border border-black hover:bg-black/5'
                                            }`}
                                        >
                                            📄 Resume Text (OCR)
                                        </button>
                                        <button
                                            onClick={() => setActiveDetailTab('telemetry')}
                                            className={`px-4 py-2 font-grotesk text-[10px] font-black uppercase tracking-widest transition-all cursor-pointer ${
                                                activeDetailTab === 'telemetry'
                                                    ? 'bg-black text-white'
                                                    : 'bg-white text-black border border-black hover:bg-black/5'
                                            }`}
                                        >
                                            🔍 Raw Telemetry JSON
                                        </button>
                                        <button
                                            onClick={() => setActiveDetailTab('skills')}
                                            className={`px-4 py-2 font-grotesk text-[10px] font-black uppercase tracking-widest transition-all cursor-pointer ${
                                                activeDetailTab === 'skills'
                                                    ? 'bg-black text-white'
                                                    : 'bg-white text-black border border-black hover:bg-black/5'
                                            }`}
                                        >
                                            🎯 Skills Matrix
                                        </button>
                                    </div>
                                </div>

                                {activeDetailTab === 'resume' && (
                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between text-xs text-black/60 font-grotesk uppercase font-bold">
                                            <span>EXTRACTED VIA TESSERACT OCR & PDF PARSER</span>
                                            {selectedCase.resume_text && (
                                                <button
                                                    onClick={() => {
                                                        navigator.clipboard.writeText(selectedCase.resume_text);
                                                        alert("Full resume text copied to clipboard!");
                                                    }}
                                                    className="hover:underline hover:text-black cursor-pointer"
                                                >
                                                    Copy Resume Text
                                                </button>
                                            )}
                                        </div>
                                        <div className="bg-[#101218] p-6 text-white font-mono text-xs overflow-y-auto max-h-[420px] rounded border border-black leading-relaxed whitespace-pre-wrap select-all">
                                            {selectedCase.resume_text || "No raw resume text recorded for this application."}
                                        </div>
                                    </div>
                                )}

                                {activeDetailTab === 'telemetry' && (
                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between text-xs text-black/60 font-grotesk uppercase font-bold">
                                            <span>FULL EVIDENCE JSON & ANOMALY SIGNALS</span>
                                            <button
                                                onClick={() => {
                                                    navigator.clipboard.writeText(JSON.stringify(selectedCase.evidence_json, null, 2));
                                                    alert("Evidence JSON copied to clipboard!");
                                                }}
                                                className="hover:underline hover:text-black cursor-pointer"
                                            >
                                                Copy JSON
                                            </button>
                                        </div>
                                        <pre className="bg-[#101218] p-6 text-[#A7FF2E] font-mono text-xs overflow-y-auto max-h-[420px] rounded border border-black leading-relaxed whitespace-pre-wrap select-all">
                                            {JSON.stringify(selectedCase.evidence_json || {}, null, 2)}
                                        </pre>
                                    </div>
                                )}

                                {activeDetailTab === 'skills' && (
                                    <div className="space-y-6">
                                        <div className="flex items-center justify-between text-xs text-black/60 font-grotesk uppercase font-bold">
                                            <span>COMPETENCY GRAPH & PROVEN ATTRIBUTES</span>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                                            {(selectedCase.skills || []).map((skill, i) => (
                                                <div key={i} className="p-4 bg-[#F9F9F7] border border-black/10 flex items-center justify-between">
                                                    <span className="font-grotesk font-black text-xs uppercase">{skill}</span>
                                                    <span className="font-mono text-[10px] text-green-700 font-bold">VERIFIED</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Decision controls */}
                            <div className="w-full flex flex-col sm:flex-row gap-6 justify-center items-center py-12 border-t-[3px] border-[#1c1c1c] mt-12">
                                <button
                                    onClick={() => handleAction('clear')}
                                    disabled={!!actionLoading}
                                    className="w-full sm:w-auto px-16 py-6 bg-green-700 text-white font-grotesk font-black text-xs tracking-[0.4em] uppercase hover:bg-green-800 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[8px_8px_0px_rgba(0,0,0,0.1)] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                                >
                                    {actionLoading === 'clear' ? 'PROCESSING...' : 'CLEAR EVIDENCE & APPROVE'}
                                </button>
                                <button
                                    onClick={() => handleAction('blacklist')}
                                    disabled={!!actionLoading}
                                    className="w-full sm:w-auto px-16 py-6 bg-red-700 text-white font-grotesk font-black text-xs tracking-[0.4em] uppercase hover:bg-red-800 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[8px_8px_0px_rgba(0,0,0,0.1)] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                                >
                                    {actionLoading === 'blacklist' ? 'PROCESSING...' : 'CONFIRM FRAUD & BLACKLIST'}
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>

            <GridPlus className="fixed inset-0 pointer-events-none opacity-5 z-0" />
            <style>{`
                .custom-scrollbar-reviewer::-webkit-scrollbar { width: 6px; }
                .custom-scrollbar-reviewer::-webkit-scrollbar-thumb { background: #1c1c1c; border-radius: 10px; }
                .custom-scrollbar-reviewer::-webkit-scrollbar-track { background: rgba(0,0,0,0.05); }
            `}</style>
        </motion.div>
    );
}
