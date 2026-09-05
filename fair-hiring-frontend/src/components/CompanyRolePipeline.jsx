import { useEffect, useMemo, useState, useCallback } from "react";
import { motion } from "framer-motion";
import PipelineGrid from "./PipelineGrid";
import JobDetailsModal from "./JobDetailsModal";
import { api } from "../api/backend";

const STATUS_TO_COLUMN = {
  pending: "hidden", // We don't show the millions of raw applications
  verified: "hidden",
  matched: "selected",
  selected: "selected",
  needs_review: "selected", // Review cases also show up in the main selection hub
  rejected: "rejected",
};

const COLUMN_META = [
  { id: "selected", title: "Selection & Review Hub" },
];

export default function CompanyRolePipeline({ roleId, onBack, onSelectCandidate, onViewSelected }) {
  const companyId = localStorage.getItem("fhn_company_id") || "";
  const [jobs, setJobs] = useState([]);
  const [jobId, setJobId] = useState(roleId || null);
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  useEffect(() => {
    if (!companyId) return;
    (async () => {
      try {
        setLoading(true);
        const js = await api.listCompanyJobs(companyId);
        setJobs(Array.isArray(js) ? js : []);
        if (!jobId && Array.isArray(js) && js.length) setJobId(js[0].id);
      } catch (e) {
        console.warn("Failed to load jobs", e);
      } finally {
        setLoading(false);
      }
    })();
  }, [companyId]);

  const refreshApps = useCallback(async (jid) => {
    if (!companyId || !jid) return;
    try {
      setLoading(true);
      const data = await api.listJobApplications(companyId, jid);
      setApps(Array.isArray(data) ? data : []);
    } catch (e) {
      console.warn("Failed to load applications", e);
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  useEffect(() => {
    if (roleId) setJobId(roleId);
  }, [roleId]);

  useEffect(() => {
    refreshApps(jobId);
  }, [jobId, refreshApps]);

  const columns = useMemo(() => {
    const byCol = {};
    COLUMN_META.forEach(c => byCol[c.id] = []);

    // Use a Map to de-duplicate by anon_id across all status stages
    const latestAppsMap = new Map();
    for (const a of apps) {
      const existing = latestAppsMap.get(a.anon_id);
      if (!existing || new Date(a.created_at) > new Date(existing.created_at)) {
        latestAppsMap.set(a.anon_id, a);
      }
    }

    const currentJob = jobs.find(j => String(j.id) === String(jobId));

    for (const a of latestAppsMap.values()) {
      const col = STATUS_TO_COLUMN[a.status] || "applied";
      if (byCol[col]) {
        byCol[col].push({
          application_id: a.application_id,
          id: a.anon_id,
          confidence: a.match_score ?? 0,
          bias: (a.feedback?.message ? "Feedback" : "—"),
          stage: col,
          breakdown: a.feedback?.breakdown,
          status: a.status,
          feedback: a.feedback,
          candidate_details: a.candidate_details,
          job_title: currentJob?.title || "Technical Role"
        });
      }
    }

    return COLUMN_META.map((c) => ({
      id: c.id,
      title: c.title,
      candidates: byCol[c.id],
    }));
  }, [apps, jobs, jobId]);

  const runMatching = async () => {
    if (!companyId || !jobId) return;
    try {
      setRunning(true);
      await api.runMatching(companyId, jobId);
      await refreshApps(jobId);
    } catch (e) {
      console.error(e);
      alert("Run matching failed. See console for details.");
    } finally {
      setRunning(false);
    }
  };

  const handleDecision = async (applicationIds, action, note) => {
    if (!companyId || !jobId || !applicationIds?.length) return;
    try {
      await api.decideApplications(companyId, jobId, applicationIds, action, note);
      await refreshApps(jobId);
    } catch (e) {
      console.error("Decision failed:", e);
      alert("Failed to update candidate status: " + (e.message || "Unknown error"));
    }
  };

  const [finalizing, setFinalizing] = useState(false);
  const handleAutoFinalize = async () => {
    if (!companyId || !jobId) return;
    const currentJob = jobs.find(j => String(j.id) === String(jobId));
    const quota = currentJob?.max_participants || 50;
    const confirmed = window.confirm(
      `Auto-finalize candidates based on merit rank?\n\nThis will select the top ${quota} ranked candidates (Approved Selection) and provide detailed developmental feedback to remaining applicants.`
    );
    if (!confirmed) return;

    try {
      setFinalizing(true);
      const res = await api.autoFinalizeJob(companyId, jobId);
      alert(`Auto-finalization complete!\n• Selected: ${res.selected_count}\n• Rejected with reports: ${res.rejected_count}\n• Quota: ${res.quota}`);
      await refreshApps(jobId);
    } catch (e) {
      console.error("Auto-finalize failed:", e);
      alert("Failed to auto-finalize: " + (e.message || "Unknown error"));
    } finally {
      setFinalizing(false);
    }
  };

  const [deleting, setDeleting] = useState(false);
  const handleDeleteJob = async () => {
    if (!companyId || !jobId) return;
    const currentJob = jobs.find(j => String(j.id) === String(jobId));
    const confirmDelete = window.confirm(
      `Are you sure you want to delete the job "${currentJob?.title || jobId}"? This will remove all associated applications and candidate data.`
    );
    if (!confirmDelete) return;

    try {
      setDeleting(true);
      await api.deleteJob(companyId, jobId);
      alert("Job deleted successfully.");
      if (onBack) {
        onBack();
      }
    } catch (e) {
      console.error("Failed to delete job:", e);
      alert("Failed to delete job: " + (e.message || "Unknown error"));
    } finally {
      setDeleting(false);
    }
  };

  const approvedCandidates = useMemo(() => {
    return apps.filter(a => a.status === "selected");
  }, [apps]);

  const approvedEmails = useMemo(() => {
    const list = [];
    const seen = new Set();
    for (const a of approvedCandidates) {
      const email = a.candidate_details?.email;
      if (email && email.includes("@") && !seen.has(email)) {
        seen.add(email);
        list.push({
          email: email,
          name: a.candidate_details?.name || a.anon_id || "Candidate",
          anonId: a.anon_id,
          score: a.match_score || 0
        });
      }
    }
    return list;
  }, [approvedCandidates]);

  const [isMailMergeModalOpen, setIsMailMergeModalOpen] = useState(false);

  const handleGmailMailMerge = (customEmails = null) => {
    const emailList = customEmails || approvedEmails.map(c => c.email);
    if (emailList.length === 0) {
      alert("No approved candidates with email addresses found to send mail.");
      return;
    }

    const currentJob = jobs.find(j => String(j.id) === String(jobId));
    const roleTitle = currentJob?.title || "Technical Role";
    const subject = `Offer of Technical Selection: ${roleTitle} — Fair Hiring Network`;
    const body = `Dear Candidate,

Congratulations! Following our technical signature verification, problem-solving benchmarks, and bias-neutral assessment on the Fair Hiring Network, we are pleased to inform you that you have been approved and selected for the ${roleTitle} role.

Our engineering team was exceptionally impressed by your verified skills and merit rank.

Next Steps:
Please reply to this email at your earliest convenience to confirm your availability for our technical onboarding and offer walkthrough.

Sincerely,
${companyId ? `The ${companyId} Talent Acquisition Team` : "Hiring Team"}
Fair Hiring Network (Cryptographically Verified Signature Selection)`;

    const toParam = emailList.join(",");
    const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(toParam)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

    window.open(gmailUrl, "_blank", "noopener,noreferrer");
    setIsMailMergeModalOpen(true);
  };

  const handleOpenIndividualGmail = () => {
    const currentJob = jobs.find(j => String(j.id) === String(jobId));
    const roleTitle = currentJob?.title || "Technical Role";
    const subject = `Offer of Technical Selection: ${roleTitle} — Fair Hiring Network`;

    approvedEmails.forEach((c) => {
      const candidateBody = `Dear ${c.name || 'Candidate'},

Congratulations! Following our technical signature verification and merit evaluation on the Fair Hiring Network, you have been selected for the ${roleTitle} role.

Next Steps:
Please reply to confirm your availability for an onboarding discussion.

Sincerely,
${companyId ? `The ${companyId} Talent Acquisition Team` : "Hiring Team"}`;

      const url = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(c.email)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(candidateBody)}`;
      window.open(url, "_blank", "noopener,noreferrer");
    });
  };

  return (
    <div className="h-screen overflow-y-auto bg-[#E6E6E3] text-[#1c1c1c]">
      {/* STICKY HEADER */}
      <header className="sticky top-0 left-0 w-full bg-[#E6E6E3] border-b-[3px] border-[#1c1c1c] z-50 px-6 md:px-12 py-6 flex justify-between items-center bg-opacity-95 backdrop-blur-sm">
        <div className="flex items-center gap-6">
          <button
            onClick={onBack}
            className="px-6 py-3 border-[2px] border-[#1c1c1c] font-grotesk text-[10px] font-black uppercase tracking-[0.2em] hover:bg-[#1c1c1c] hover:text-[#E6E6E3] transition-all flex items-center gap-2 group"
          >
            <span className="group-hover:-translate-x-1 transition-transform inline-block">←</span> BACK
          </button>
          <div className="h-10 w-[2px] bg-[#1c1c1c]/10 hidden md:block"></div>
          <div className="flex items-center gap-4">
            <div className="w-8 h-[2px] bg-[#1c1c1c]"></div>
            <span className="font-montreal font-black text-sm md:text-base tracking-[0.2em] uppercase text-[#1c1c1c]">
              ROLE PIPELINE: {jobs.find(j => String(j.id) === String(jobId))?.title}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="font-mono text-[9px] font-black opacity-30 uppercase tracking-widest text-[#1c1c1c]">
            ROLE REF: {jobId || 'R-101'}
          </div>
          <div className="px-3 py-1 bg-[#A7FF2E] text-black font-grotesk text-[8px] font-black uppercase tracking-widest rounded-full border border-black/10 shadow-sm">
            INTELLIGENCE v3 ACTIVE
          </div>
          <div className="h-4 w-[1px] bg-black/10" />
          {approvedEmails.length > 0 && (
            <button
              onClick={() => handleGmailMailMerge()}
              className="px-4 py-2 border-2 border-black bg-[#A7FF2E] text-black font-grotesk text-[9px] font-black uppercase tracking-widest hover:bg-black hover:text-[#A7FF2E] transition-all shadow-[3px_3px_0px_#000] flex items-center gap-1.5 cursor-pointer"
            >
              <span>✉</span>
              <span>SEND MAIL ({approvedEmails.length})</span>
            </button>
          )}
          <button
            onClick={runMatching}
            disabled={running}
            className={`px-4 py-2 border border-black/10 transition-all font-grotesk text-[9px] font-black uppercase tracking-widest ${running ? 'bg-gray-200 cursor-not-allowed opacity-50' : 'bg-black text-white hover:bg-[#1c1c1c]'}`}
          >
            {running ? "ENGINE RUNNING..." : "RE-RUN MATCHING ENGINE"}
          </button>
          <button
            onClick={handleAutoFinalize}
            disabled={finalizing}
            className={`px-4 py-2 border-2 border-black font-grotesk text-[9px] font-black uppercase tracking-widest transition-all ${
              finalizing ? 'bg-gray-200 cursor-not-allowed opacity-50' : 'bg-[#A7FF2E] text-black hover:bg-black hover:text-[#A7FF2E] shadow-[3px_3px_0px_#000]'
            }`}
          >
            {finalizing ? "FINALIZING..." : `AUTO-FINALIZE TOP ${jobs.find(j => String(j.id) === String(jobId))?.max_participants || 50}`}
          </button>
          <button
            onClick={() => setIsDetailsOpen(true)}
            className="px-6 py-2 border-2 border-black bg-white font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-black hover:text-white transition-all shadow-[4px_4px_0px_#000]"
          >
            VERIFY ROLE SPEC
          </button>
          <button
            onClick={handleDeleteJob}
            disabled={deleting}
            className="px-5 py-2 border-2 border-[#FF4D4D] bg-[#FF4D4D] text-white font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-red-700 transition-all shadow-[4px_4px_0px_#000] active:translate-x-[2px] active:translate-y-[2px]"
          >
            {deleting ? "DELETING..." : "DELETE ROLE"}
          </button>
        </div>
      </header>

      <main className="max-w-[1440px] mx-auto px-6 md:px-12 py-12">
        <div className="mb-20">
          <h1 className="font-montreal font-black text-6xl md:text-8xl uppercase tracking-tighter leading-none mb-4">
            CANDIDATE FLOW
          </h1>
          <p className="font-inter text-sm font-bold opacity-60 uppercase tracking-tight max-w-2xl">
            Live technical signature matching across distributed evaluation nodes.
          </p>
        </div>

        {loading ? (
          <div className="py-24 flex items-center justify-center font-grotesk text-xs font-black uppercase tracking-[0.3em] opacity-30">
            Analyzing Data Streams...
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "circOut" }}
          >
            <PipelineGrid
              columns={columns}
              onDecision={handleDecision}
              onMailMerge={() => handleGmailMailMerge()}
              approvedEmails={approvedEmails}
            />
          </motion.div>
        )}
      </main>

      <JobDetailsModal
        isOpen={isDetailsOpen}
        onClose={() => setIsDetailsOpen(false)}
        job={jobs.find(j => String(j.id) === String(jobId))}
      />

      {/* CANDIDATE MAIL HELPER MODAL */}
      {isMailMergeModalOpen && (
        <div
          className="fixed inset-0 z-[200] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setIsMailMergeModalOpen(false)}
        >
          <div
            className="bg-white border-4 border-black p-8 max-w-xl w-full shadow-[8px_8px_0px_#000] space-y-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start border-b-2 border-black pb-4">
              <div>
                <span className="px-2.5 py-1 bg-[#A7FF2E] text-black font-grotesk text-[9px] font-black uppercase tracking-wider">
                  CANDIDATE DISPATCH
                </span>
                <h3 className="font-montreal font-black text-2xl uppercase tracking-tight mt-2">
                  Send Selection Notifications
                </h3>
              </div>
              <button
                onClick={() => setIsMailMergeModalOpen(false)}
                className="text-xl font-bold hover:opacity-50"
              >
                ✕
              </button>
            </div>

            <div className="bg-[#101218] p-4 text-white space-y-3 font-mono text-xs">
              <div className="flex justify-between items-center text-[#A7FF2E] border-b border-white/10 pb-2">
                <span>APPROVED CANDIDATES ({approvedEmails.length})</span>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(approvedEmails.map(c => c.email).join(", "));
                    alert("All email addresses copied to clipboard!");
                  }}
                  className="hover:underline text-[10px] uppercase font-bold"
                >
                  Copy All Emails
                </button>
              </div>
              <div className="max-h-40 overflow-y-auto space-y-1.5 pr-2">
                {approvedEmails.map((c, i) => (
                  <div key={i} className="flex justify-between text-white/80 text-[11px]">
                    <span className="font-bold text-white">{c.name} ({c.anonId})</span>
                    <span className="text-[#A7FF2E]">{c.email}</span>
                  </div>
                ))}
              </div>
            </div>

            <p className="font-inter text-xs text-black/70 leading-relaxed font-semibold">
              Gmail compose opened with the candidate email addresses pre-filled for direct selection notifications.
            </p>

            <div className="flex flex-wrap gap-3 pt-2">
              <button
                onClick={() => handleGmailMailMerge()}
                className="flex-1 py-3 bg-[#A7FF2E] text-black border-2 border-black font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-black hover:text-[#A7FF2E] transition-all shadow-[3px_3px_0px_#000]"
              >
                OPEN GMAIL ↗
              </button>
              {approvedEmails.length > 1 && (
                <button
                  onClick={handleOpenIndividualGmail}
                  className="py-3 px-4 bg-white text-black border-2 border-black font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-black hover:text-white transition-all shadow-[3px_3px_0px_#000]"
                  title="Opens separate Gmail compose tabs for each candidate"
                >
                  OPEN INDIVIDUAL TABS ({approvedEmails.length})
                </button>
              )}
              <button
                onClick={() => setIsMailMergeModalOpen(false)}
                className="py-3 px-5 border-2 border-black font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-black hover:text-white transition-all"
              >
                CLOSE
              </button>
            </div>
          </div>
        </div>
      )}
      {/* GRID OVERLAY */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03] z-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]" />
    </div>
  );
}
