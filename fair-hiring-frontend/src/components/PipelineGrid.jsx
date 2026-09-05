import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";

export default function PipelineGrid({ columns, onDecision, onMailMerge, approvedEmails = [] }) {
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [selectedAppIds, setSelectedAppIds] = useState(new Set());

  const toggleSelect = (appId) => {
    if (!appId) return;
    setSelectedAppIds((prev) => {
      const next = new Set(prev);
      if (next.has(appId)) next.delete(appId);
      else next.add(appId);
      return next;
    });
  };

  return (
    <div className="relative">
      {/* BULK ACTION BAR */}
      <AnimatePresence>
        {selectedAppIds.size > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mb-8 p-4 md:p-6 bg-black text-white border-4 border-black flex flex-wrap items-center justify-between gap-4 shadow-[6px_6px_0px_#A7FF2E]"
          >
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 bg-[#A7FF2E] rounded-full animate-ping" />
              <span className="font-grotesk text-xs md:text-sm font-black uppercase tracking-[0.2em] text-[#A7FF2E]">
                {selectedAppIds.size} CANDIDATE(S) SELECTED FOR BULK ACTION
              </span>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={async () => {
                  if (onDecision) {
                    await onDecision(Array.from(selectedAppIds), 'select');
                    setSelectedAppIds(new Set());
                  }
                }}
                className="px-6 py-2.5 bg-[#A7FF2E] text-black font-grotesk text-[10px] font-black uppercase tracking-[0.3em] hover:bg-white transition-all shadow-[3px_3px_0px_#fff] active:translate-x-[2px] active:translate-y-[2px]"
              >
                APPROVE SELECTED ({selectedAppIds.size}) ✓
              </button>
              <button
                onClick={async () => {
                  if (onDecision) {
                    await onDecision(Array.from(selectedAppIds), 'reject');
                    setSelectedAppIds(new Set());
                  }
                }}
                className="px-5 py-2.5 bg-transparent text-[#FF4D4D] border border-[#FF4D4D] font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-[#FF4D4D] hover:text-white transition-all"
              >
                REJECT SELECTED
              </button>
              <button
                onClick={() => setSelectedAppIds(new Set())}
                className="px-4 py-2.5 bg-white/10 text-white font-grotesk text-[9px] font-black uppercase tracking-widest hover:bg-white/20 transition-all"
              >
                DESELECT ALL
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex gap-8 overflow-x-auto pb-12 scroll-smooth snap-x">
        {columns.map((column) => (
          <div key={column.id} className="min-w-[320px] md:min-w-[380px] flex flex-col gap-6 snap-start">
            <div className="flex items-center justify-between border-b-4 border-black pb-4">
              <h3 className="font-montreal font-black text-xl uppercase tracking-tighter text-[#1c1c1c]">
                {column.title}
              </h3>
              <span className="font-grotesk text-[10px] font-black bg-black text-white px-2 py-1">
                {String(column.candidates.length).padStart(2, '0')}
              </span>
            </div>

            <div className="flex flex-col gap-6">
              {column.candidates.map((cand) => {
                const isCardChecked = selectedAppIds.has(cand.application_id || cand.id);
                return (
                  <motion.div
                    key={cand.id}
                    layoutId={cand.id}
                    whileHover={{ y: -4, x: -2 }}
                    onClick={() => setSelectedCandidate(cand)}
                    className="relative group cursor-pointer"
                  >
                    <div className="absolute inset-0 bg-black translate-x-1 translate-y-1 transition-transform group-hover:translate-x-2 group-hover:translate-y-2 opacity-10" />
                    <div className="relative bg-white border-2 border-black p-6 space-y-6 transition-all group-hover:shadow-[4px_4px_0px_#000]">
                      <div className="flex justify-between items-start">
                        <div className="flex items-start gap-3">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleSelect(cand.application_id || cand.id);
                            }}
                            className={`w-5 h-5 border-2 border-black flex items-center justify-center transition-all mt-0.5 cursor-pointer ${
                              isCardChecked
                                ? 'bg-black text-[#A7FF2E]'
                                : 'bg-white hover:bg-black/10'
                            }`}
                            title="Select for bulk actions"
                          >
                            {isCardChecked && <span className="text-xs font-black leading-none">✓</span>}
                          </button>
                          <div className="space-y-1">
                            <label className="font-grotesk text-[9px] font-black opacity-30 uppercase tracking-widest block">IDENTIFIER</label>
                            <div className="font-montreal font-black text-sm text-black tracking-widest">
                              {cand.id}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <label className="font-grotesk text-[9px] font-black opacity-30 uppercase tracking-widest block">SCORE</label>
                          <div className="font-montreal font-black text-2xl text-black">
                            {cand.confidence}%
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="h-1.5 w-full bg-black/5 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${cand.confidence}%` }}
                            className={`h-full ${cand.confidence > 80 ? 'bg-green-500' : cand.confidence > 50 ? 'bg-yellow-400' : 'bg-red-500'}`}
                          />
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-black/5">
                        <div className="flex items-center gap-2">
                          <span className="font-grotesk text-[8px] font-black border border-black/10 px-2 py-0.5 uppercase">
                            {cand.bias || 'VERIFIED'}
                          </span>
                          {cand.status === 'selected' && (
                            <span className="font-grotesk text-[8px] font-black bg-[#A7FF2E] text-black px-2 py-0.5 uppercase">
                              APPROVED ✓
                            </span>
                          )}
                        </div>
                        <div className="font-grotesk text-[9px] font-black text-black opacity-100 transition-opacity uppercase tracking-widest">
                          DETAILS →
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}

              {column.candidates.length === 0 && (
                <div className="py-20 border-2 border-dashed border-black/10 flex flex-col items-center justify-center opacity-20">
                  <div className="w-8 h-8 border-2 border-black rounded-full mb-4 opacity-20" />
                  <span className="font-grotesk text-[9px] uppercase tracking-[0.2em]">Void Stream</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* DETAIL MODAL */}
      <AnimatePresence>
        {selectedCandidate && (
          <div className="fixed inset-0 z-[300] flex items-center justify-center p-6 md:p-12">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedCandidate(null)}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="relative w-full max-w-4xl bg-[#E6E6E3] border-4 border-black p-8 md:p-12 overflow-y-auto max-h-[90vh] shadow-[24px_24px_0px_rgba(0,0,0,0.2)]"
            >
              <div className="flex justify-between items-start mb-12">
                <div className="space-y-4">
                  <span className={`inline-block px-4 py-1.5 font-grotesk font-black text-[10px] tracking-[0.2em] uppercase ${
                    selectedCandidate.status === 'needs_review'
                      ? 'bg-yellow-400 text-black'
                      : selectedCandidate.status === 'selected'
                      ? 'bg-[#A7FF2E] text-black'
                      : selectedCandidate.status === 'matched'
                      ? 'bg-[#00E5FF] text-black'
                      : 'bg-[#FF4D4D] text-white'
                  }`}>
                    {selectedCandidate.status === 'needs_review'
                      ? 'REVIEW REQUIRED'
                      : selectedCandidate.status === 'selected'
                      ? 'SELECTED'
                      : selectedCandidate.status === 'matched'
                      ? 'SHORTLISTED'
                      : 'REJECTED'}
                  </span>
                  <div className="space-y-1">
                    <h3 className="font-montreal font-black text-4xl uppercase tracking-tighter">{selectedCandidate.job_title}</h3>
                    <p className="font-inter text-sm font-bold opacity-60 uppercase">
                      {selectedCandidate.status === 'selected'
                        ? 'OFFER EXTENDED • VERIFIED BY FH-AGENT'
                        : selectedCandidate.status === 'matched'
                        ? 'PIPELINE MATCH COMPLETED • PENDING FINAL DECISION'
                        : selectedCandidate.status === 'needs_review'
                        ? 'HUMAN REVIEW PENDING'
                        : 'AUDIT COMPLETED'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedCandidate(null)}
                  className="flex-shrink-0 whitespace-nowrap font-grotesk font-black text-xs uppercase tracking-[0.3em] bg-black text-white px-6 py-3 hover:bg-white hover:text-black transition-all"
                >
                  [ CLOSE ]
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-1 gap-12">
                <div className="bg-white border-4 border-black p-8 space-y-8">
                  <div className="flex flex-col md:flex-row justify-between items-start gap-8 pb-8 border-b-2 border-black/5">
                    <div className="space-y-1">
                      <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block mb-1">CANDIDATE ID</label>
                      <span className="font-montreal font-black text-2xl uppercase tracking-widest text-black">{selectedCandidate.id}</span>
                    </div>
                    <div className="text-right">
                      <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block mb-2">FINAL SCORE</label>
                      <div className="font-montreal font-black text-5xl tracking-tighter">{selectedCandidate.confidence}<span className="text-sm opacity-50 ml-1">/100</span></div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                    <div className="space-y-6">
                      <label className="font-grotesk text-[11px] font-black opacity-40 uppercase tracking-widest block">TECHNICAL REPERTOIRE</label>
                      <div className="flex flex-wrap gap-2 text-[10px] font-bold uppercase font-inter">
                        {(() => {
                          const flattenSkills = (raw) => {
                            if (!raw) return [];
                            if (Array.isArray(raw)) {
                              return raw.map(s => (typeof s === "string" ? s : (s.name || s.skill || ""))).filter(Boolean);
                            }
                            if (typeof raw === "object") {
                              const combined = [
                                ...(raw.core || []),
                                ...(raw.frameworks || []),
                                ...(raw.infrastructure || []),
                                ...(raw.tools || [])
                              ];
                              return combined.map(s => (typeof s === "string" ? s : (s.name || s.skill || ""))).filter(Boolean);
                            }
                            return [];
                          };

                          let skills = flattenSkills(selectedCandidate.feedback?.verified_skills);
                          if (skills.length === 0) {
                            skills = flattenSkills(selectedCandidate.feedback?.matched_skills || selectedCandidate.feedback?.analysis?.matched_skills);
                          }
                          if (skills.length === 0 && selectedCandidate.candidate_details?.skills) {
                            skills = flattenSkills(selectedCandidate.candidate_details.skills);
                          }
                          if (skills.length === 0 && selectedCandidate.verified_skills) {
                            skills = flattenSkills(selectedCandidate.verified_skills);
                          }

                          if (skills.length === 0) {
                            return <span className="opacity-30 italic">No specific technical signatures detected</span>;
                          }

                          return [...new Set(skills.map(s => s.toUpperCase()))].map(s => (
                            <span key={s} className="border-2 border-black px-3 py-1 bg-black/5">{s}</span>
                          ));
                        })()}
                      </div>
                    </div>
                    <div className="space-y-6">
                      <label className="font-grotesk text-[11px] font-black opacity-40 uppercase tracking-widest block">MATCHING FEEDBACK</label>
                      <div className="bg-[#101218] p-6 text-white rounded-sm">
                        <p className="font-inter text-xs font-bold leading-relaxed uppercase tracking-tight opacity-80">
                          {selectedCandidate.status === 'needs_review' ? (
                            <span className="text-yellow-400 font-black">STATED SKILLS CONFLICT WITH SOURCE EVIDENCE. HUMAN AUDIT REQUIRED TO PROCEED.</span>
                          ) : selectedCandidate.feedback?.error?.includes("502") || selectedCandidate.feedback?.recommendation?.includes("error") ? (
                            <span className="text-red-400">CAUTION: Job requirements extraction failed (Provider 502). Matching may be inaccurate due to missing job intent.</span>
                          ) : (
                            selectedCandidate.feedback?.recommendation || selectedCandidate.feedback?.message || (selectedCandidate.status === 'matched' || selectedCandidate.status === 'selected' ? "Verification complete: Technical alignment confirmed." : "Technical signatures analyzed; no significant alignment found.")
                          )}
                        </p>
                      </div>
                    </div>
                  </div>

                  {selectedCandidate.status === 'needs_review' && (
                    <div className="pt-8 border-t-4 border-black space-y-6">
                      <div className="flex items-center gap-4 bg-yellow-400/10 p-4 border-2 border-yellow-400/20">
                        <span className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse" />
                        <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.2em] text-[#1c1c1c]">HUMAN REVIEW PROTOCOL ACTIVE</label>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <button className="px-10 py-6 bg-green-600 text-white font-grotesk text-[11px] font-black uppercase tracking-[0.3em] hover:bg-green-700 hover:scale-[1.02] transition-all flex items-center justify-center gap-3 group/btn">
                          CLEAR EVIDENCE <span className="text-xl group-hover/btn:translate-x-1 transition-transform">→</span>
                        </button>
                        <button className="px-10 py-6 bg-red-600 text-white font-grotesk text-[11px] font-black uppercase tracking-[0.3em] hover:bg-red-700 hover:scale-[1.02] transition-all flex items-center justify-center gap-3 group/btn">
                          RE-ESCALATE HUB <span className="text-xl group-hover/btn:scale-110 transition-transform">↻</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {(selectedCandidate.status === 'selected' || selectedCandidate.status === 'matched') && selectedCandidate.candidate_details && (
                    <div className="pt-8 border-t-4 border-black">
                      <label className={`font-grotesk text-[10px] font-black uppercase tracking-[0.2em] px-4 py-1 inline-block mb-6 ${selectedCandidate.status === 'selected' ? 'text-[#A7FF2E] bg-black' : 'text-black bg-[#00E5FF]'}`}>
                        {selectedCandidate.status === 'selected' ? 'SELECTED CANDIDATE PERSONAL INFOS' : 'SHORTLISTED CANDIDATE PERSONAL INFOS'}
                      </label>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 bg-black/5 p-6 border-2 border-black">
                        <div className="space-y-1">
                          <label className="font-grotesk text-[9px] font-black opacity-40 uppercase tracking-widest block">FULL NAME</label>
                          <span className="font-montreal font-black text-lg uppercase text-black">{selectedCandidate.candidate_details.name}</span>
                        </div>
                        <div className="space-y-1">
                          <label className="font-grotesk text-[9px] font-black opacity-40 uppercase tracking-widest block">VERIFIED EMAIL</label>
                          <span className="font-montreal font-black text-lg uppercase text-black">{selectedCandidate.candidate_details.email}</span>
                        </div>
                        <div className="space-y-1">
                          <label className="font-grotesk text-[9px] font-black opacity-40 uppercase tracking-widest block">INSTITUTION / COLLEGE</label>
                          <span className="font-montreal font-black text-lg uppercase text-black">{selectedCandidate.candidate_details.college || "N/A"}</span>
                        </div>
                        <div className="space-y-1">
                          <label className="font-grotesk text-[9px] font-black opacity-40 uppercase tracking-widest block">VERIFIED SKILLS REPERTOIRE</label>
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {(() => {
                              const v = selectedCandidate.feedback?.verified_skills;
                              let arr = [];
                              if (Array.isArray(v)) arr = v;
                              else if (typeof v === "object" && v) {
                                arr = [...(v.core || []), ...(v.frameworks || []), ...(v.infrastructure || []), ...(v.tools || [])];
                              }
                              if (arr.length === 0 && selectedCandidate.candidate_details?.skills) {
                                arr = selectedCandidate.candidate_details.skills;
                              }
                              if (arr.length === 0) arr = selectedCandidate.feedback?.matched_skills || [];
                              const names = arr.map(item => (typeof item === "string" ? item : (item.name || item.skill || ""))).filter(Boolean);
                              if (names.length === 0) return <span className="font-montreal text-sm opacity-50 font-bold">N/A</span>;
                              return [...new Set(names)].map(n => (
                                <span key={n} className="px-2 py-0.5 bg-black text-white text-[9px] font-grotesk font-black uppercase tracking-wider">
                                  {n}
                                </span>
                              ));
                            })()}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {selectedCandidate.confidence < 60 && (selectedCandidate.status !== 'matched' && selectedCandidate.status !== 'selected') && (
                    <div className="pt-8 border-t-2 border-black/5">
                      <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.2em] text-[#FF4D4D] block mb-4">LACKING AREAS: DEVELOPMENTAL GAPS</label>
                      <ul className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3 font-inter text-[11px] font-bold text-black/60 uppercase tracking-tight list-disc pl-5">
                        {(selectedCandidate.feedback?.missing_skills || selectedCandidate.feedback?.analysis?.missing_skills || []).length > 0 ? (
                          (selectedCandidate.feedback?.missing_skills || selectedCandidate.feedback?.analysis?.missing_skills || []).map((s, i) => (
                            <li key={i}>{s}</li>
                          ))
                        ) : (
                          <li className="list-none pl-0 italic opacity-50">General technical depth verified</li>
                        )}
                      </ul>
                    </div>
                  )}
                  {/* RECRUITER DECISION ACTION BAR */}
                  <div className="pt-8 border-t-4 border-black flex flex-wrap items-center justify-between gap-4 bg-black/5 -mx-8 -mb-8 p-8 mt-8">
                    <div className="flex items-center gap-3">
                      <span className="font-grotesk text-[10px] font-black uppercase tracking-[0.2em] opacity-50">
                        DECISION STATUS:
                      </span>
                      <span className={`text-[10px] font-black uppercase px-3 py-1 ${
                        selectedCandidate.status === 'selected'
                          ? 'bg-[#A7FF2E] text-black font-montreal font-black'
                          : 'bg-[#00E5FF] text-black font-montreal font-black'
                      }`}>
                        {selectedCandidate.status === 'selected' ? 'SELECTION APPROVED ✓' : 'SHORTLISTED CANDIDATE'}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-4">
                      {selectedCandidate.status !== 'selected' ? (
                        <>
                          <button
                            type="button"
                            onClick={async () => {
                              if (onDecision && selectedCandidate.application_id) {
                                await onDecision([selectedCandidate.application_id], 'select');
                                setSelectedCandidate(prev => ({ ...prev, status: 'selected' }));
                              }
                            }}
                            className="px-8 py-3.5 bg-[#A7FF2E] text-black border-2 border-black font-grotesk text-[10px] font-black uppercase tracking-[0.3em] hover:bg-black hover:text-[#A7FF2E] transition-all shadow-[4px_4px_0px_#000] active:translate-x-[2px] active:translate-y-[2px]"
                          >
                            APPROVE CANDIDATE SELECTION ✓
                          </button>
                          <button
                            type="button"
                            onClick={async () => {
                              if (onDecision && selectedCandidate.application_id) {
                                await onDecision([selectedCandidate.application_id], 'reject');
                                setSelectedCandidate(prev => ({ ...prev, status: 'rejected' }));
                              }
                            }}
                            className="px-6 py-3.5 bg-white text-[#FF4D4D] border-2 border-[#FF4D4D] font-grotesk text-[10px] font-black uppercase tracking-[0.2em] hover:bg-[#FF4D4D] hover:text-white transition-all shadow-[3px_3px_0px_#FF4D4D]"
                          >
                            REJECT / DISMISS
                          </button>
                        </>
                      ) : (
                        <>
                          <span className="text-emerald-700 font-grotesk text-[10px] font-black uppercase tracking-wider">
                            OFFER EXTENDED • CANDIDATE NOTIFIED
                          </span>
                          <button
                            type="button"
                            onClick={async () => {
                              if (onDecision && selectedCandidate.application_id) {
                                await onDecision([selectedCandidate.application_id], 'reset');
                                setSelectedCandidate(prev => ({ ...prev, status: 'matched' }));
                              }
                            }}
                            className="px-5 py-2.5 bg-white border-2 border-black font-grotesk text-[9px] font-black uppercase tracking-widest hover:bg-black hover:text-white transition-all shadow-[2px_2px_0px_#000]"
                          >
                            REVOKE SELECTION
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Scroll indicator for horizontal layout */}
      <div className="flex justify-center mt-12 gap-4">
        <div className="w-12 h-1 bg-black/10 rounded-full overflow-hidden">
          <motion.div
            animate={{ x: [-12, 12, -12] }}
            transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
            className="w-1/2 h-full bg-black/40"
          />
        </div>
      </div>
    </div>
  );
}
