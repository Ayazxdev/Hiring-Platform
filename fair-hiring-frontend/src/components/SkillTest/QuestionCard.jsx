import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';

export default function QuestionCard({ question, selectedOption, onSelectOption }) {
    return (
        <div className="w-full max-w-3xl mx-auto space-y-12">
            <div className="space-y-6">
                <label className="font-grotesk text-[10px] uppercase opacity-40 font-bold tracking-widest">
                    QUESTION {question.index + 1}
                </label>
                <div className="font-montreal font-bold text-2xl md:text-3xl leading-relaxed min-h-[100px] text-[#1c1c1c] max-w-none">
                    <ReactMarkdown
                        components={{
                            code({ node, inline, className, children, ...props }) {
                                return !inline ? (
                                    <span className="block bg-[#1c1c1c]/5 p-6 rounded-lg my-6 font-mono text-sm overflow-x-auto border border-[#1c1c1c]/10 text-left leading-normal">
                                        <code {...props}>{children}</code>
                                    </span>
                                ) : (
                                    <code className="bg-[#1c1c1c]/10 px-1 py-0.5 rounded font-mono text-sm" {...props}>
                                        {children}
                                    </code>
                                )
                            }
                        }}
                    >
                        {question.question}
                    </ReactMarkdown>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
                {question.options.map((option, idx) => {
                    const isSelected = selectedOption === option;
                    return (
                        <button
                            key={idx}
                            onClick={() => onSelectOption(option)}
                            className={`
                                relative text-left p-6 md:p-8 border transition-all duration-300 group
                                ${isSelected
                                    ? 'border-[#1c1c1c] bg-[#1c1c1c] text-[#E6E6E3]'
                                    : 'border-[#1c1c1c]/10 hover:border-[#1c1c1c]/40 hover:bg-[#1c1c1c]/5'
                                }
                            `}
                        >
                            <div className="flex items-start gap-4">
                                <span className={`
                                    font-grotesk text-xs font-black uppercase tracking-widest mt-1
                                    ${isSelected ? 'opacity-100' : 'opacity-40 group-hover:opacity-100'}
                                `}>
                                    {String.fromCharCode(65 + idx)}
                                </span>
                                <span className="font-inter text-lg leading-relaxed font-medium">
                                    {option}
                                </span>
                            </div>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
