import React, { useState } from 'react';
import { Icons } from './constants';

export const InterviewSetup = ({ onStart }) => {
    const [role, setRole] = useState('Frontend Engineer');
    const [company, setCompany] = useState('');
    const [difficulty, setDifficulty] = useState('Mid-Level');
    const [focus, setFocus] = useState(['Problem Solving', 'Communication']);

    const handleFocusToggle = (f) => {
        setFocus(prev => prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]);
    };

    const focusOptions = [
        { name: 'Coding', description: 'Evaluates your technical implementation skills.' },
        { name: 'System Design', description: 'Assesses architectural and scalability thinking.' },
        { name: 'Behavioral', description: 'Focuses on past experiences and soft skills.' },
        { name: 'Communication', description: 'Measures clarity and articulation.' },
        { name: 'Problem Solving', description: 'Evaluates logical reasoning and approach.' },
        { name: 'Leadership', description: 'Assesses management and initiative potential.' }
    ];

    return (
        <div className="max-w-3xl mx-auto p-12 bg-white border-[3px] border-[#1c1c1c] shadow-[12px_12px_0px_#1c1c1c]/10 animate-in fade-in slide-in-from-bottom-8 duration-700">
            <div className="flex items-center gap-6 mb-12 border-b-[3px] border-[#1c1c1c] pb-8">
                <div className="w-16 h-16 bg-[#1c1c1c] flex items-center justify-center">
                    <Icons.Sparkles className="w-8 h-8 text-white" />
                </div>
                <div>
                    <h2 className="text-4xl font-black tracking-tight uppercase font-montreal">Session Configuration</h2>
                    <p className="text-[#1c1c1c]/50 font-black text-[10px] tracking-[0.2em] uppercase font-grotesk mt-1">Configure your AI agent parameters</p>
                </div>
            </div>

            <div className="space-y-12">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                    <div className="space-y-4">
                        <label className="text-[10px] font-black uppercase tracking-[0.2em] text-[#1c1c1c] font-grotesk block border-l-[3px] border-[#1c1c1c] pl-3">Target Role</label>
                        <input
                            type="text"
                            value={role}
                            onChange={(e) => setRole(e.target.value)}
                            className="w-full px-6 py-5 border-[3px] border-[#1c1c1c] bg-transparent text-[#1c1c1c] focus:bg-[#E6E6E3] outline-none transition-all font-black uppercase text-sm font-grotesk"
                            placeholder="e.g. Lead Developer"
                        />
                    </div>

                    <div className="space-y-4">
                        <label className="text-[10px] font-black uppercase tracking-[0.2em] text-[#1c1c1c] font-grotesk block border-l-[3px] border-[#1c1c1c] pl-3">Company Context</label>
                        <input
                            type="text"
                            value={company}
                            onChange={(e) => setCompany(e.target.value)}
                            className="w-full px-6 py-5 border-[3px] border-[#1c1c1c] bg-transparent text-[#1c1c1c] focus:bg-[#E6E6E3] outline-none transition-all font-black uppercase text-sm font-grotesk"
                            placeholder="e.g. OpenAI"
                        />
                    </div>
                </div>

                <div className="space-y-6">
                    <label className="text-[10px] font-black uppercase tracking-[0.2em] text-[#1c1c1c] font-grotesk block border-l-[3px] border-[#1c1c1c] pl-3">Seniority Level</label>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        {['Junior', 'Mid-Level', 'Senior', 'Lead'].map((d) => (
                            <button
                                key={d}
                                onClick={() => setDifficulty(d)}
                                className={`px-4 py-4 border-[3px] border-[#1c1c1c] text-[10px] font-black tracking-[0.2em] uppercase transition-all ${difficulty === d
                                    ? 'bg-[#1c1c1c] text-white shadow-[4px_4px_0px_#ccc]'
                                    : 'bg-transparent text-[#1c1c1c] hover:bg-[#E6E6E3]'
                                    }`}
                            >
                                {d}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="space-y-6">
                    <label className="text-[10px] font-black uppercase tracking-[0.2em] text-[#1c1c1c] font-grotesk block border-l-[3px] border-[#1c1c1c] pl-3">Evaluation Focus</label>
                    <div className="flex flex-wrap gap-3">
                        {focusOptions.map((f) => (
                            <button
                                key={f.name}
                                title={f.description}
                                onClick={() => handleFocusToggle(f.name)}
                                className={`px-6 py-3 border-[2px] border-[#1c1c1c] text-[10px] font-black uppercase tracking-[0.2em] transition-all relative group ${focus.includes(f.name)
                                    ? 'bg-[#1c1c1c] text-white'
                                    : 'bg-transparent text-[#1c1c1c] hover:bg-[#E6E6E3]'
                                    }`}
                            >
                                {f.name}
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 hidden group-hover:block w-56 p-4 bg-[#1c1c1c] text-white text-[10px] font-bold shadow-2xl z-50 pointer-events-none normal-case tracking-normal">
                                    {f.description}
                                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-[8px] border-transparent border-t-[#1c1c1c]" />
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                <button
                    onClick={() => onStart({ role, company, difficulty, focus })}
                    className="w-full mt-8 py-8 bg-[#1c1c1c] text-white border-[3px] border-[#1c1c1c] font-grotesk font-black text-xl tracking-[0.3em] uppercase transition-all shadow-[8px_8px_0px_#ccc] hover:bg-white hover:text-black hover:-translate-y-2 hover:shadow-[12px_12px_0px_#bbb] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none flex items-center justify-center gap-4"
                >
                    <Icons.Sparkles className="w-6 h-6" />
                    INITIALIZE INTERVIEW
                </button>
            </div>
            <p className="mt-12 text-[9px] text-center text-[#1c1c1c]/40 font-black tracking-[0.5em] uppercase">SYSTEM V1.0 // FAIR HIRING NETWORK</p>
        </div>
    );
};
