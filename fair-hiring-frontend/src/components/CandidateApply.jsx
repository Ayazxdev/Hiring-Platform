import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { createPortal } from 'react-dom';
import { api } from '../api/backend';

export default function CandidateApply({ roleId, roleData: propRoleData, onExit, onTakeTest, onComplete }) {
    // ... (state hooks remain the same)
    const [step, setStep] = useState('form');
    const [formData, setFormData] = useState({
        resume: null,
        githubUrl: '',
        leetcodeUser: '',
        codeforcesUser: '',
        linkedinUrl: '',
        linkedinPdf: null
    });
    const [uploading, setUploading] = useState(false);
    const [toggles, setToggles] = useState({
        leetcode: false,
        codeforces: false,
        linkedin: false
    });

    // Role data from props
    const roleData = {
        title: propRoleData?.title || 'Unknown Role',
        skills: propRoleData?.tags || []
    };

    const [applicationId, setApplicationId] = useState(null);
    const [pipelineStatus, setPipelineStatus] = useState(null);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setStep('submitting');

        const anonId = localStorage.getItem("fhn_candidate_anon_id");
        if (!anonId) {
            setStep('error');
            setError("You are not logged in as a candidate. Please login again.");
            return;
        }

        const formDataData = new FormData();
        formDataData.append('job_id', roleId);
        formDataData.append('anon_id', anonId);
        formDataData.append('resume', formData.resume);
        if (formData.githubUrl) formDataData.append('github', formData.githubUrl);
        if (formData.leetcodeUser) formDataData.append('leetcode', formData.leetcodeUser);
        if (formData.codeforcesUser) formDataData.append('codeforces', formData.codeforcesUser);
        if (formData.linkedinUrl) formDataData.append('linkedin_url', formData.linkedinUrl);
        if (formData.linkedinPdf) formDataData.append('linkedin_pdf', formData.linkedinPdf);

        try {
            const resp = await api.applyToJob(formDataData);
            setApplicationId(resp.application_id);
            setStep('processing');
            startPolling(resp.application_id);
        } catch (err) {
            console.error(err);
            setError(err?.message || "Application failed. Please try again.");
            setStep('error');
        }
    };

    const startPolling = (appId) => {
        // Smart polling: 3s -> 5s -> 10s -> 15s
        let attempt = 0;

        const poll = async () => {
            attempt++;

            try {
                const status = await api.getApplicationStatus(appId);
                setPipelineStatus(status);

                if (status.status === 'matched' || status.status === 'rejected' || status.status === 'failed') {
                    if (status.status === 'matched') setStep('success');
                    else if (status.status === 'rejected') setStep('rejected');
                    else setStep('error');
                    return; // Stop polling
                } else if (status.test_required) {
                    setStep('test_required');
                    return; // Stop polling
                }

                // Calculate next delay based on attempt count
                let delay = 3000; // Default 3s
                if (attempt > 3) delay = 5000;
                if (attempt > 6) delay = 10000;
                if (attempt > 10) delay = 15000;

                // Schedule next poll
                setTimeout(poll, delay);

            } catch (err) {
                console.error("Polling error:", err);
                // Retry with backoff even on error, but stop after too many failures
                if (attempt < 20) {
                    setTimeout(poll, 5000);
                } else {
                    setStep('error');
                    setError("Connection lost. Please refresh.");
                }
            }
        };

        // Start first poll
        poll();
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setUploading(true);
            setTimeout(() => {
                setFormData({ ...formData, resume: file });
                setUploading(false);
            }, 1500);
        }
    };

    return createPortal(
        <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ duration: 0.7, ease: [0.4, 0, 0.2, 1] }}
            className="fixed inset-0 z-[200] bg-[#E6E6E3] text-[#1c1c1c] overflow-y-auto selection:bg-black selection:text-white"
            style={{ isolation: 'isolate' }}
            data-lenis-prevent
        >
            {/* PERSISTENT HEADER */}
            {/* STICKY HEADER */}
            <header className="sticky top-0 left-0 w-full bg-[#E6E6E3] border-b-[3px] border-[#1c1c1c] z-[100] px-6 md:px-12 py-6 flex justify-between items-center bg-opacity-95 backdrop-blur-sm">
                <div className="flex items-center gap-6">
                    <button
                        onClick={onExit}
                        className="px-6 py-3 border-[2px] border-[#1c1c1c] font-grotesk text-[11px] font-black uppercase tracking-[0.2em] hover:bg-[#1c1c1c] hover:text-[#E6E6E3] transition-all flex items-center gap-2 group"
                    >
                        <span className="group-hover:-translate-x-1 transition-transform inline-block">←</span> [ ESCAPE ]
                    </button>
                    <div className="h-10 w-[2px] bg-[#1c1c1c]/10 hidden md:block"></div>
                    <span className="font-montreal font-black text-sm md:text-base tracking-[0.2em] uppercase text-[#1c1c1c]">
                        APPLICATION INTERFACE
                    </span>
                </div>
                <div className="font-grotesk text-[10px] font-black tracking-widest uppercase opacity-40">
                    ID: {roleId?.slice(0, 8) || 'REF-882'}
                </div>
            </header>

            <main className="max-w-[1440px] mx-auto px-6 md:px-12 pt-0 pb-20 min-h-screen">
                <AnimatePresence mode="wait">
                    {step === 'form' ? (
                        <motion.div
                            key="apply-form"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="space-y-16 relative"
                        >
                            <div className="absolute top-12 right-0 z-10">
                                <button
                                    onClick={onExit}
                                    className="bg-black text-white px-8 py-3 font-grotesk text-[10px] font-black uppercase tracking-[0.3em] hover:bg-black/90 transition-all shadow-[4px_4px_0px_#ccc] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
                                >
                                    BACK
                                </button>
                            </div>

                            {/* HERO SECTION */}
                            <section className="space-y-6 pb-12 border-b border-black/10">
                                <div className="space-y-4">
                                    <label className="font-grotesk text-xs uppercase opacity-100 font-black tracking-[0.3em] text-black">DESIGNATION TARGET</label>
                                    <h1 className="font-montreal font-black text-6xl md:text-9xl uppercase tracking-tighter leading-[0.85]">
                                        {roleData.title}
                                    </h1>
                                </div>
                                <div className="flex flex-wrap items-center gap-4 pt-4">
                                    <label className="font-grotesk text-[10px] uppercase opacity-60 font-black tracking-widest mr-4">CORE EXPECTATIONS</label>
                                    {roleData.skills.map(skill => (
                                        <span key={skill} className="px-5 py-2 border border-black font-grotesk text-[11px] font-black uppercase tracking-wider bg-black text-white shadow-[4px_4px_0px_rgba(0,0,0,0.1)]">
                                            {skill}
                                        </span>
                                    ))}
                                </div>
                            </section>

                            <form onSubmit={handleSubmit} className="space-y-24">
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 md:gap-24 items-start">
                                    {/* LEFT COLUMN: MANDATORY & PRIMARY */}
                                    <div className="space-y-16">
                                        <div className="space-y-12">
                                            <h2 className="font-montreal font-black text-4xl uppercase tracking-tighter border-b-4 border-black pb-2 inline-block">MANDATORY SIGNALS</h2>

                                            {/* RESUME */}
                                            <section className="space-y-6">
                                                <div className="flex justify-between items-baseline">
                                                    <label className="font-grotesk text-sm font-black uppercase text-black tracking-widest">01. RESUME (PDF ONLY)</label>
                                                    <span className="font-inter text-[10px] font-black uppercase opacity-60 text-black animate-pulse">REQUIRED</span>
                                                </div>
                                                <div className="relative group">
                                                    <input
                                                        type="file"
                                                        accept=".pdf"
                                                        onChange={handleFileChange}
                                                        className="absolute inset-0 opacity-0 cursor-pointer z-20"
                                                        required={!formData.resume}
                                                    />
                                                    <div className={`h-48 border-4 border-black ${formData.resume ? 'bg-black text-[#E6E6E3]' : 'bg-transparent hover:bg-black/10'} transition-all flex flex-col items-center justify-center p-8 text-center gap-4 relative z-10`}>
                                                        <div className="font-grotesk text-sm font-black uppercase tracking-[0.2em]">
                                                            {uploading ? 'UPLOADING...' : formData.resume ? `FILE: ${formData.resume.name}` : '+ SELECT PDF FILE'}
                                                        </div>
                                                        {!formData.resume && !uploading && (
                                                            <div className="font-inter text-[10px] font-black uppercase opacity-40">Drag PDF here or click to browse</div>
                                                        )}
                                                        {uploading && (
                                                            <div className="w-full max-w-[200px] h-[4px] bg-white/20 relative overflow-hidden">
                                                                <motion.div
                                                                    initial={{ x: '-100%' }}
                                                                    animate={{ x: '100%' }}
                                                                    transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                                                                    className="absolute inset-0 bg-white"
                                                                />
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </section>

                                            {/* GITHUB */}
                                            <section className="space-y-6">
                                                <div className="flex justify-between items-baseline">
                                                    <label className="font-grotesk text-sm font-black uppercase text-black tracking-widest">02. REPOSITORY ARCHIVE</label>
                                                    <span className="font-inter text-[10px] font-black uppercase opacity-60 text-black">REQUIRED</span>
                                                </div>
                                                <div className="space-y-4">
                                                    <div className="bg-red-500/20 border-l-4 border-red-800 p-4 mb-2">
                                                        <p className="font-inter text-[10px] font-black uppercase tracking-tight text-black flex items-center gap-2">
                                                            <span className="text-sm">ℹ️</span> 
                                                            IMPORTANT: Ensure all repositories you wish to be evaluated are set to PUBLIC.
                                                        </p>
                                                    </div>
                                                    <input
                                                        type="url"
                                                        placeholder="GITHUB.COM/USERNAME"
                                                        value={formData.githubUrl}
                                                        onChange={(e) => setFormData({ ...formData, githubUrl: e.target.value })}
                                                        className="w-full bg-transparent border-b-4 border-black py-6 font-montreal text-4xl md:text-5xl uppercase tracking-tighter focus:outline-none placeholder:text-black/10 transition-all font-black"
                                                        required
                                                    />
                                                    <p className="font-inter text-xs font-bold text-black opacity-60 leading-relaxed uppercase tracking-tight">
                                                        Our agents will audit your repositories for verified technical signatures.
                                                    </p>
                                                </div>
                                            </section>
                                        </div>

                                        {/* TRANSPARENCY BLOCK moved here for balance on desktop */}
                                        <section className="p-8 bg-black text-[#E6E6E3] space-y-6">
                                            <label className="font-grotesk text-xs uppercase opacity-100 font-black tracking-widest text-white border-b border-white/20 pb-2 flex items-center gap-3">
                                                <span className="w-2 h-2 bg-yellow-400 rounded-full" />
                                                EVALUATION PROTOCOL
                                            </label>
                                            <div className="grid grid-cols-1 gap-4">
                                                {[
                                                    'Primary focus on real project work',
                                                    'Skill-test results weighted heavily',
                                                    'Bias masking applied to all identifiers',
                                                    'Direct matching with team requirements',
                                                    'Zero-tolerance for bot-generated resumes'
                                                ].map(item => (
                                                    <div key={item} className="font-grotesk text-[10px] font-black uppercase tracking-widest flex items-start gap-4 opacity-70">
                                                        <span className="opacity-40">{'>'}</span>
                                                        {item}
                                                    </div>
                                                ))}
                                            </div>
                                        </section>
                                    </div>

                                    {/* RIGHT COLUMN: VERIFICATION & OPTIONAL */}
                                    <div className="space-y-16 lg:sticky lg:top-32">
                                        <div className="space-y-12">
                                            <h2 className="font-montreal font-black text-4xl uppercase tracking-tighter border-b-4 border-black pb-2 inline-block">VERIFICATION & SIGNALS</h2>

                                            {/* SKILL TEST CTA */}
                                            <section
                                                onClick={onTakeTest}
                                                className="group cursor-pointer bg-white border-4 border-black p-10 space-y-6 hover:bg-black hover:text-white transition-all transform hover:-translate-y-1 shadow-[8px_8px_0px_rgba(0,0,0,1)] hover:shadow-none"
                                            >
                                                <div className="flex justify-between items-start">
                                                    <div className="space-y-2">
                                                        <h3 className="font-montreal font-black text-3xl uppercase tracking-tight leading-none text-inherit">TECHNICAL ASSESSMENT</h3>
                                                        <p className="font-grotesk text-[10px] font-black uppercase tracking-widest opacity-60">Highly weighting: {roleData.skills[0]} logic</p>
                                                    </div>
                                                    <div className="bg-black text-white px-6 py-2 font-grotesk text-[10px] font-black uppercase tracking-widest transition-all shadow-[3px_3px_0px_#ccc] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none">
                                                        TAKE NOW
                                                    </div>
                                                </div>
                                                <p className="font-inter text-xs font-bold leading-relaxed opacity-80 uppercase tracking-tight">
                                                    Generated instant-assessment to verify your core logic and syntax accuracy.
                                                </p>
                                            </section>

                                            {/* OPTIONAL SIGNALS TOGGLES */}
                                            <section className="space-y-8">
                                                <div className="flex items-center justify-between border-b-2 border-black/5 pb-2">
                                                    <label className="font-grotesk text-sm font-black uppercase text-black tracking-[0.2em]">OPTIONAL EXTRA SIGNALS</label>
                                                    <span className="font-grotesk text-[9px] font-black uppercase opacity-40">SELECT TO ENABLE</span>
                                                </div>

                                                <div className="space-y-6">
                                                    {/* LeetCode Toggle */}
                                                    <div className="space-y-4">
                                                        <button
                                                            type="button"
                                                            onClick={() => setToggles(t => ({ ...t, leetcode: !t.leetcode }))}
                                                            className={`w-full flex justify-between items-center p-5 border-2 transition-all ${toggles.leetcode ? 'bg-black text-white border-black' : 'border-black/10 hover:border-black'}`}
                                                        >
                                                            <span className="font-grotesk font-black text-xs uppercase tracking-widest">LEETCODE PROFILE</span>
                                                            <span className="font-montreal font-black text-xl">{toggles.leetcode ? '-' : '+'}</span>
                                                        </button>
                                                        <AnimatePresence>
                                                            {toggles.leetcode && (
                                                                <motion.div
                                                                    initial={{ height: 0, opacity: 0 }}
                                                                    animate={{ height: 'auto', opacity: 1 }}
                                                                    exit={{ height: 0, opacity: 0 }}
                                                                    className="overflow-hidden"
                                                                >
                                                                    <div className="py-4 space-y-4">
                                                                        <input
                                                                            type="text"
                                                                            placeholder="USERNAME"
                                                                            value={formData.leetcodeUser}
                                                                            onChange={(e) => setFormData({ ...formData, leetcodeUser: e.target.value })}
                                                                            className="w-full bg-transparent border-b-2 border-black py-4 font-montreal text-2xl uppercase tracking-tight focus:outline-none placeholder:text-black/10 font-bold"
                                                                        />
                                                                    </div>
                                                                </motion.div>
                                                            )}
                                                        </AnimatePresence>
                                                    </div>

                                                    {/* Codeforces Toggle */}
                                                    <div className="space-y-4">
                                                        <button
                                                            type="button"
                                                            onClick={() => setToggles(t => ({ ...t, codeforces: !t.codeforces }))}
                                                            className={`w-full flex justify-between items-center p-5 border-2 transition-all ${toggles.codeforces ? 'bg-black text-white border-black' : 'border-black/10 hover:border-black'}`}
                                                        >
                                                            <span className="font-grotesk font-black text-xs uppercase tracking-widest">CODEFORCES ID</span>
                                                            <span className="font-montreal font-black text-xl">{toggles.codeforces ? '-' : '+'}</span>
                                                        </button>
                                                        <AnimatePresence>
                                                            {toggles.codeforces && (
                                                                <motion.div
                                                                    initial={{ height: 0, opacity: 0 }}
                                                                    animate={{ height: 'auto', opacity: 1 }}
                                                                    exit={{ height: 0, opacity: 0 }}
                                                                    className="overflow-hidden"
                                                                >
                                                                    <div className="py-4 space-y-4">
                                                                        <input
                                                                            type="text"
                                                                            placeholder="HANDLE"
                                                                            value={formData.codeforcesUser}
                                                                            onChange={(e) => setFormData({ ...formData, codeforcesUser: e.target.value })}
                                                                            className="w-full bg-transparent border-b-2 border-black py-4 font-montreal text-2xl uppercase tracking-tight focus:outline-none placeholder:text-black/10 font-bold"
                                                                        />
                                                                    </div>
                                                                </motion.div>
                                                            )}
                                                        </AnimatePresence>
                                                    </div>

                                                    {/* LinkedIn Toggle */}
                                                    <div className="space-y-4">
                                                        <button
                                                            type="button"
                                                            onClick={() => setToggles(t => ({ ...t, linkedin: !t.linkedin }))}
                                                            className={`w-full flex justify-between items-center p-5 border-2 transition-all ${toggles.linkedin ? 'bg-black text-white border-black' : 'border-black/10 hover:border-black'}`}
                                                        >
                                                            <span className="font-grotesk font-black text-xs uppercase tracking-widest">LINKEDIN PROFILE</span>
                                                            <span className="font-montreal font-black text-xl">{toggles.linkedin ? '-' : '+'}</span>
                                                        </button>
                                                        <AnimatePresence>
                                                            {toggles.linkedin && (
                                                                <motion.div
                                                                    initial={{ height: 0, opacity: 0 }}
                                                                    animate={{ height: 'auto', opacity: 1 }}
                                                                    exit={{ height: 0, opacity: 0 }}
                                                                    className="overflow-hidden"
                                                                >
                                                                    <div className="py-4 space-y-4">
                                                                        <div className="space-y-2">
                                                                            <label className="font-grotesk text-[10px] font-black uppercase tracking-widest opacity-40 block">
                                                                                PUBLIC PROFILE URL
                                                                            </label>
                                                                            <div className="relative">
                                                                                <input
                                                                                    type="url"
                                                                                    placeholder="https://www.linkedin.com/in/username"
                                                                                    value={formData.linkedinUrl}
                                                                                    onChange={(e) => setFormData({ ...formData, linkedinUrl: e.target.value })}
                                                                                    className="w-full bg-white border-2 border-black p-4 font-grotesk text-xs tracking-wider outline-none focus:bg-black focus:text-white transition-colors"
                                                                                />
                                                                            </div>
                                                                        </div>
                                                                        <div className="flex items-center gap-2">
                                                                            <span className="w-2 h-2 bg-[#0077B5] rounded-full inline-block animate-pulse shrink-0" />
                                                                            <p className="font-inter text-[10px] font-bold uppercase opacity-60">
                                                                                Automated profile scraping via Bright Data residential proxy network.
                                                                            </p>
                                                                        </div>
                                                                    </div>
                                                                </motion.div>
                                                            )}
                                                        </AnimatePresence>
                                                    </div>
                                                </div>
                                            </section>
                                        </div>

                                        {/* CENTERED SUBMIT BUTTON */}
                                        <div className="mt-24 pt-12 border-t-8 border-black flex justify-center">
                                            <button
                                                type="submit"
                                                className="w-full md:max-w-xl py-8 bg-black text-white border border-black font-grotesk font-black text-xl tracking-[0.4em] uppercase hover:bg-white hover:text-black transition-all shadow-[6px_6px_0px_#ccc] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none disabled:opacity-50 mb-24"
                                            >
                                                PUSH APPLICATION
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </form>
                        </motion.div>
                    ) : (step === 'processing' || step === 'submitting') ? (
                        <motion.div
                            key="processing-state"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="h-[80vh] flex flex-col items-center justify-center p-12"
                        >
                            <div className="w-full max-w-4xl space-y-20">
                                <div className="space-y-4 text-center">
                                    <h2 className="font-montreal font-black text-6xl uppercase tracking-tighter">
                                        EVALUATION IN PROGRESS
                                    </h2>
                                    <p className="font-grotesk text-sm font-black uppercase tracking-[0.3em] opacity-40">
                                        STAGE: {pipelineStatus?.current_stage || 'INITIALIZING'}
                                    </p>
                                </div>

                                {/* Progress Bar */}
                                <div className="space-y-4">
                                    <div className="flex justify-between font-grotesk text-[10px] font-black uppercase tracking-widest">
                                        <span>SIGNAL STRENGTH: {pipelineStatus?.progress_percentage || 0}%</span>
                                        <span>STATUS: {pipelineStatus?.status || 'PENDING'}</span>
                                    </div>
                                    <div className="h-4 border-2 border-black bg-white p-1">
                                        <motion.div
                                            className="h-full bg-black"
                                            initial={{ width: 0 }}
                                            animate={{ width: `${pipelineStatus?.progress_percentage || 0}%` }}
                                            transition={{ duration: 0.5 }}
                                        />
                                    </div>
                                </div>

                                {/* Stages Grid */}
                                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                    {(() => {
                                        const baseStages = ['ATS', 'SKILL', 'BIAS', 'MATCHING', 'PASSPORT'];
                                        if (formData.githubUrl) baseStages.splice(1, 0, 'GITHUB');
                                        if (formData.leetcodeUser) baseStages.splice(2, 0, 'LEETCODE');
                                        if (formData.codeforcesUser) baseStages.splice(3, 0, 'CODEFORCES');
                                        if (formData.linkedinPdf) baseStages.splice(4, 0, 'LINKEDIN');

                                        // If test required, it becomes a stage
                                        if (pipelineStatus?.test_required) baseStages.splice(baseStages.indexOf('SKILL') + 1, 0, 'TEST');

                                        return baseStages.map((s, i) => {
                                            const isCompleted = pipelineStatus?.stages_completed?.includes(s);
                                            const isCurrent = pipelineStatus?.current_stage === s;
                                            return (
                                                <div key={s} className={`p-4 border-2 border-black flex flex-col items-center justify-center gap-2 transition-all ${isCompleted ? 'bg-black text-white' : isCurrent ? 'bg-white animate-pulse' : 'bg-transparent opacity-20'}`}>
                                                    <span className="font-grotesk text-[8px] font-black">{s}</span>
                                                    {isCompleted && <span className="text-[10px]">✓</span>}
                                                </div>
                                            );
                                        });
                                    })()}
                                </div>

                                {pipelineStatus?.evidence && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className="p-8 border-4 border-black bg-white shadow-[8px_8px_0px_#000] space-y-6"
                                    >
                                        <div className="flex justify-between items-center border-b border-black/10 pb-2">
                                            <label className="font-grotesk text-[10px] font-black uppercase tracking-widest block">AGENT EVIDENCE STREAM</label>
                                            <span className="font-grotesk text-[8px] opacity-40 uppercase">Decentralized Verification</span>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                            <div className="space-y-4">
                                                <h4 className="font-montreal font-black text-xs uppercase tracking-widest opacity-60">Verified Technical Depth</h4>
                                                <div className="flex flex-wrap gap-2">
                                                    {(pipelineStatus.evidence.skills?.skills || pipelineStatus.credential_preview?.skills || []).slice(0, 12).map(skill => (
                                                        <span key={skill} className="px-3 py-1 bg-black text-white font-grotesk text-[9px] font-black uppercase">{skill}</span>
                                                    ))}
                                                </div>
                                            </div>

                                            <div className="space-y-4">
                                                <h4 className="font-montreal font-black text-xs uppercase tracking-widest opacity-60">Factual Signal Log</h4>
                                                <div className="space-y-2 max-h-[150px] overflow-y-auto pr-2 custom-scrollbar-light">
                                                    {pipelineStatus.evidence.ats && (
                                                        <div className="flex justify-between text-[10px] font-bold uppercase border-b border-black/5 pb-1">
                                                            <span>RESUME_EVAL</span>
                                                            <span className="text-green-600">PROCESSED</span>
                                                        </div>
                                                    )}
                                                    {pipelineStatus.evidence.github && (
                                                        <div className="flex justify-between text-[10px] font-bold uppercase border-b border-black/5 pb-1">
                                                            <span>REPO_AUDIT</span>
                                                            <span className="text-green-600">VERIFIED</span>
                                                        </div>
                                                    )}
                                                    {pipelineStatus.evidence.matching && (
                                                        <div className="flex justify-between text-[10px] font-bold uppercase border-b border-black/5 pb-1">
                                                            <span>ROLE_ALIGNMENT</span>
                                                            <span>{pipelineStatus.match_score || 0}%</span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </div>
                        </motion.div>
                    ) : step === 'test_required' ? (
                        <motion.div
                            key="test-required"
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            className="h-[80vh] flex flex-col items-center justify-center space-y-12"
                        >
                            <div className="max-w-2xl text-center space-y-8 p-12 border-4 border-black bg-white shadow-[12px_12px_0px_#000]">
                                <h1 className="font-montreal font-black text-5xl uppercase tracking-tighter">TEST REQUIRED</h1>
                                <p className="font-inter text-sm font-bold uppercase leading-relaxed text-black/60">
                                    Our agents have verified your core profile but require additional logic evidence to complete the skill passport.
                                </p>
                                <button
                                    onClick={() => onTakeTest(applicationId)}
                                    className="w-full py-6 bg-black text-white font-grotesk font-black text-lg tracking-[0.3em] uppercase hover:bg-white hover:text-black transition-all border-2 border-black"
                                >
                                    START ASSESSMENT
                                </button>
                            </div>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="status-final"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="h-[80vh] flex flex-col items-center justify-center space-y-12 text-center"
                        >
                            <div className={`w-32 h-32 border-4 border-black flex items-center justify-center text-4xl font-black ${step === 'success' ? 'bg-green-400' : 'bg-red-400'}`}>
                                {step === 'success' ? '✓' : '!'}
                            </div>
                            <div className="space-y-4">
                                <h2 className="font-montreal font-black text-6xl uppercase tracking-tighter">
                                    {step === 'success' ? 'MATCH CONFIRMED' : step === 'rejected' ? 'REJECTED' : 'SYSTEM ERROR'}
                                </h2>
                                <p className="font-grotesk text-sm font-black opacity-40 uppercase tracking-[0.3em]">
                                    {step === 'success'
                                        ? 'Identity verified. Credentials issued.'
                                        : step === 'rejected'
                                            ? (pipelineStatus?.pipeline_error || 'Application did not meet system thresholds.')
                                            : 'An internal processing error occurred.'}
                                </p>
                                <button
                                    onClick={onComplete}
                                    className="px-12 py-4 border-4 border-black font-grotesk font-black text-xs uppercase tracking-widest mt-8 hover:bg-black hover:text-white transition-all shadow-[6px_6px_0px_#ccc] active:translate-x-[2px] active:translate-y-[2px]"
                                >
                                    RETURN TO DASHBOARD
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>

            <style>{`
                input::placeholder { opacity: 0.3; color: black; }
            `}</style>
        </motion.div >,
        document.body
    );
}
