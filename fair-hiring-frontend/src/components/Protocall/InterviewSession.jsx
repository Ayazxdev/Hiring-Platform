import React, { useEffect, useRef, useState, useCallback } from 'react';
import { GoogleGenAI, Modality, Type } from '@google/genai';
import { InterviewStatus } from './types';
import { GEMINI_MODEL, Icons } from './constants';
import { createPcmBlob, decode, decodeAudioData } from './audioUtils';


const FRAME_RATE = 1;
const JPEG_QUALITY = 0.5;

const updateVisualFeedbackDeclaration = {
    name: 'updateVisualFeedback',
    parameters: {
        type: Type.OBJECT,
        description: 'Provide immediate professional UI feedback based on candidate visual cues and tonality.',
        properties: {
            cue: {
                type: Type.STRING,
                description: 'A short observation (e.g., "Excellent posture", "Confident vocal tone")',
            },
            sentiment: {
                type: Type.STRING,
                description: 'Visual sentiment: "positive", "neutral", or "constructive".',
            }
        },
        required: ['cue', 'sentiment'],
    },
};

export const InterviewSession = ({ config, onComplete }) => {
    const [isReady, setIsReady] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [currentTranscript, setCurrentTranscript] = useState([]);
    const [partialTranscript, setPartialTranscript] = useState({ user: '', model: '' });
    const [error, setError] = useState(null);
    const [secondsElapsed, setSecondsElapsed] = useState(0);

    const [visualFeedback, setVisualFeedback] = useState(null);
    const feedbackTimeoutRef = useRef(null);
    const scrollRef = useRef(null);

    const audioContextRef = useRef(null);
    const sessionRef = useRef(null);
    const nextStartTimeRef = useRef(0);
    const sourcesRef = useRef(new Set());
    const transcriptionRef = useRef({ user: '', model: '' });

    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const frameIntervalRef = useRef(null);
    const timerIntervalRef = useRef(null);
    const isMutedRef = useRef(false);

    const sessionActiveRef = useRef(false);
    const audioSourceRef = useRef(null);
    const scriptProcessorRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            const scrollContainer = scrollRef.current;
            requestAnimationFrame(() => {
                scrollContainer.scrollTo({
                    top: scrollContainer.scrollHeight,
                    behavior: 'smooth'
                });
            });
        }
    }, [currentTranscript, partialTranscript]);

    useEffect(() => {
        isMutedRef.current = isMuted;
    }, [isMuted]);

    useEffect(() => {
        if (isReady && isListening) {
            timerIntervalRef.current = window.setInterval(() => {
                setSecondsElapsed(prev => prev + 1);
            }, 1000);
        } else {
            if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
        }
        return () => {
            if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
        };
    }, [isReady, isListening]);

    const formatTime = (totalSeconds) => {
        const mins = Math.floor(totalSeconds / 60);
        const secs = totalSeconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const blobToBase64 = (blob) => {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.readAsDataURL(blob);
        });
    };

    const cleanup = useCallback(() => {
        sessionActiveRef.current = false;
        if (sessionRef.current) {
            try { sessionRef.current.close(); } catch (e) { }
            sessionRef.current = null;
        }
        if (audioContextRef.current) {
            try { audioContextRef.current.input.close(); } catch (e) { }
            try { audioContextRef.current.output.close(); } catch (e) { }
            audioContextRef.current = null;
        }
        if (audioSourceRef.current) {
            try { audioSourceRef.current.disconnect(); } catch (e) { }
            audioSourceRef.current = null;
        }
        if (scriptProcessorRef.current) {
            try { scriptProcessorRef.current.disconnect(); } catch (e) { }
            scriptProcessorRef.current = null;
        }
        if (frameIntervalRef.current) {
            clearInterval(frameIntervalRef.current);
            frameIntervalRef.current = null;
        }
        if (timerIntervalRef.current) {
            clearInterval(timerIntervalRef.current);
            timerIntervalRef.current = null;
        }
        if (feedbackTimeoutRef.current) {
            clearTimeout(feedbackTimeoutRef.current);
            feedbackTimeoutRef.current = null;
        }

        sourcesRef.current.forEach(s => { try { s.stop(); } catch (e) { } });
        sourcesRef.current.clear();
        nextStartTimeRef.current = 0;
        setIsReady(false);
        setIsListening(false);
    }, []);

    const handleFinish = () => {
        onComplete(currentTranscript, formatTime(secondsElapsed));
    };

    const initializeSession = useCallback(async () => {
        cleanup();
        const apiKey = import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.GEMINI_API_KEY || import.meta.env.VITE_API_KEY || localStorage.getItem('fhn_gemini_api_key');

        if (!apiKey) {
            setError("API Key Missing. Set VITE_GEMINI_API_KEY in .env or configure in interview lobby");
            return;
        }

        try {
            const ai = new GoogleGenAI({ apiKey });
            const inCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
            const outCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
            audioContextRef.current = { input: inCtx, output: outCtx };

            const stream = await navigator.mediaDevices.getUserMedia({
                audio: { echoCancellation: true, noiseSuppression: true },
                video: { width: { ideal: 1280 }, height: { ideal: 720 } }
            });

            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }

            const sessionPromise = ai.live.connect({
                model: GEMINI_MODEL,
                callbacks: {
                    onopen: () => {
                        sessionActiveRef.current = true;
                        setIsReady(true);
                        setIsListening(true);
                        inCtx.resume();
                        outCtx.resume();

                        const source = inCtx.createMediaStreamSource(stream);
                        const scriptProcessor = inCtx.createScriptProcessor(512, 1, 1);
                        audioSourceRef.current = source;
                        scriptProcessorRef.current = scriptProcessor;

                        scriptProcessor.onaudioprocess = (e) => {
                            if (isMutedRef.current || !sessionActiveRef.current) return;
                            const inputData = e.inputBuffer.getChannelData(0);
                            const pcmBlob = createPcmBlob(inputData);
                            sessionPromise.then(s => {
                                if (sessionActiveRef.current) s.sendRealtimeInput({ media: pcmBlob });
                            }).catch(() => { });
                        };
                        source.connect(scriptProcessor);
                        scriptProcessor.connect(inCtx.destination);

                        frameIntervalRef.current = window.setInterval(() => {
                            if (videoRef.current && canvasRef.current && sessionRef.current && sessionActiveRef.current) {
                                const canvas = canvasRef.current;
                                const video = videoRef.current;
                                const ctx = canvas.getContext('2d');
                                if (ctx && video.videoWidth) {
                                    canvas.width = video.videoWidth;
                                    canvas.height = video.videoHeight;
                                    ctx.drawImage(video, 0, 0);
                                    canvas.toBlob(async (blob) => {
                                        if (blob && sessionActiveRef.current) {
                                            const base64Data = await blobToBase64(blob);
                                            sessionPromise.then(s => {
                                                if (sessionActiveRef.current) {
                                                    s.sendRealtimeInput({
                                                        media: { data: base64Data, mimeType: 'image/jpeg' }
                                                    });
                                                }
                                            }).catch(() => { });
                                        }
                                    }, 'image/jpeg', JPEG_QUALITY);
                                }
                            }
                        }, 1000 / FRAME_RATE);

                        setTimeout(() => {
                            sessionPromise.then(s => {
                                if (sessionActiveRef.current) {
                                    s.send({
                                        text: "Begin the interview. Greet the candidate and ask your first question."
                                    });
                                }
                            }).catch(() => { });
                        }, 1000);
                    },
                    onmessage: async (msg) => {
                        if (!audioContextRef.current) return;

                        if (msg.toolCall) {
                            for (const fc of msg.toolCall.functionCalls) {
                                if (fc.name === 'updateVisualFeedback') {
                                    const args = fc.args;
                                    setVisualFeedback(args);
                                    if (feedbackTimeoutRef.current) clearTimeout(feedbackTimeoutRef.current);
                                    feedbackTimeoutRef.current = window.setTimeout(() => setVisualFeedback(null), 4000);
                                    sessionPromise.then(s => {
                                        if (sessionActiveRef.current) {
                                            s.sendToolResponse({
                                                functionResponses: { id: fc.id, name: fc.name, response: { result: "ok" } }
                                            });
                                        }
                                    }).catch(() => { });
                                }
                            }
                        }

                        if (msg.serverContent?.outputTranscription) {
                            transcriptionRef.current.model += msg.serverContent.outputTranscription.text;
                            setPartialTranscript(prev => ({ ...prev, model: transcriptionRef.current.model }));
                        }
                        if (msg.serverContent?.inputTranscription) {
                            transcriptionRef.current.user += msg.serverContent.inputTranscription.text;
                            setPartialTranscript(prev => ({ ...prev, user: transcriptionRef.current.user }));
                        }

                        if (msg.serverContent?.turnComplete) {
                            const uText = transcriptionRef.current.user.trim();
                            const mText = transcriptionRef.current.model.trim();
                            if (uText || mText) {
                                setCurrentTranscript(prev => [
                                    ...prev,
                                    ...(uText ? [{ role: 'user', text: uText }] : []),
                                    ...(mText ? [{ role: 'interviewer', text: mText }] : [])
                                ]);
                            }
                            transcriptionRef.current = { user: '', model: '' };
                            setPartialTranscript({ user: '', model: '' });
                        }

                        const base64Audio = msg.serverContent?.modelTurn?.parts[0]?.inlineData?.data;
                        if (base64Audio) {
                            const ctx = audioContextRef.current.output;
                            nextStartTimeRef.current = Math.max(nextStartTimeRef.current, ctx.currentTime);
                            const audioBuffer = await decodeAudioData(decode(base64Audio), ctx, 24000, 1);
                            const source = ctx.createBufferSource();
                            source.buffer = audioBuffer;
                            source.connect(ctx.destination);
                            source.addEventListener('ended', () => sourcesRef.current.delete(source));
                            source.start(nextStartTimeRef.current);
                            nextStartTimeRef.current += audioBuffer.duration;
                            sourcesRef.current.add(source);
                        }

                        if (msg.serverContent?.interrupted) {
                            sourcesRef.current.forEach(s => { try { s.stop(); } catch (e) { } });
                            sourcesRef.current.clear();
                            nextStartTimeRef.current = 0;
                            setPartialTranscript(prev => ({ ...prev, model: '' }));
                            transcriptionRef.current.model = '';
                        }
                    },
                    onerror: (e) => {
                        sessionActiveRef.current = false;
                        setError(`Hardware Link Error: ${e.message || 'Connection failed'}`);
                        setIsListening(false);
                    },
                    onclose: (e) => {
                        sessionActiveRef.current = false;
                        setIsListening(false);
                    }
                },
                config: {
                    responseModalities: [Modality.AUDIO],
                    tools: [{ functionDeclarations: [updateVisualFeedbackDeclaration] }],
                    speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Puck' } } },
                    inputAudioTranscription: {},
                    outputAudioTranscription: {},
                    systemInstruction: `
            You are "Fair Hiring AI", an elite executive interviewer for a ${config.difficulty} ${config.role} position${config.company ? ` at ${config.company}` : ''}.
            
            CORE MISSION:
            Lead a high-stakes professional interview.
            
            OPERATIONAL PROTOCOL:
            1. BE PROACTIVE: Start the interview immediately. Greet the candidate and ask the first question.
            2. CHALLENGE: Ask insightful questions focused on: ${config.focus.join(', ')}.
            3. PROBE: If the answer is brief, ask follow-up questions to uncover depth.
            4. VISUAL AWARENESS: Use "updateVisualFeedback" to note confidence, eye contact, or tone.
            5. PROFESSIONAL: Maintain a direct, sophisticated, and encouraging tone.
          `
                }
            });

            sessionRef.current = await sessionPromise;
        } catch (err) {
            setError(`Hardware Sync Error: ${err.message}`);
        }
    }, [config, cleanup]);

    useEffect(() => {
        initializeSession();
        return cleanup;
    }, [initializeSession, cleanup]);

    const renderSentences = (text, isActive, role) => {
        if (!text) return null;
        const sentences = text.match(/[^.!?]+[.!?]*\s*/g) || [text];

        return sentences.map((s, idx) => {
            const isLatest = idx === sentences.length - 1;
            const highlightClass = isLatest && isActive
                ? 'text-[#1c1c1c] font-black scale-[1.01] inline-block'
                : 'opacity-50';

            return (
                <span key={idx} className={`transition-all duration-300 transform-gpu ${highlightClass}`}>
                    {s}
                </span>
            );
        });
    };

    return (
        <div className="flex flex-col h-[80vh] border-[3px] border-[#1c1c1c] bg-white shadow-[16px_16px_0px_#1c1c1c]/5 overflow-hidden animate-in fade-in zoom-in-95 duration-700">
            {/* Session Header */}
            <div className="bg-[#FFFFFF] px-8 py-5 flex justify-between items-center border-b-[3px] border-[#1c1c1c]">
                <div className="flex items-center gap-8">
                    <div className="flex gap-3 items-center">
                        <div className={`w-3 h-3 rounded-full ${isListening ? (isMuted ? 'bg-amber-500' : 'bg-green-500 animate-pulse') : 'bg-red-500'}`} />
                        <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#1c1c1c]">
                            {isMuted ? 'INPUT_MUTED' : isListening ? 'SESSION_ID_LIVE' : 'SESSION_PAUSED'}
                        </span>
                    </div>
                    <div className="h-4 w-[2px] bg-[#1c1c1c]/10" />
                    <div className="flex items-center gap-3">
                        <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#1c1c1c] opacity-40">ELAPSED_TIME</span>
                        <span className="font-grotesk text-sm font-black text-[#1c1c1c] tabular-nums">{formatTime(secondsElapsed)}</span>
                    </div>
                </div>
                <div className="flex gap-4">
                    <button
                        onClick={() => setIsMuted(!isMuted)}
                        className={`px-6 py-2 border-[2px] font-black text-[10px] uppercase tracking-widest transition-all ${isMuted ? 'bg-amber-400 border-[#1c1c1c] text-[#1c1c1c]' : 'bg-transparent border-[#1c1c1c]/20 text-[#1c1c1c] hover:border-[#1c1c1c]'}`}
                    >
                        {isMuted ? "UNMUTE_MIC" : "MUTE_MIC"}
                    </button>
                    <button
                        onClick={handleFinish}
                        className="bg-black text-white px-6 py-2 border-[2px] border-black font-black text-[10px] uppercase tracking-widest hover:bg-white hover:text-black transition-all shadow-[4px_4px_0px_#ccc]"
                    >
                        FINISH_INTERVIEW
                    </button>
                </div>
            </div>

            <div className="flex-1 flex flex-col lg:flex-row p-8 gap-8 overflow-hidden bg-[#E6E6E3]/30">
                {/* Visual Area */}
                <div className="flex-1 flex flex-col space-y-8 overflow-hidden">
                    <div className="relative aspect-video border-[3px] border-[#1c1c1c] bg-black overflow-hidden shadow-[8px_8px_0px_#ccc]">
                        <video ref={videoRef} autoPlay muted playsInline className="w-full h-full object-cover mirror opacity-90" />
                        <canvas ref={canvasRef} className="hidden" />

                        {visualFeedback && (
                            <div className="absolute bottom-8 left-8 right-8 animate-in slide-in-from-bottom-4 fade-in duration-500 z-50">
                                <div className={`px-6 py-4 border-[3px] bg-white flex items-center gap-4 shadow-[8px_8px_0px_rgba(0,0,0,0.1)] ${visualFeedback.sentiment === 'positive' ? 'border-green-600' :
                                    visualFeedback.sentiment === 'constructive' ? 'border-amber-500' :
                                        'border-[#1c1c1c]'
                                    }`}>
                                    <div className={`w-3 h-3 rounded-full ${visualFeedback.sentiment === 'positive' ? 'bg-green-600' :
                                        visualFeedback.sentiment === 'constructive' ? 'bg-amber-500' :
                                            'bg-[#1c1c1c]'
                                        } animate-pulse`} />
                                    <span className="text-[11px] font-black tracking-[0.2em] uppercase text-[#1c1c1c] font-grotesk">{visualFeedback.cue}</span>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="p-8 border-[3px] border-[#1c1c1c] bg-white flex items-center justify-between shadow-[8px_8px_0px_#ccc]">
                        <div className="flex items-center gap-6">
                            <div className={`w-14 h-14 border-[3px] border-[#1c1c1c] flex items-center justify-center transition-all ${isMuted ? 'bg-amber-400' : 'bg-[#1c1c1c] text-white shadow-xl'}`}>
                                {isMuted ? <Icons.MicrophoneSlash className="w-6 h-6" /> : <Icons.Microphone className="w-6 h-6 animate-pulse" />}
                            </div>
                            <div>
                                <h3 className="text-xl font-black tracking-tight font-montreal uppercase">Neural Voice Sync</h3>
                                <p className="text-[10px] font-black opacity-40 font-grotesk uppercase tracking-widest mt-1">System is processing sensory input stream</p>
                            </div>
                        </div>
                        {error && (
                            <div className="px-5 py-3 border-[2px] border-red-500 text-red-500 text-[10px] font-black uppercase tracking-widest animate-pulse">
                                {error}
                            </div>
                        )}
                    </div>
                </div>

                {/* Intelligence Log */}
                <div className="w-full lg:w-[450px] border-[3px] border-[#1c1c1c] bg-white flex flex-col overflow-hidden shadow-[8px_8px_0px_#ccc]">
                    <div className="px-6 py-4 border-b-[3px] border-[#1c1c1c] flex items-center justify-between bg-[#1c1c1c]/5">
                        <h4 className="text-[10px] font-black uppercase tracking-[0.4em] text-[#1c1c1c]">Communication Log</h4>
                        <span className="text-[9px] font-black text-[#1c1c1c] opacity-40">SYNC_ACTIVE</span>
                    </div>

                    <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-10 font-grotesk scroll-smooth pb-10 custom-scrollbar">
                        {currentTranscript.map((t, i) => (
                            <div key={i} className={`flex flex-col animate-in fade-in slide-in-from-bottom-2 duration-300 ${t.role === 'user' ? 'items-end' : 'items-start'}`}>
                                <div className={`flex items-center gap-3 mb-3 ${t.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                                    <span className="text-[8px] font-black uppercase tracking-[0.3em] opacity-40">
                                        {t.role === 'user' ? 'CANDIDATE' : 'FAIR_HIRING_AI'}
                                    </span>
                                </div>
                                <div className={`px-6 py-5 border-[2px] text-sm leading-relaxed max-w-[92%] transition-all ${t.role === 'user'
                                    ? 'bg-[#E6E6E3] border-[#1c1c1c] text-[#1c1c1c]'
                                    : 'bg-[#1c1c1c] border-[#1c1c1c] text-white'
                                    }`}>
                                    {t.text}
                                </div>
                            </div>
                        ))}

                        {(partialTranscript.user || partialTranscript.model) && (
                            <div className="space-y-6">
                                {partialTranscript.user && (
                                    <div className="flex flex-col items-end">
                                        <div className="flex items-center gap-2 mb-3 flex-row-reverse">
                                            <span className="text-[8px] font-black uppercase tracking-widest text-[#1c1c1c] animate-pulse">Candidate Speaking...</span>
                                        </div>
                                        <div className="px-6 py-5 border-[2px] border-[#1c1c1c]/20 border-dashed text-sm leading-relaxed text-[#1c1c1c]/60 italic italic font-medium">
                                            {renderSentences(partialTranscript.user, true, 'user')}
                                        </div>
                                    </div>
                                )}
                                {partialTranscript.model && (
                                    <div className="flex flex-col items-start">
                                        <div className="flex items-center gap-2 mb-3">
                                            <span className="text-[8px] font-black uppercase tracking-widest text-[#1c1c1c] animate-pulse">AI Responding...</span>
                                        </div>
                                        <div className="px-6 py-5 border-[2px] border-[#1c1c1c] bg-[#1c1c1c] text-white text-sm leading-relaxed shadow-[4px_4px_0px_#ccc]">
                                            {renderSentences(partialTranscript.model, true, 'model')}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {!currentTranscript.length && !partialTranscript.user && !partialTranscript.model && (
                            <div className="flex flex-col items-center justify-center py-20 opacity-10">
                                <Icons.Sparkles className="w-12 h-12 mb-4" />
                                <p className="text-[10px] font-black uppercase tracking-[0.5em] text-center">Neural Link Established</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <style>{`
                .custom-scrollbar::-webkit-scrollbar { width: 5px; }
                .custom-scrollbar::-webkit-scrollbar-thumb { background: #1c1c1c; }
                .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
            `}</style>
        </div>
    );
};
