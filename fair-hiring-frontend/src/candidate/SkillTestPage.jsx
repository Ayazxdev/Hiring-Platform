import { motion } from 'framer-motion';
import TestRenderer from '../components/SkillTest/TestRenderer';
import GridPlus from '../components/GridPlus';

export default function SkillTestPage({ roleId, roleData, onExit, onComplete }) {
    return (
        <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
            className="fixed inset-0 z-[250] bg-[#E6E6E3] text-[#1c1c1c] overflow-y-auto selection:bg-black selection:text-white"
            data-lenis-prevent
        >
            {/* STICKY HEADER */}
            <header className="sticky top-0 left-0 w-full bg-[#E6E6E3] border-b-[3px] border-[#1c1c1c] z-50 px-6 md:px-12 py-6 flex justify-between items-center bg-opacity-95 backdrop-blur-sm">
                <div className="flex items-center gap-6">
                    <button
                        onClick={onExit}
                        className="px-6 py-3 border-[2px] border-[#1c1c1c] font-grotesk text-[11px] font-black uppercase tracking-[0.2em] hover:bg-[#1c1c1c] hover:text-[#E6E6E3] transition-all flex items-center gap-2 group"
                    >
                        <span className="group-hover:-translate-x-1 transition-transform inline-block">←</span> CANCEL TEST
                    </button>
                    <div className="h-10 w-[2px] bg-[#1c1c1c]/10 hidden md:block"></div>
                    <span className="font-montreal font-black text-sm md:text-base tracking-[0.2em] uppercase text-[#1c1c1c]">
                        SKILL VERIFICATION MODULE
                    </span>
                </div>
                <div className="font-grotesk text-[10px] font-black tracking-widest uppercase opacity-40">
                    AGENT: ACTIVE
                </div>
            </header>

            <main className="max-w-[1280px] mx-auto px-6 md:px-12 py-12 min-h-[90vh] flex flex-col">
                <TestRenderer
                    roleData={roleData}
                    onComplete={(result) => {
                        console.log("Test Completed Payload:", result);
                        onComplete(result);
                    }}
                />
            </main>

            <GridPlus className="fixed inset-0 pointer-events-none opacity-5 z-0" />

        </motion.div>
    );
}
