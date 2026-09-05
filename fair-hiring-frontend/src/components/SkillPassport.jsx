import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
    BarChart,
    Bar,
    XAxis,
    Tooltip,
    ResponsiveContainer,
    Cell,
} from "recharts";
import GridPlus from "./GridPlus";
import { api } from "../api/backend";


const SkillDetailCard = ({ skill, onClose }) => {
    if (!skill) return null;

    const getConfidenceRange = (confidence) => {
        if (confidence >= 0 && confidence <= 20) return "0-20";
        if (confidence >= 21 && confidence <= 40) return "21-40";
        if (confidence >= 41 && confidence <= 60) return "41-60";
        if (confidence >= 61 && confidence <= 80) return "61-80";
        if (confidence >= 81 && confidence <= 100) return "81-100";
        return "";
    };

    const userRange = getConfidenceRange(skill.confidence);

    useEffect(() => {
        // Prevent body scroll when modal is open
        const originalStyle = window.getComputedStyle(document.body).overflow;
        document.body.style.overflow = "hidden";
        window.dispatchEvent(new CustomEvent('modal-state-change', { detail: { open: true } }));
        return () => {
            document.body.style.overflow = originalStyle;
            window.dispatchEvent(new CustomEvent('modal-state-change', { detail: { open: false } }));
        };
    }, []);

    // Helper to render skill categories
    const renderSkillCategory = (label, skills) => {
        if (!skills || skills.length === 0) return null;
        return (
            <div className="space-y-3">
                <label className="font-grotesk text-[9px] uppercase opacity-40 tracking-widest font-black text-black">
                    {label}
                </label>
                <div className="flex flex-wrap gap-2">
                    {skills.map((s, i) => {
                        const name = typeof s === 'string' ? s : s.name;
                        const score = typeof s === 'object' ? s.score : null;
                        return (
                            <div key={i} className="flex items-center gap-1.5 px-3 py-1.5 bg-black/5 border border-black/10 rounded-full group/chip hover:bg-black hover:text-white transition-all duration-300">
                                <span className="font-inter text-[10px] font-bold uppercase tracking-tight">
                                    {name}
                                </span>
                                {score !== undefined && score !== null && (
                                    <span className="font-grotesk text-[8px] font-black opacity-40 group-hover/chip:opacity-100">
                                        {score}%
                                    </span>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    };

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-black text-white px-3 py-2 rounded-lg shadow-2xl border border-white/10 backdrop-blur-md">
                    <p className="font-grotesk text-[10px] font-black uppercase tracking-widest mb-1">{payload[0].payload.range} Range</p>
                    <p className="font-inter text-[14px] font-bold">{payload[0].value} Candidates</p>
                </div>
            );
        }
        return null;
    };

    return createPortal(
        <div
            className="fixed inset-0 z-[1000] bg-black/60 backdrop-blur-md overflow-y-auto no-scrollbar scroll-smooth"
            onClick={onClose}
            data-lenis-prevent
        >
            <div className="min-h-full flex items-center justify-center p-4 md:p-12">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                    className="relative bg-[#FFFFFF] text-[#1c1c1c] w-full max-w-2xl shadow-[0_48px_100px_rgba(0,0,0,0.3)] flex flex-col overflow-hidden rounded-[2.5rem] border-8 border-black/5"
                    style={{ pointerEvents: "auto" }}
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Badge Vibe Header */}
                    <div className="bg-black text-white p-8 md:p-12 space-y-6 relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -mr-32 -mt-32 blur-3xl"></div>
                        <div className="flex justify-between items-start relative z-10">
                            <h2 className="font-montreal font-black text-4xl md:text-6xl uppercase tracking-tighter leading-none">
                                {skill.id}
                            </h2>
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                                <span className="font-grotesk text-[9px] font-black uppercase tracking-[0.4em] opacity-60">Verified Credential</span>
                            </div>
                            <button
                                onClick={onClose}
                                className="w-12 h-12 border border-white/20 rounded-full flex items-center justify-center font-bold hover:bg-white hover:text-black transition-all text-xl"
                            >
                                ✕
                            </button>
                        </div>
                        <div className="flex flex-wrap gap-8 md:gap-16 relative z-10 pt-4">
                            <div>
                                <label className="block font-grotesk text-[8px] uppercase opacity-40 tracking-widest font-black mb-1">CANDIDATE ID</label>
                                <span className="font-inter text-sm font-bold tracking-tight uppercase">{skill.candidateId || "ANON-USER"}</span>
                            </div>
                            <div>
                                <label className="block font-grotesk text-[8px] uppercase opacity-40 tracking-widest font-black mb-1">ISSUED DATE</label>
                                <span className="font-inter text-sm font-bold tracking-tight">{new Date(skill.issuedAt).toLocaleDateString('en-GB')}</span>
                            </div>
                        </div>
                    </div>

                    <div className="p-8 md:p-12 space-y-10">
                        {/* Summary Section */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                            <div className="space-y-2">
                                <label className="font-grotesk text-[10px] uppercase opacity-100 tracking-widest font-black text-black">
                                    CONFIDENCE SCORE
                                </label>
                                <div className="flex items-baseline gap-3">
                                    <div className="font-montreal font-black text-7xl md:text-8xl uppercase tracking-tighter">
                                        {skill.confidence}%
                                    </div>
                                    <span className="font-grotesk text-xs font-black uppercase tracking-widest opacity-40">VERIFIED</span>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <label className="font-grotesk text-[10px] uppercase opacity-100 tracking-widest font-black text-black">
                                    DISTRIBUTION
                                </label>
                                <div className="h-24 w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart
                                            data={skill.distribution}
                                            margin={{ top: 0, right: 0, left: -40, bottom: 0 }}
                                        >
                                            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.05)' }} />
                                            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                                                {skill.distribution?.map((entry, index) => (
                                                    <Cell
                                                        key={`cell-${index}`}
                                                        fill={"#1c1c1c"}
                                                        fillOpacity={entry.range === userRange ? 1 : 0.15}
                                                        className="transition-all duration-300 hover:fill-opacity-100 cursor-pointer"
                                                    />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>

                        {/* Skills Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 py-10 border-y border-black/5">
                            <div className="space-y-8">
                                {renderSkillCategory("Core Languages", skill.verifiedSkills?.core)}
                                {renderSkillCategory("Frameworks & Libs", skill.verifiedSkills?.frameworks)}
                            </div>
                            <div className="space-y-8">
                                {renderSkillCategory("Infrastructure", skill.verifiedSkills?.infrastructure)}
                                {renderSkillCategory("Tools & Others", skill.verifiedSkills?.tools)}
                            </div>
                        </div>

                        {/* Footer / Action */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                            <div className="space-y-1.5 p-5 bg-black/5 rounded-3xl border border-black/5">
                                <label className="block font-grotesk text-[9px] uppercase opacity-40 tracking-widest font-black">VALID UNTIL</label>
                                <span className="font-inter text-sm font-bold tracking-tight">{new Date(skill.expiresAt).toLocaleDateString('en-GB')}</span>
                            </div>
                            <div className="space-y-1.5 p-5 bg-black/5 rounded-3xl border border-black/5">
                                <label className="block font-grotesk text-[9px] uppercase opacity-40 tracking-widest font-black">QUALIFICATION</label>
                                <span className={`font-inter text-sm font-bold tracking-tight uppercase ${skill.status === 'PENDING_TEST' ? 'text-amber-600' : 'text-emerald-700'}`}>
                                    {skill.status === 'PENDING_TEST' ? 'CONDITIONAL (TEST PENDING)' : skill.status}
                                </span>
                                {skill.status === 'PENDING_TEST' && (
                                    <span className="block text-[8px] text-black/50 font-normal leading-tight">
                                        Self-attested claims awaiting targeted assessment
                                    </span>
                                )}
                            </div>
                        </div>

                        <button
                            onClick={onClose}
                            className="w-full py-6 bg-[#1c1c1c] text-white rounded-2xl font-grotesk font-black text-[10px] tracking-[0.4em] uppercase hover:bg-black transition-all shadow-xl hover:shadow-2xl active:scale-[0.98]"
                        >
                            CLOSE CREDENTIAL
                        </button>
                    </div>
                </motion.div>
            </div>
        </div>,
        document.body,
    );
};

const SkillPassport = ({ isStandalone = false, onBack, candidateId }) => {
    const [selectedSkill, setSelectedSkill] = useState(null);
    const [passportSkills, setPassportSkills] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const anon = candidateId || localStorage.getItem("fhn_candidate_anon_id");
        console.group("SkillPassport Diagnostic");
        console.log("Current ID:", anon);

        const transformCredential = (existingData) => {
            const cred = existingData?.credential || existingData?.credential_json || existingData;
            const derived = cred?.derived || {};
            const passportEvidence = cred?.evidence?.passport || {};
            const skillsEvidence =
                cred?.evidence?.skills?.data?.output?.output ||
                cred?.evidence?.skills?.output?.output ||
                cred?.evidence?.skills?.data?.output ||
                cred?.evidence?.skills?.output ||
                cred?.evidence?.skills ||
                {};

            // Extract verified_skills from multiple possible locations
            let existingSkills =
                cred?.verified_skills ||
                derived?.verified_skills ||
                passportEvidence?.verified_skills ||
                skillsEvidence?.verified_skills ||
                { core: [], frameworks: [], infrastructure: [], tools: [] };

            // Handle flat list format if it's not a tiered object
            let verifiedSkills = {
                core: [],
                frameworks: [],
                infrastructure: [],
                tools: []
            };

            if (Array.isArray(existingSkills)) {
                // Heuristic categorization for flat list
                existingSkills.forEach(s => {
                    const name = typeof s === 'string' ? s : (s.skill || s.name || "");
                    const lower = name.toLowerCase();
                    if (["react", "next.js", "django", "flask", "node.js", "express", "tensorflow", "opencv", "fastapi"].some(fw => lower.includes(fw))) {
                        verifiedSkills.frameworks.push(s);
                    } else if (["aws", "docker", "kubernetes", "cloud", "infra", "lambda", "sagemaker"].some(inf => lower.includes(inf))) {
                        verifiedSkills.infrastructure.push(s);
                    } else if (["git", "github", "vs code", "jira", "grafana", "jupyter", "visual studio"].some(t => lower.includes(t))) {
                        verifiedSkills.tools.push(s);
                    } else {
                        verifiedSkills.core.push(s);
                    }
                });
            } else if (typeof existingSkills === 'object' && existingSkills !== null) {
                verifiedSkills = {
                    core: existingSkills.core || [],
                    frameworks: existingSkills.frameworks || [],
                    infrastructure: existingSkills.infrastructure || [],
                    tools: existingSkills.tools || []
                };
            }

            // Extract match score — this is the primary CONFIDENCE SCORE shown on the passport
            const matchingEvidence = cred?.evidence?.matching;
            const matchScore =
                derived?.match_score ||
                matchingEvidence?.match_score ||
                matchingEvidence?.data?.match_score ||
                matchingEvidence?.data?.output?.match_score ||
                0;

            // skill_confidence is the portfolio signal score (internal, not shown as main confidence)
            const confidence = matchScore || derived?.confidence || derived?.skill_confidence || skillsEvidence?.skill_confidence || 0;

            // Extract status
            const pipelineStatus = cred?.pipeline_status || cred?.application_status || "";
            const credStatus =
                derived?.credential_status ||
                skillsEvidence?.credential_status ||
                (pipelineStatus === "completed" || cred?.stages_completed?.includes("PASSPORT") ? "VERIFIED" : pipelineStatus.toUpperCase()) ||
                "VERIFIED";

            // Extract issued date
            const issuedAt =
                passportEvidence?.issued_at ||
                cred?.started_at ||
                existingData?.issued_at ||
                new Date().toISOString();

            return {
                id: cred?.credential_id || existingData?.application_id
                    ? `PASSPORT-${existingData?.application_id || cred?.credential_id || 'UNKNOWN'}`
                    : `PASSPORT-UNKNOWN`,
                candidateId: existingData?.anon_id || cred?.candidate_id || anon,
                confidence: confidence,
                matchScore: matchScore,
                verifiedSkills: verifiedSkills,
                status: credStatus,
                issuedAt: issuedAt,
                expiresAt: (() => {
                    const d = new Date(issuedAt);
                    d.setFullYear(d.getFullYear() + 1);
                    return d.toISOString();
                })(),
                distribution: [
                    { range: "0-20", count: 5 }, { range: "21-40", count: 12 }, { range: "41-60", count: 18 },
                    { range: "61-80", count: 22 }, { range: "81-100", count: 9 },
                ],
                verified: existingData?.verified || false,
                signatureB64: existingData?.signature_b64 || "",
                hashSha256: existingData?.hash_sha256 || "",
            };
        };

        (async () => {
            if (!anon || anon === "ANON-UNSET") {
                console.warn("No valid ID found.");
                setPassportSkills([]);
                setIsLoading(false);
                console.groupEnd();
                return;
            }

            try {
                const result = await api.getPassport(anon);
                console.log("API Result type:", typeof result, Array.isArray(result));
                console.log("API Result:", JSON.stringify(result)?.substring(0, 500));

                let items = [];
                if (Array.isArray(result)) {
                    items = result;
                } else if (result?.credentials && Array.isArray(result.credentials)) {
                    items = result.credentials;
                } else if (result && (result.credential || result.credential_json || result.anon_id)) {
                    items = [result];
                }

                if (items.length > 0) {
                    const mapped = items.map(transformCredential);
                    console.log("Mapped credentials:", mapped);
                    setPassportSkills(mapped);
                } else {
                    console.warn("No credentials found in response");
                    setPassportSkills([]);
                }
            } catch (e) {
                console.error("Fetch failure:", e);
                setPassportSkills([]);
            } finally {
                setIsLoading(false);
                console.groupEnd();
            }
        })();
    }, [candidateId]);

    const pageTransition = {
        initial: { x: 20, opacity: 0 },
        animate: { x: 0, opacity: 1 },
        exit: { x: -20, opacity: 0 },
        transition: { duration: 0.5, ease: [0.4, 0, 0.2, 1] },
    };

    return (
        <motion.div
            key="passport"
            initial={isStandalone ? { opacity: 0 } : { x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -20, opacity: 0 }}
            transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
            className={`w-full space-y-8 text-[#1c1c1c] ${isStandalone ? 'max-w-[1280px] mx-auto px-6 md:px-12 py-12 min-h-screen bg-[#E6E6E3]' : ''}`}
        >
            {isStandalone && (
                <div className="flex flex-col mb-12 border-b-2 border-black/10 pb-6 relative">
                    <span className="font-grotesk text-[9px] md:text-[10px] font-black uppercase tracking-[0.4em] text-black opacity-40 mb-1">FAIR HIRING NETWORK</span>
                    <h1 className="font-montreal font-black text-xs md:text-sm uppercase tracking-[0.2em] text-black">CREDENTIAL PASSPORT</h1>
                    {candidateId && (
                        <div className="absolute top-0 right-0 font-grotesk text-[9px] md:text-[10px] font-black uppercase tracking-widest text-black/40">
                            ID: {candidateId}
                        </div>
                    )}
                </div>
            )}

            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                <div className="space-y-2">
                    <h2 className="font-montreal font-black text-4xl md:text-7xl uppercase tracking-tighter leading-none text-[#1c1c1c]">
                        CREDENTIAL PASSPORT
                    </h2>
                    <p className="font-inter text-[10px] md:text-sm opacity-100 font-bold max-w-lg uppercase tracking-tight text-[#1c1c1c]">
                        {passportSkills.length === 1 ? `ID: ${passportSkills[0].id} • Authenticated Technical Credential` : "Authenticated technical signatures · Verifiable ownership"}
                    </p>
                </div>
            </div>

            <div className="border-t border-[#1c1c1c]/15">
                {isLoading ? (
                    <div className="py-24 text-center">
                        <div className="font-grotesk text-[10px] font-black uppercase tracking-[0.5em] animate-pulse">Retrieving Authenticated Signatures...</div>
                    </div>
                ) : passportSkills.length > 0 ? (
                    passportSkills.map((skill, idx) => (
                        <div key={skill.id || `skill-${idx}`} className="relative group/skill">
                            <button
                                onClick={() => setSelectedSkill(skill)}
                                className="w-full text-left group flex flex-col md:flex-row border-b border-[#1c1c1c]/15 py-8 md:py-12 items-start md:items-center justify-between hover:bg-black/5 transition-all duration-500 px-4 -mx-4 cursor-pointer gap-6 md:gap-0"
                            >
                                <div className="space-y-2">
                                    <label className="font-grotesk text-[9px] font-black uppercase tracking-[0.3em] text-black/30">CREDENTIAL ID</label>
                                    <h3 className="font-montreal font-black text-4xl md:text-5xl uppercase tracking-tight group-hover:translate-x-4 transition-transform duration-700 text-[#1c1c1c]">
                                        {skill.id}
                                    </h3>
                                    <p className="font-inter text-[10px] md:text-sm uppercase tracking-[0.2em] opacity-100 font-black text-black">
                                        Verified technical signature · {skill.confidence}% confidence
                                    </p>
                                </div>
                                <div className="bg-black text-white px-10 py-4 font-grotesk text-[10px] font-black uppercase tracking-[0.4em] hover:bg-black/90 transition-all shadow-[6px_6px_0px_#ccc] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none w-full md:w-auto text-center">
                                    VIEW DETAILS →
                                </div>
                            </button>
                        </div>
                    ))
                ) : (
                    <div className="py-24 text-center space-y-6">
                        <div className="font-montreal font-black text-3xl uppercase opacity-20">NO CREDENTIALS ISSUED</div>
                        <p className="font-grotesk text-[9px] font-black uppercase tracking-[0.2em] opacity-40 max-w-xs mx-auto text-center">
                            Ensure you are logged in with a valid candidate ID.
                            <br />
                            Current ID Session: <span className="text-black/80">{candidateId || localStorage.getItem("fhn_candidate_anon_id") || "None Detected"}</span>
                        </p>
                    </div>
                )}
            </div>

            {isStandalone && (
                <div className="mt-12 pt-12 border-t border-black/10 text-center">
                    <div className="font-grotesk text-[9px] font-black uppercase tracking-[0.3em] opacity-30 text-black">
                        Secure NFC Access · Verification ID: {candidateId || 'LIVE'}
                    </div>
                </div>
            )}

            {/* SKILL DETAIL MODAL */}
            <AnimatePresence>
                {selectedSkill && (
                    <SkillDetailCard
                        skill={selectedSkill}
                        onClose={() => setSelectedSkill(null)}
                    />
                )}
            </AnimatePresence>

            <style>{`
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>

            {isStandalone && <GridPlus className="fixed inset-0 pointer-events-none opacity-5 z-[-1]" />}
        </motion.div>
    );
};

export default SkillPassport;
