import { motion } from 'framer-motion';

export default function TestResult({ result, onBack }) {
    const { percentage, passed, explanations } = result;

    return (
        <div className="max-w-4xl mx-auto space-y-16 py-12">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
                className="flex flex-col md:flex-row justify-between items-end gap-8 border-b border-[#1c1c1c]/10 pb-12"
            >
                <div className="space-y-4">
                    <label className="font-grotesk text-[10px] uppercase opacity-60 font-bold tracking-widest">
                        ASSESSMENT COMPLETE
                    </label>
                    <h2 className="font-montreal font-black text-6xl md:text-7xl w-full leading-none uppercase">
                        {percentage >= 70 ? 'High Confidence' : 'Building Baseline'}
                    </h2>
                </div>
                <div className="flex flex-col items-end">
                    <div className="font-montreal font-black text-6xl md:text-8xl">
                        {percentage}%
                    </div>
                    <div className="font-grotesk text-[10px] uppercase opacity-60 font-bold tracking-widest">
                        SKILL CONFIDENCE
                    </div>
                </div>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
                <div className="md:col-span-1 space-y-6">
                    <h3 className="font-grotesk text-[11px] font-black uppercase tracking-widest">RESULT SIGNAL</h3>
                    <p className="font-inter text-sm opacity-70 leading-relaxed">
                        {percentage >= 70
                            ? "Excellent work. This score demonstrates strong alignment with the technical role requirements. Your skill passport has been updated with this signal."
                            : "Your current signal shows potential but suggests gaps in key areas. We recommend focusing on the highlighted topics in the breakdown."}
                    </p>
                    <button
                        onClick={onBack}
                        className="w-full py-4 mt-8 bg-[#1c1c1c] text-[#E6E6E3] font-grotesk font-black text-xs tracking-[0.3em] uppercase hover:scale-[1.02] transition-all"
                    >
                        COMPLETE & RETURN
                    </button>
                </div>

                <div className="md:col-span-2 space-y-10">
                    <div className="flex justify-between items-center">
                        <h3 className="font-grotesk text-[11px] font-black uppercase tracking-widest">TECHNICAL FEEDBACK</h3>
                        <div className="font-inter text-[10px] opacity-40 italic">Scroll for detail ↓</div>
                    </div>

                    <div className="space-y-8 max-h-[60vh] overflow-y-auto custom-scrollbar pr-6">
                        {explanations.map((item, idx) => (
                            <div key={idx} className={`relative p-8 border ${item.isCorrect ? 'border-[#1c1c1c]/10 bg-white/5' : 'border-red-900/20 bg-red-500/[0.02]'} space-y-4 group transition-all duration-500 hover:border-[#1c1c1c]/40`}>
                                <div className="flex justify-between items-start">
                                    <div className="space-y-1">
                                        <span className="font-grotesk text-[10px] font-bold uppercase tracking-widest opacity-30">SIGNAL {idx + 1}</span>
                                        <div className={`font-grotesk text-[10px] font-black uppercase tracking-widest ${item.isCorrect ? 'text-green-600' : 'text-red-500'}`}>
                                            {item.isCorrect ? 'VALIDATED' : 'DATA MISMATCH'}
                                        </div>
                                    </div>
                                    <div className="w-8 h-8 rounded-full border border-[#1c1c1c]/10 flex items-center justify-center font-grotesk text-[10px] font-black">
                                        {item.isCorrect ? '✓' : '!'}
                                    </div>
                                </div>

                                <p className="font-inter text-base font-semibold leading-snug pr-8">{item.question}</p>

                                <div className="pt-4 border-t border-[#1c1c1c]/5 grid md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-40 mb-2 block">Agent Explanation</label>
                                        <p className="font-inter text-sm opacity-70 leading-relaxed italic pr-4">
                                            {item.explanation}
                                        </p>
                                    </div>
                                    {item.relevance && (
                                        <div>
                                            <label className="font-grotesk text-[9px] font-black uppercase tracking-widest opacity-40 mb-2 block">Why This Matters</label>
                                            <p className="font-inter text-sm opacity-60 leading-relaxed">
                                                {item.relevance}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
            <style>{`
                .custom-scrollbar::-webkit-scrollbar { width: 4px; }
                .custom-scrollbar::-webkit-scrollbar-thumb { background: #1c1c1c; border-radius: 10px; }
                .custom-scrollbar::-webkit-scrollbar-track { background: rgba(0,0,0,0.05); }
            `}</style>
        </div>
    );
}
