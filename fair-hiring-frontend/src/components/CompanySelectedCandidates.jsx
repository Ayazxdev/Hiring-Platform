import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import GridPlus from './GridPlus';

const MOCK_SELECTED = [
    {
        id: 'C-7729',
        name: 'Alex Rivera',
        score: 94,
        skills: ['React', 'TypeScript', 'Node.js'],
        biasStatus: 'Passed',
        summary: 'Demonstrated exceptional architectural thinking and deep understanding of state management patterns.',
        unlocked: true
    },
    {
        id: 'C-4421',
        name: 'Jordan Smith',
        score: 91,
        skills: ['Next.js', 'PostgreSQL', 'AWS'],
        biasStatus: 'Passed',
        summary: 'Strong full-stack capabilities with a focus on scalable infrastructure and performance optimization.',
        unlocked: true
    }
];

export default function CompanySelectedCandidates({ roleId, onBack }) {
    const [candidates] = useState(MOCK_SELECTED);
    const [expandedId, setExpandedId] = useState(null);

    const toggleExpand = (id) => {
        setExpandedId(expandedId === id ? null : id);
    };

    return (
        <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.7, ease: [0.4, 0, 0.2, 1] }}
            className="fixed inset-0 z-[180] bg-[#E6E6E3] text-[#1c1c1c] overflow-y-auto flex flex-col"
            style={{ willChange: 'transform' }}
            data-lenis-prevent
        >
            {/* STICKY HEADER */}
            <header className="sticky top-0 left-0 w-full bg-[#E6E6E3] border-b-[3px] border-[#1c1c1c] z-50 px-6 md:px-12 py-5 flex justify-between items-center bg-opacity-95 backdrop-blur-sm flex-shrink-0">
                <div className="flex items-center gap-6">
                    <button
                        onClick={onBack}
                        className="px-6 py-3 border-[2px] border-[#1c1c1c] font-grotesk text-[10px] font-black uppercase tracking-[0.2em] hover:bg-[#1c1c1c] hover:text-[#E6E6E3] transition-all flex items-center gap-2 group"
                    >
                        <span className="group-hover:-translate-x-1 transition-transform inline-block">←</span> BACK
                    </button>
                    <div className="h-10 w-[2px] bg-[#1c1c1c]/10 hidden md:block"></div>
                    <span className="font-montreal font-black text-sm tracking-[0.2em] uppercase text-[#1c1c1c]">
                        SELECTED SHORTLIST
                    </span>
                </div>
                <div className="font-mono text-[9px] font-black opacity-30 uppercase tracking-widest">
                    ROLE REF: {roleId || 'R-101'}
                </div>
            </header>

            <main className="flex-1 max-w-[1280px] mx-auto px-6 md:px-12 py-12 w-full space-y-10">
                <div className="space-y-3">
                    <h1 className="font-montreal font-black text-4xl md:text-5xl uppercase tracking-tighter leading-tight">
                        IDENTIFIED <br />CAPABILITY
                    </h1>
                    <p className="font-inter text-[10px] font-bold opacity-40 uppercase tracking-[0.2em]">
                        {candidates.length} VERIFIED CANDIDATES READY FOR ENGAGEMENT
                    </p>
                </div>

                <div className="space-y-4">
                    {candidates.map((candidate) => (
                        <div
                            key={candidate.id}
                            className={`bg-white border-[2px] border-[#1c1c1c] transition-all duration-300 ${expandedId === candidate.id ? 'shadow-[12px_12px_0px_rgba(0,0,0,0.05)]' : 'hover:bg-[#F9F9F7] shadow-[4px_4px_0px_rgba(0,0,0,0.02)]'}`}
                        >
                            {/* ROW HEADER - CLICKABLE */}
                            <div
                                onClick={() => toggleExpand(candidate.id)}
                                className="p-6 md:p-8 flex items-center justify-between cursor-pointer"
                            >
                                <div className="flex items-center gap-8 md:gap-16">
                                    <div className="space-y-1">
                                        <span className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-30">CANDIDATE ID</span>
                                        <div className="font-montreal font-black text-xl uppercase tracking-tight">{candidate.id}</div>
                                    </div>
                                    <div className="space-y-1">
                                        <span className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-30">IDENTITY</span>
                                        <div className="font-montreal font-black text-xl uppercase text-[#1c1c1c]">{candidate.name}</div>
                                    </div>
                                    <div className="hidden md:block space-y-1">
                                        <span className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-30">SCORE</span>
                                        <div className="font-montreal font-black text-xl">{candidate.score}%</div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-4">
                                    <span className="px-3 py-1 bg-green-600 text-white font-grotesk text-[8px] font-black uppercase tracking-widest rounded-[2px]">BIAS PASSED</span>
                                    <div className={`text-2xl transition-transform duration-300 ${expandedId === candidate.id ? 'rotate-180' : ''}`}>↓</div>
                                </div>
                            </div>

                            {/* EXPANDABLE DETAILS */}
                            <AnimatePresence>
                                {expandedId === candidate.id && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: "auto", opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.4, ease: "circOut" }}
                                        className="overflow-hidden border-t-[2px] border-[#1c1c1c]"
                                    >
                                        <div className="p-8 md:p-12 grid grid-cols-1 lg:grid-cols-2 gap-12 bg-[#F9F9F7]/50">
                                            <div className="space-y-8">
                                                <div className="space-y-4">
                                                    <span className="font-grotesk text-[10px] font-black uppercase tracking-widest opacity-40 text-[#1c1c1c]">CORE REPERTOIRE</span>
                                                    <div className="flex flex-wrap gap-2">
                                                        {candidate.skills.map(skill => (
                                                            <span key={skill} className="px-4 py-2 bg-[#1c1c1c] text-white font-grotesk text-[9px] font-black uppercase tracking-widest">
                                                                {skill}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                                <div className="space-y-4">
                                                    <span className="font-grotesk text-[10px] font-black uppercase tracking-widest opacity-40 text-[#1c1c1c]">TALENT SUMMARY</span>
                                                    <p className="font-inter text-sm font-bold leading-relaxed text-[#1c1c1c]/80 italic border-l-4 border-[#1c1c1c] pl-6 bg-white/50 py-4">
                                                        “{candidate.summary}”
                                                    </p>
                                                </div>
                                            </div>

                                            <div className="flex flex-col justify-end gap-4">
                                                <button className="w-full px-10 py-6 bg-[#1c1c1c] text-white font-grotesk font-black text-xs tracking-[0.3em] uppercase hover:bg-black hover:scale-[1.01] transition-all flex items-center justify-center gap-4 group shadow-[8px_8px_0px_rgba(0,0,0,0.1)]">
                                                    CALL FOR INTERVIEW <span className="text-xl group-hover:translate-x-2 transition-transform">→</span>
                                                </button>
                                                <button className="w-full px-8 py-5 border-[2px] border-[#1c1c1c] font-grotesk font-black text-[10px] tracking-[0.2em] uppercase hover:bg-[#1c1c1c] hover:text-white transition-all">
                                                    DOWNLOAD FULL DOSSIER
                                                </button>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    ))}
                </div>
            </main>

            <GridPlus className="fixed inset-0 pointer-events-none opacity-5 z-0" />
        </motion.div>
    );
}
