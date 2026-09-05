import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { generateSkillTest } from '../../api/generateTest';
import { analyzeIntegrity } from '../../services/AntiCheatSystem'; // Import Anti-Cheat
import TestIntro from './TestIntro';
import QuestionCard from './QuestionCard';
import TestResult from './TestResult';

export default function TestRenderer({ roleData, onComplete }) {
    const [status, setStatus] = useState('loading');
    const [testData, setTestData] = useState(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [answers, setAnswers] = useState({});
    const [result, setResult] = useState(null);
    const [timeLeft, setTimeLeft] = useState(600);
    const [error, setError] = useState(null);

    // Track candidate interaction telemetry
    const startTimeRef = useRef(null);
    const interactionsRef = useRef([]);

    // Reset timer on new question
    useEffect(() => {
        if (status === 'test') {
            startTimeRef.current = Date.now();
        }
    }, [currentIndex, status]);

    const recordInteraction = (isFinalSubmission = false) => {
        if (!startTimeRef.current || !testData) return;

        const currentQ = testData.questions[currentIndex];
        const timeTaken = Date.now() - startTimeRef.current;
        const selectedOpt = answers[currentQ.id];
        const selectedIndex = currentQ.options.indexOf(selectedOpt);

        interactionsRef.current.push({
            questionId: currentQ.id,
            timeTaken,
            selectedOptionIndex: selectedIndex,
            timestamp: new Date().toISOString()
        });

        // Reset for next question unless submitting
        if (!isFinalSubmission) startTimeRef.current = Date.now();
    };

    const submitTest = useCallback(() => {
        if (!testData) return;

        // Record final question telemetry
        recordInteraction(true);

        // Calculate Score
        let correctCount = 0;
        const explanations = testData.questions.map(q => {
            const isCorrect = answers[q.id] === q.correct;
            if (isCorrect) correctCount++;
            return {
                question: q.question,
                isCorrect,
                explanation: q.explanation
            };
        });

        const percentage = Math.round((correctCount / testData.questions.length) * 100);
        const passed = percentage >= (testData.scoring.pass_threshold || 60);

        // Run integrity check on collected telemetry
        const integrityReport = analyzeIntegrity({
            interactions: interactionsRef.current,
            totalTime: 600000 - (timeLeft * 1000), // Approximate total time
            score: percentage,
            level: roleData.level || 'Mid' // Use role level from props
        });

        console.log("🛡️ Integrity Report Generated:", integrityReport);

        const resultData = {
            percentage,
            passed,
            explanations,
            jobId: roleData.jobId || 'unknown',
            integrity: integrityReport // Attach signal data
        };

        setResult(resultData);
        setStatus('result');
    }, [testData, answers, roleData, timeLeft]);

    useEffect(() => {
        let timer;
        if (status === 'test' && timeLeft > 0) {
            timer = setInterval(() => {
                setTimeLeft((prev) => {
                    if (prev <= 1) {
                        clearInterval(timer);
                        submitTest(); // Auto-submit
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        }
        return () => clearInterval(timer);
    }, [status, timeLeft, submitTest]);

    useEffect(() => {
        const fetchTest = async () => {
            try {
                setError(null);
                const data = await generateSkillTest(roleData);

                // 🛑 RANDOMIZE QUESTIONS & OPTIONS
                const shuffledQuestions = [...data.questions].sort(() => Math.random() - 0.5).map(q => ({
                    ...q,
                    options: [...q.options].sort(() => Math.random() - 0.5)
                }));

                setTestData({ ...data, questions: shuffledQuestions });
                setStatus('intro');
            } catch (err) {
                console.error("Failed to load test", err);
                setError(err.message || "Impossible to reach the Skill Verification Agent. Check your API key and connection.");
            }
        };
        fetchTest();
    }, [roleData]);

    const handleStart = () => {
        setStatus('test');
    };

    const handleAnswer = (questionId, option) => {
        setAnswers(prev => ({ ...prev, [questionId]: option }));
    };

    const handleNext = () => {
        if (currentIndex < testData.questions.length - 1) {
            recordInteraction(); // Log timing
            setCurrentIndex(prev => prev + 1);
        } else {
            submitTest();
        }
    };

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-full space-y-8 text-center max-w-md mx-auto">
                <div className="w-16 h-16 border border-red-500/20 rounded-full flex items-center justify-center text-red-500">!</div>
                <div className="space-y-2">
                    <h3 className="font-montreal font-bold text-2xl uppercase tracking-tight">Agent Error</h3>
                    <p className="font-inter text-sm opacity-60 leading-relaxed">{error}</p>
                </div>
                <button onClick={() => window.location.reload()} className="px-8 py-4 bg-[#1c1c1c] text-[#E6E6E3] font-grotesk font-black text-[10px] tracking-[0.3em] uppercase transition-all">
                    Retry Agent Connection
                </button>
            </div>
        );
    }

    if (status === 'loading') {
        return (
            <div className="flex flex-col items-center justify-center h-full space-y-4">
                <div className="w-12 h-12 border-2 border-[#1c1c1c]/10 border-t-[#1c1c1c] rounded-full animate-spin" />
                <p className="font-grotesk text-[10px] uppercase tracking-widest opacity-40 animate-pulse text-center">
                    INITIALIZING LOCAL AGENT (LLAMA 3.1)...<br />
                    <span className="text-[8px] opacity-70">Checking cache & generating secure, offline test questions</span>
                </p>
            </div>
        );
    }

    return (
        <div className="w-full h-full flex flex-col relative">
            <AnimatePresence mode="wait">
                {status === 'intro' && (
                    <motion.div
                        key="intro"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="h-full"
                    >
                        <TestIntro
                            role={testData.role}
                            level={testData.level}
                            onStart={handleStart}
                        />
                    </motion.div>
                )}

                {status === 'test' && (
                    <motion.div
                        key="test"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="flex-1 flex flex-col justify-between py-8"
                    >
                        {/* PROGRESS BAR */}
                        <div className="w-full h-1 bg-[#1c1c1c]/5 mb-8 relative overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${((currentIndex + 1) / testData.questions.length) * 100}%` }}
                                transition={{ duration: 0.5 }}
                                className="absolute top-0 left-0 h-full bg-[#1c1c1c]"
                            />
                        </div>

                        <QuestionCard
                            question={{ ...testData.questions[currentIndex], index: currentIndex }}
                            selectedOption={answers[testData.questions[currentIndex].id]}
                            onSelectOption={(opt) => handleAnswer(testData.questions[currentIndex].id, opt)}
                        />

                        <div className="sticky bottom-0 bg-[#E6E6E3]/95 backdrop-blur-sm pt-8 pb-0 border-t border-[#1c1c1c]/5 flex justify-between items-center z-10">
                            <div className="flex items-center gap-6">
                                <div className="font-grotesk text-[10px] font-bold uppercase tracking-widest opacity-40">
                                    QUESTION {currentIndex + 1} OF {testData.questions.length}
                                </div>
                                <div className={`font-grotesk text-[10px] font-bold uppercase tracking-widest ${timeLeft < 60 ? 'text-red-500 animate-pulse' : 'opacity-40'}`}>
                                    TIME LEFT: {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
                                </div>
                            </div>

                            <button
                                onClick={handleNext}
                                disabled={!answers[testData.questions[currentIndex].id]}
                                className="px-8 py-4 bg-[#1c1c1c] text-[#E6E6E3] font-grotesk font-black text-xs tracking-[0.3em] uppercase disabled:opacity-20 disabled:cursor-not-allowed transition-all hover:scale-[1.02]"
                            >
                                {currentIndex === testData.questions.length - 1 ? 'SUBMIT TEST' : 'NEXT QUESTION →'}
                            </button>
                        </div>
                    </motion.div>
                )}

                {status === 'result' && (
                    <motion.div
                        key="result"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="h-full"
                    >
                        <TestResult result={result} onBack={() => onComplete(result)} />
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
