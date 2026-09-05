import { motion } from 'framer-motion';

export default function TestIntro({ role, level, onStart }) {
    return (
        <div className="flex flex-col items-center justify-center h-full space-y-12 text-center max-w-2xl mx-auto">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="space-y-6"
            >
                <div className="space-y-2">
                    <label className="font-grotesk text-[10px] uppercase opacity-60 font-bold tracking-widest">
                        SKILL VERIFICATION
                    </label>
                    <h1 className="font-montreal font-black text-5xl md:text-7xl uppercase tracking-tighter leading-none">
                        {role}
                    </h1>
                    <div className="flex items-center justify-center gap-2">
                        <span className="px-3 py-1 border border-[#1c1c1c]/10 rounded-full font-inter text-[10px] uppercase font-bold tracking-widest opacity-60">
                            Level: {level}
                        </span>
                        <span className="px-3 py-1 border border-[#1c1c1c]/10 rounded-full font-inter text-[10px] uppercase font-bold tracking-widest opacity-60">
                            ~10 Minutes
                        </span>
                    </div>
                </div>

                <p className="font-inter text-sm md:text-base opacity-70 max-w-lg mx-auto leading-relaxed">
                    This assessment validates your technical proficiency for the role.
                    Questions adapt to the job requirements.
                    Results are analyzed instantly by the Skill Verification Agent.
                </p>
            </motion.div>

            <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.6 }}
                onClick={onStart}
                className="group relative px-12 py-6 bg-[#1c1c1c] text-[#E6E6E3] overflow-hidden"
            >
                <span className="relative z-10 font-grotesk font-black text-xs tracking-[0.3em] uppercase group-hover:tracking-[0.4em] transition-all duration-300">
                    Begin Assessment
                </span>
                <div className="absolute inset-0 bg-black translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
            </motion.button>
        </div>
    );
}
