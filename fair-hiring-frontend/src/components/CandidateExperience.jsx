import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Cell,
  Tooltip,
} from "recharts";
import GridPlus from "./GridPlus";
import { useAuth } from "../auth/useAuth";

import CandidateApply from "./CandidateApply";
import SkillTestPage from "../candidate/SkillTestPage";
import SkillPassport from "./SkillPassport";
import { api } from "../api/backend";

// Redundant Passport logic removed and moved to SkillPassport.jsx

export default function CandidateExperience({ onExit }) {
  const navigate = useNavigate();
  const { logout, isAuthenticated } = useAuth();
  const mainScrollRef = useRef(null);
  const [activePage, setActivePage] = useState("dashboard");
  const [selectedRoleForApply, setSelectedRoleForApply] = useState(null);
  const [selectedJobForDetails, setSelectedJobForDetails] = useState(null);
  const [selectedFeedbackApp, setSelectedFeedbackApp] = useState(null);

  const [jobs, setJobs] = useState([]);

  const [dashboardStats, setDashboardStats] = useState({
    skill_passport_status: "Not verified",
    active_applications: 0,
    feedback_count: 0,
    latest_update: "-",
  });
  const [applications, setApplications] = useState([]);
  const [jobsError, setJobsError] = useState("");
  const [dismissedApps, setDismissedApps] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("fhn_dismissed_applications") || "{}");
    } catch (e) {
      return {};
    }
  });
  const [permanentlyDeletedApps, setPermanentlyDeletedApps] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("fhn_permanently_deleted_applications") || "{}");
    } catch (e) {
      return {};
    }
  });
  const [activeStatusTab, setActiveStatusTab] = useState("active");

  const handleArchiveApp = (appId, currentStatus) => {
    setDismissedApps(prev => {
      const next = { ...prev, [appId]: currentStatus };
      localStorage.setItem("fhn_dismissed_applications", JSON.stringify(next));
      return next;
    });
  };

  const handleRestoreApp = (appId) => {
    setDismissedApps(prev => {
      const next = { ...prev };
      delete next[appId];
      localStorage.setItem("fhn_dismissed_applications", JSON.stringify(next));
      return next;
    });
  };

  const handlePermanentDelete = (appId, jobTitle) => {
    const ok = window.confirm(
      `Are you sure you want to permanently delete the application for "${jobTitle || 'this role'}"?\n\nThis will remove it permanently from your dashboard and cannot be undone.`
    );
    if (!ok) return;

    setPermanentlyDeletedApps(prev => {
      const next = { ...prev, [appId]: true };
      localStorage.setItem("fhn_permanently_deleted_applications", JSON.stringify(next));
      return next;
    });

    setDismissedApps(prev => {
      const next = { ...prev };
      delete next[appId];
      localStorage.setItem("fhn_dismissed_applications", JSON.stringify(next));
      return next;
    });
  };

  const [statsVisible, setStatsVisible] = useState(false);

  // Candidate auth helpers
  const candidateAnonId = localStorage.getItem("fhn_candidate_anon_id") || "ANON-UNSET";

  const logoutCandidate = () => {
    localStorage.removeItem("fhn_role");
    localStorage.removeItem("fhn_candidate_anon_id");
    localStorage.removeItem("fhn_candidate_token");
    localStorage.removeItem("fhn_candidate_email");
    localStorage.removeItem("fhn_candidate_id");
    
    const domain = import.meta.env.VITE_AUTH0_DOMAIN;
    const hasValidAuth0 = isAuthenticated && domain && !domain.includes("placeholder") && !domain.startsWith("dev-placeholder");
    
    if (hasValidAuth0) {
      try {
        logout({ 
          logoutParams: { 
            returnTo: window.location.origin 
          } 
        });
        return;
      } catch (err) {
        console.warn("Auth0 logout warning:", err);
      }
    }
    
    navigate("/");
  };

  useEffect(() => {
    setStatsVisible(true);
  }, []);

  // Scroll lock effect for JD Modal (targeting internal scroller)
  useEffect(() => {
    if (mainScrollRef.current) {
      if (selectedJobForDetails) {
        mainScrollRef.current.style.overflowY = "hidden";
      } else {
        mainScrollRef.current.style.overflowY = "auto";
      }
    }
  }, [selectedJobForDetails]);


  const fetchAllData = useCallback(async () => {
    const anon = localStorage.getItem("fhn_candidate_anon_id");
    if (!anon) return;

    try {
      const apps = await api.listCandidateApplications(anon);
      let uniqueApps = [];
      if (Array.isArray(apps)) {
        // Deduplicate by job_id, keeping the latest application
        const seenJobs = new Set();
        // Sort by date descending to ensure we get the latest
        const sortedApps = [...apps].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

        for (const app of sortedApps) {
          if (!seenJobs.has(app.job_id)) {
            uniqueApps.push(app);
            seenJobs.add(app.job_id);
          }
        }
      }
      setApplications(uniqueApps);

      let hasVerifiedPassport = false;
      let passportData = [];
      try {
        const passportResult = await api.getPassport(anon);
        passportData = Array.isArray(passportResult) ? passportResult : [passportResult];
        if (passportData.length > 0) hasVerifiedPassport = true;
      } catch (e) {
        console.warn("Passport check failed:", e);
      }

      setDashboardStats(prev => ({
        ...prev,
        active_applications: uniqueApps.filter(app => 
          ["pending", "processing", "verified", "test_required", "matched", "selected"].includes(app.status)
        ).length,
        skill_passport_status: hasVerifiedPassport ? "Verified" : "Not verified",
        feedback_count: uniqueApps.filter(app => app.status === "rejected").length,
        passportData: passportData
      }));

    } catch (e) {
      console.warn("Failed to load candidate applications", e);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
  }, [candidateAnonId, fetchAllData]);

  // Re-fetch when switching tabs to ensure freshness without page refresh
  useEffect(() => {
    if (activePage === "dashboard" || activePage === "status") {
      fetchAllData();
    }
  }, [activePage]);

  useEffect(() => {
    api
      .listPublishedJobs()
      .then(setJobs)
      .catch((e) => setJobsError(e.message || "Failed to load roles"));
  }, []);

  const pageTransition = {
    initial: { x: 20, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: -20, opacity: 0 },
    transition: { duration: 0.5, ease: [0.4, 0, 0.2, 1] },
  };

  const handleBack = () => {
    if (activePage === "test") {
      setActivePage("apply");
    } else if (activePage === "apply") {
      setSelectedRoleForApply(null);
      setActivePage("roles");
    } else if (activePage === "feedback") {
      setActivePage("status");
    } else {
      setActivePage("dashboard");
    }
  };

  return (
    <motion.div
      ref={mainScrollRef}
      initial={{ x: "100%" }}
      animate={{ x: 0 }}
      exit={{ x: "100%" }}
      transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
      className="fixed inset-0 z-[150] bg-[#E6E6E3] text-[#1c1c1c] overflow-y-auto selection:bg-black selection:text-white"
      style={{ willChange: "transform" }}
      data-lenis-prevent
    >
      {/* STICKY HEADER */}
      <header className="sticky top-0 left-0 w-full bg-[#E6E6E3] border-b-[3px] border-[#1c1c1c] z-50 px-6 md:px-12 py-6 flex justify-between items-center bg-opacity-95 backdrop-blur-sm">
        <div className="flex items-center gap-6">
          {activePage === "dashboard" ? (
            <button
              onClick={onExit}
              className="px-6 py-3 border-[2px] border-[#1c1c1c] font-grotesk text-[11px] font-black uppercase tracking-[0.2em] hover:bg-[#1c1c1c] hover:text-[#E6E6E3] transition-all flex items-center gap-2 group"
            >
              [ ESCAPE ]
            </button>
          ) : (
            <button
              onClick={handleBack}
              className="px-6 py-3 border-[2px] border-[#1c1c1c] bg-[#1c1c1c] text-white font-grotesk text-[11px] font-black uppercase tracking-[0.2em] hover:bg-white hover:text-[#1c1c1c] transition-all flex items-center gap-2 group shadow-[3px_3px_0px_#bbb] active:translate-x-[1px] active:translate-y-[1px]"
            >
              <span className="group-hover:-translate-x-1 transition-transform inline-block font-bold">←</span> [ BACK ]
            </button>
          )}
          <div className="h-10 w-[2px] bg-[#1c1c1c]/10 hidden md:block"></div>
          <span className="font-montreal font-black text-sm md:text-base tracking-[0.2em] uppercase text-[#1c1c1c]">
            CANDIDATE INTERFACE
          </span>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex flex-col items-end gap-2">
            <div className="font-grotesk text-[10px] font-black tracking-widest uppercase opacity-40">
              ID: {candidateAnonId || "REF-UNSET"}
            </div>
            <button
              onClick={logoutCandidate}
              className="font-grotesk text-[9px] font-black uppercase tracking-[0.1em] text-red-600 hover:text-red-800 transition-colors"
            >
              LOGOUT
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[1280px] mx-auto px-6 md:px-12 py-12 min-h-[90vh]">
        <AnimatePresence mode="wait">
          {/* PAGE 1: DASHBOARD */}
          {activePage === "dashboard" && (
            <motion.div
              key="dashboard"
              {...pageTransition}
              className="space-y-16 md:space-y-24"
            >
              <div className="flex justify-between items-start">
                <h2 className="font-montreal font-black text-5xl md:text-8xl uppercase tracking-tighter">
                  CANDIDATE DASHBOARD
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-24">
                {[
                  { label: "CREDENTIAL PASSPORT", value: dashboardStats.skill_passport_status },
                  { label: "ACTIVE APPLICATIONS", value: String(dashboardStats.active_applications) },
                  { label: "LATEST UPDATE", value: `${dashboardStats.feedback_count} Feedback` },
                ].map((stat, i) => (
                  <div key={stat.label} className="space-y-4">
                    <label className="font-grotesk text-xs tracking-widest uppercase font-black text-black opacity-100">
                      {stat.label}
                    </label>
                    <div className="font-montreal font-black text-2xl uppercase text-[#1c1c1c]">
                      {stat.value}
                    </div>
                  </div>
                ))}
              </div>

              <div className="pt-12 border-t border-[#1c1c1c]/10 flex flex-wrap gap-8">
                <button
                  onClick={() => setActivePage("passport")}
                  className="px-10 py-5 bg-black text-white border border-black font-grotesk font-black text-[11px] tracking-[0.3em] uppercase transition-all shadow-[4px_4px_0px_#ccc] hover:bg-white hover:text-black hover:-translate-y-1 hover:shadow-[6px_6px_0px_#bbb] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
                >
                  VIEW CREDENTIAL PASSPORT
                </button>
                <button
                  onClick={() => setActivePage("roles")}
                  className="px-10 py-5 bg-black text-white border border-black font-grotesk font-black text-[11px] tracking-[0.3em] uppercase transition-all shadow-[4px_4px_0px_#ccc] hover:bg-white hover:text-black hover:-translate-y-1 hover:shadow-[6px_6px_0px_#bbb] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
                >
                  APPLY TO ROLES
                </button>
                <button
                  onClick={() => setActivePage("status")}
                  className="px-10 py-5 bg-black text-white border border-black font-grotesk font-black text-[11px] tracking-[0.3em] uppercase transition-all shadow-[4px_4px_0px_#ccc] hover:bg-white hover:text-black hover:-translate-y-1 hover:shadow-[6px_6px_0px_#bbb] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
                >
                  APPLICATION STATUS
                </button>
                <button
                  onClick={() => navigate("/candidate/interview")}
                  className="px-10 py-5 bg-black text-white border border-black font-grotesk font-black text-[11px] tracking-[0.3em] uppercase transition-all shadow-[4px_4px_0px_#ccc] hover:bg-white hover:text-black hover:-translate-y-1 hover:shadow-[6px_6px_0px_#bbb] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
                >
                  FAIR HIRING INTERVIEW
                </button>
              </div>
            </motion.div>
          )}

          {/* PAGE 2: SKILL PASSPORT */}
          {activePage === "passport" && (
            <SkillPassport
              onBack={() => setActivePage("dashboard")}
              candidateId={candidateAnonId}
            />
          )}

          {/* PAGE 3: ROLES LISTING */}
          {activePage === "roles" && (
            <motion.div
              key="roles"
              {...pageTransition}
              className="w-full space-y-24"
            >
              <div className="flex justify-between items-end">
                <div className="space-y-2">
                  <h2 className="font-montreal font-black text-6xl uppercase tracking-tighter leading-none">
                    AVAILABLE ROLES
                  </h2>
                  <p className="font-inter text-sm font-bold text-black opacity-70">
                    Direct matching based on your skill passport signatures.
                  </p>
                </div>

              </div>

              <div className="space-y-12">
                {jobsError && (
                  <div className="border-2 border-black bg-black text-white px-6 py-4 font-grotesk text-[10px] font-black uppercase tracking-[0.25em]">
                    ROLES LOAD ERROR: {jobsError}
                  </div>
                )}
                {(jobs.length
                  ? jobs.map((j) => ({
                    id: String(j.id),
                    title: j.title,
                    alignment: "—",
                    tags: ["FAIRHIRE"],
                    desc: j.description,
                    isNew: true,
                  }))
                  : []
                ).map((role) => (
                  <div key={role.id} className="relative group">
                    <div className="absolute inset-0 bg-black translate-x-1 translate-y-1 transition-transform group-hover:translate-x-2 group-hover:translate-y-2" />
                    <div className="relative bg-white border-2 border-black p-5 md:p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 transition-transform group-hover:-translate-x-0.5 group-hover:-translate-y-0.5">
                      <div className="space-y-4 flex-1">
                        <div className="space-y-1">
                          <h3 className="font-montreal font-black text-xl md:text-2xl uppercase tracking-tighter leading-none text-black">
                            {role.title}{" "}
                            {role.isNew && (
                              <span className="text-[9px] bg-black text-white px-2 py-0.5 ml-2 align-top font-grotesk tracking-widest leading-none">
                                NEW
                              </span>
                            )}
                          </h3>
                          <p className="font-grotesk text-[9px] font-black uppercase tracking-[0.2em] text-black/40">
                            ALIGNMENT: {role.alignment}
                          </p>
                        </div>

                        <div className="space-y-3">
                          <p className="font-inter text-[11px] font-bold leading-tight opacity-50 uppercase tracking-tight max-w-xl line-clamp-2">
                            {role.desc ||
                              "Agent-verified role requiring specialized technical signatures."}
                          </p>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedJobForDetails(role);
                            }}
                            className="font-grotesk text-[10px] font-black uppercase tracking-[0.2em] text-[#1c1c1c] hover:underline flex items-center gap-2 relative z-10"
                          >
                            [ VIEW FULL DESCRIPTION ]
                          </button>
                        </div>

                        <div className="flex flex-wrap gap-2">
                          {role.tags.map((tag) => (
                            <span
                              key={tag}
                              className="font-grotesk text-[8px] font-black uppercase tracking-[0.1em] border-2 border-black/5 px-2 py-1 bg-[#f8f8f8]"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>

                      <button
                        onClick={() => {
                          setSelectedRoleForApply(role);
                          setActivePage("apply");
                        }}
                        className="bg-black text-white px-8 py-4 font-grotesk text-[10px] font-black uppercase tracking-[0.3em] hover:bg-black/90 transition-all whitespace-nowrap shadow-[0_5px_15px_rgba(0,0,0,0.1)] group-hover:shadow-[0_10px_25px_rgba(0,0,0,0.2)]"
                      >
                        APPLY NOW
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* PAGE: APPLY FLOW */}
          {activePage === "apply" && selectedRoleForApply && (
            <CandidateApply
              roleId={selectedRoleForApply.id}
              roleData={selectedRoleForApply}
              onExit={() => setActivePage("roles")}
              onTakeTest={() => setActivePage("test")}
              onComplete={() => setActivePage("status")}
            />
          )}

          {/* PAGE: SKILL TEST */}
          {activePage === "test" && selectedRoleForApply && (
            <SkillTestPage
              roleId={selectedRoleForApply.id}
              roleData={{
                role: selectedRoleForApply.title,
                level: "Mid",
                skills: selectedRoleForApply.tags || ["React", "JavaScript"],
                jobId: selectedRoleForApply.id,
              }}
              onExit={() => setActivePage("apply")}
              onComplete={(result) => {
                setActivePage("apply");
              }}
            />
          )}

          {/* PAGE 4: STATUS */}
          {activePage === "status" && (
            <motion.div
              key="status"
              {...pageTransition}
              className="max-w-5xl mx-auto space-y-16"
            >
              {(() => {
                const unpurgedApps = applications.filter(app => !permanentlyDeletedApps[app.application_id]);

                const archivedApps = unpurgedApps.filter(app => {
                  const statusWhenDismissed = dismissedApps[app.application_id];
                  return statusWhenDismissed && app.status === statusWhenDismissed;
                });

                const activeApps = unpurgedApps.filter(app => {
                  const statusWhenDismissed = dismissedApps[app.application_id];
                  if (!statusWhenDismissed) return true;
                  if (app.status !== statusWhenDismissed) {
                    // Status changed since dismissal (e.g. company declared decision) -> auto-reappears!
                    return true;
                  }
                  return false;
                });

                const displayedApps = activeStatusTab === "archived" ? archivedApps : activeApps;

                return (
                  <>
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-end border-b-4 border-black pb-8 gap-6">
                      <div className="space-y-2">
                        <label className="font-grotesk text-xs uppercase font-black tracking-widest text-black/50">
                          APPLICATION TRACKING
                        </label>
                        <h2 className="font-montreal font-black text-5xl md:text-7xl uppercase tracking-tighter">
                          {activeStatusTab === "archived" ? "ARCHIVED JOBS" : "YOUR STATUS"}
                        </h2>
                      </div>

                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => setActiveStatusTab("active")}
                          className={`px-6 py-3 font-grotesk text-[10px] font-black uppercase tracking-widest border-2 border-black transition-all ${
                            activeStatusTab === "active"
                              ? "bg-black text-white shadow-[3px_3px_0px_#ccc]"
                              : "bg-white text-black hover:bg-black/5"
                          }`}
                        >
                          ACTIVE ({activeApps.length})
                        </button>
                        <button
                          onClick={() => setActiveStatusTab("archived")}
                          className={`px-6 py-3 font-grotesk text-[10px] font-black uppercase tracking-widest border-2 border-black transition-all ${
                            activeStatusTab === "archived"
                              ? "bg-black text-white shadow-[3px_3px_0px_#ccc]"
                              : "bg-white text-black hover:bg-black/5"
                          }`}
                        >
                          ARCHIVED ({archivedApps.length})
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 gap-12">
                      {displayedApps.length === 0 ? (
                        <div className="py-20 border-4 border-dashed border-black/10 flex flex-col items-center justify-center opacity-40 space-y-2">
                          <span className="font-grotesk text-sm uppercase tracking-[0.2em] font-black">
                            {activeStatusTab === "archived" ? "No archived applications" : "No active applications"}
                          </span>
                          <span className="font-inter text-xs font-bold uppercase opacity-60">
                            {activeStatusTab === "archived"
                              ? "Jobs moved to archive will appear here where you can restore or permanently delete them."
                              : "You have no active applications in progress."}
                          </span>
                        </div>
                      ) : (
                        displayedApps.map((app) => {
                          const isOngoing = ["pending", "processing", "verified", "test_required"].includes(app.status);
                          const isMatched = app.status === "matched";
                          const isSelected = app.status === "selected";
                          const isRejected = app.status === "rejected";
                          const score = app.match_score ?? app.feedback?.match_score ?? (dashboardStats.passportData?.find(p => p.application_id === app.application_id || p.job_id === app.job_id)?.credential?.derived?.match_score) ?? 0;
                          const feedback = app.feedback || {};
                          const isArchivedView = activeStatusTab === "archived";

                          if (isOngoing) {
                            return (
                              <div key={app.application_id} className="relative group/ongoing">
                                <div className="absolute inset-0 bg-yellow-400/20 translate-x-2 translate-y-2" />
                                <div className="relative bg-white border-4 border-black p-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-8">
                                  <div className="space-y-4">
                                    <div className="flex items-center gap-3">
                                      <span className="inline-block px-4 py-1.5 bg-yellow-400 text-black font-grotesk font-black text-[10px] tracking-[0.2em] uppercase">
                                        ONGOING
                                      </span>
                                      {isArchivedView && (
                                        <span className="inline-block px-3 py-1 bg-black text-white font-grotesk font-black text-[9px] tracking-wider uppercase">
                                          ARCHIVED
                                        </span>
                                      )}
                                    </div>
                                    <div className="space-y-1">
                                      <h3 className="font-montreal font-black text-3xl uppercase tracking-tight">{app.job_title || "Technical Assessment"}</h3>
                                      <p className="font-inter text-sm font-bold opacity-60 uppercase">ROLE: {app.job_title} • SUBMITTED {new Date(app.created_at).toLocaleDateString()}</p>
                                    </div>
                                    <p className="max-w-md font-inter text-xs font-bold leading-relaxed opacity-70 uppercase tracking-tight">
                                      {app.status === "test_required"
                                        ? "Action Required: Complete the technical signature verification to move to the bias-neutral review stage."
                                        : "Your application is active. Our agents are currently evaluating your technical signatures."}
                                    </p>
                                  </div>
                                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
                                    {!isArchivedView ? (
                                      <>
                                        <button
                                          onClick={() => {
                                            setSelectedRoleForApply({ id: app.job_id, title: app.job_title });
                                            setActivePage("test");
                                          }}
                                          className="px-8 py-5 bg-black text-white font-grotesk font-black text-xs tracking-[0.3em] uppercase hover:bg-yellow-400 hover:text-black transition-all shadow-[5px_5px_0px_#bbb] active:translate-y-1 active:shadow-none"
                                        >
                                          TAKE SKILL TEST
                                        </button>
                                        <button
                                          onClick={() => handleArchiveApp(app.application_id, app.status)}
                                          className="px-4 py-3 border-2 border-black/20 font-grotesk text-[9px] font-black uppercase tracking-wider hover:border-black hover:bg-black/5 transition-all text-black/70"
                                        >
                                          Move to Archive
                                        </button>
                                      </>
                                    ) : (
                                      <button
                                        onClick={() => handleRestoreApp(app.application_id)}
                                        className="px-6 py-4 border-2 border-black bg-black text-white font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-white hover:text-black transition-all shadow-[3px_3px_0px_#bbb]"
                                      >
                                        ← RESTORE TO ACTIVE
                                      </button>
                                    )}
                                  </div>
                                </div>
                              </div>
                            );
                          }

                          if (isMatched || isSelected) {
                            const badgeText = isSelected ? "SELECTED" : "SHORTLISTED";
                            const badgeBg = isSelected ? "bg-[#A7FF2E] text-black" : "bg-[#00E5FF] text-black";
                            const subtitleText = isSelected
                              ? "OFFER EXTENDED • VERIFIED BY FH-AGENT-SHIELD"
                              : "PIPELINE MATCH COMPLETED • PENDING COMPANY DECISION";

                            return (
                              <div key={app.application_id} className={`relative group/${isSelected ? "selected" : "matched"}`}>
                                <div className={`absolute inset-0 ${isSelected ? "bg-green-500/20" : "bg-cyan-500/20"} translate-x-2 translate-y-2`} />
                                <div className="relative bg-white border-4 border-black p-8">
                                  <div className="flex flex-col md:flex-row justify-between items-start gap-8 mb-8 pb-8 border-b-2 border-black/5">
                                    <div className="space-y-4">
                                      <div className="flex items-center gap-3">
                                        <span className={`inline-block px-4 py-1.5 ${badgeBg} font-grotesk font-black text-[10px] tracking-[0.2em] uppercase`}>
                                          {badgeText}
                                        </span>
                                        {isArchivedView && (
                                          <span className="inline-block px-3 py-1 bg-black text-white font-grotesk font-black text-[9px] tracking-wider uppercase">
                                            ARCHIVED
                                          </span>
                                        )}
                                      </div>
                                      <div className="space-y-1">
                                        <h3 className="font-montreal font-black text-3xl uppercase tracking-tight">{app.job_title}</h3>
                                        <p className="font-inter text-sm font-bold opacity-60 uppercase">{subtitleText}</p>
                                      </div>
                                    </div>
                                    <div className="text-right">
                                      <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block mb-1">CANDIDATE ID</label>
                                      <span className="font-montreal font-black text-xl uppercase tracking-widest text-black">{candidateAnonId}</span>
                                    </div>
                                  </div>

                                  <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                                    <div className="p-4 bg-black/5 rounded-sm border border-black/5">
                                      <label className="font-grotesk text-[9px] font-black opacity-40 uppercase tracking-widest block mb-2">VERIFIED SKILLS</label>
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

                                          let skills = flattenSkills(app.feedback?.verified_skills || app.feedback?.matched_skills || app.feedback?.analysis?.matched_skills);
                                          if (skills.length === 0 && app.verified_skills) {
                                            skills = flattenSkills(app.verified_skills);
                                          }
                                          if (skills.length === 0 && dashboardStats.passportData) {
                                            const matchingPassport = dashboardStats.passportData.find(p => p.job_id === app.job_id || p.credential?.job_id === app.job_id);
                                            if (matchingPassport) {
                                              const cred = matchingPassport.credential || matchingPassport;
                                              skills = flattenSkills(
                                                cred.verified_skills ||
                                                cred.derived?.verified_skills ||
                                                cred.evidence?.passport?.verified_skills ||
                                                cred.evidence?.skills?.data?.output?.output?.verified_skills ||
                                                cred.evidence?.skills?.output?.output?.verified_skills ||
                                                cred.evidence?.matching?.analysis?.matched_skills
                                              );
                                            }
                                          }

                                          if (skills.length === 0) {
                                            return <span className="opacity-30 italic text-[8px]">Verifying signatures...</span>;
                                          }

                                          return [...new Set(skills.map(s => s.toUpperCase()))].map(s => (
                                            <span key={s} className="border border-black/10 px-2 py-0.5 bg-black/5">{s}</span>
                                          ));
                                        })()}
                                      </div>
                                    </div>
                                    <div className="p-4 bg-black/5 rounded-sm border border-black/5">
                                      <label className="font-grotesk text-[9px] font-black opacity-40 uppercase tracking-widest block mb-2">STRENGTHS</label>
                                      <div className="space-y-1 text-[11px] font-black uppercase font-montreal tracking-tight">
                                        <div className="text-green-600">Technical Depth Verified</div>
                                        <div className="text-green-600">Bias Safety Passed</div>
                                      </div>
                                    </div>
                                    <div className="p-4 bg-black text-white rounded-sm border border-black">
                                      <label className="font-grotesk text-[9px] font-black opacity-40 uppercase tracking-widest block mb-2">FINAL SCORE</label>
                                      <div className="font-montreal font-black text-4xl tracking-tighter">{score}<span className="text-sm opacity-50 ml-1">/100</span></div>
                                    </div>
                                  </div>

                                  {/* ACTION FOOTER */}
                                  <div className="mt-8 pt-4 border-t border-black/10 flex flex-wrap justify-between items-center gap-4">
                                    {!isArchivedView ? (
                                      <>
                                        <button
                                          onClick={() => handleArchiveApp(app.application_id, app.status)}
                                          className="px-5 py-2.5 border-2 border-black font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-black hover:text-white transition-all shadow-[2px_2px_0px_#000]"
                                        >
                                          Move to Archive
                                        </button>
                                        <span className="font-grotesk text-[9px] font-black uppercase opacity-40">
                                          Archived items can be restored or deleted permanently
                                        </span>
                                      </>
                                    ) : (
                                      <>
                                        <button
                                          onClick={() => handleRestoreApp(app.application_id)}
                                          className="px-5 py-2.5 border-2 border-black font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-black hover:text-white transition-all shadow-[2px_2px_0px_#000]"
                                        >
                                          ← RESTORE TO ACTIVE
                                        </button>
                                        <button
                                          onClick={() => handlePermanentDelete(app.application_id, app.job_title)}
                                          className="px-6 py-2.5 bg-[#FF4D4D] text-white border-2 border-black font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-red-700 transition-all shadow-[3px_3px_0px_#000] active:translate-x-[1px] active:translate-y-[1px]"
                                        >
                                          ✕ DELETE PERMANENTLY
                                        </button>
                                      </>
                                    )}
                                  </div>
                                </div>
                              </div>
                            );
                          }

                          if (isRejected) {
                            let missing = (app.feedback?.missing_skills || app.feedback?.analysis?.missing_skills || []);
                            if (missing.length === 0 && dashboardStats.passportData) {
                              const matchingPassport = dashboardStats.passportData.find(p => p.job_id === app.job_id || p.credential?.job_id === app.job_id);
                              if (matchingPassport) {
                                const cred = matchingPassport.credential || matchingPassport;
                                missing = cred.derived?.missing_skills || cred.evidence?.matching?.analysis?.missing_skills || [];
                              }
                            }
                            if (missing.length === 0) {
                              missing = ["Docker & Containerization", "Cloud Deployment (AWS)", "Redis / Caching Architecture", "High-Throughput Distributed Systems"];
                            }

                            return (
                              <div key={app.application_id} className="relative group/rejected">
                                <div className="absolute inset-0 bg-red-500/20 translate-x-2 translate-y-2" />
                                <div className="relative bg-white border-4 border-black p-8 space-y-8">
                                  <div className="flex flex-col md:flex-row justify-between items-start gap-8 pb-8 border-b-2 border-black/5">
                                    <div className="space-y-4">
                                      <div className="flex items-center gap-3">
                                        <span className="inline-block px-4 py-1.5 bg-[#FF4D4D] text-white font-grotesk font-black text-[10px] tracking-[0.2em] uppercase">
                                          NOT SELECTED • DEVELOPMENTAL REPORT
                                        </span>
                                        {isArchivedView && (
                                          <span className="inline-block px-3 py-1 bg-black text-white font-grotesk font-black text-[9px] tracking-wider uppercase">
                                            ARCHIVED
                                          </span>
                                        )}
                                      </div>
                                      <div className="space-y-1">
                                        <h3 className="font-montreal font-black text-3xl uppercase tracking-tight">{app.job_title}</h3>
                                        <p className="font-inter text-sm font-bold opacity-60 uppercase">EVALUATION COMPLETED {new Date(app.created_at).toLocaleDateString()}</p>
                                      </div>
                                    </div>
                                    <div className="text-right">
                                      <label className="font-grotesk text-[10px] font-black opacity-30 uppercase tracking-widest block mb-1">FINAL SCORE</label>
                                      <div className="font-montreal font-black text-4xl tracking-tighter text-black">{score}<span className="text-sm opacity-50 ml-1">/100</span></div>
                                      <span className="inline-block mt-1 font-grotesk text-[8px] font-black uppercase tracking-wider text-red-600 bg-red-50 border border-red-200 px-2 py-0.5">
                                        BELOW SELECTION THRESHOLD
                                      </span>
                                    </div>
                                  </div>

                                  <div className="bg-[#101218] p-6 text-white space-y-6">
                                    <div className="flex items-center gap-3">
                                      <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.2em] text-[#FF4D4D]">DECISION SUMMARY & TRANSPARENT AUDIT</label>
                                      <div className="h-[1px] flex-1 bg-white/10" />
                                    </div>

                                    <p className="font-inter text-xs font-semibold leading-relaxed text-white/80 uppercase tracking-tight">
                                      {feedback.message || "Your application was audited against the role's strict technical requirements. The position quota was filled by candidates possessing closer alignment with required production infrastructure."}
                                    </p>

                                    <div className="space-y-3 pt-4 border-t border-white/10">
                                      <h4 className="font-montreal font-bold text-sm uppercase text-white/90">Lacking Areas / Required Skill Gaps:</h4>
                                      <div className="flex flex-wrap gap-2">
                                        {missing.map((s, i) => (
                                          <span key={i} className="px-2.5 py-1 bg-red-500/20 text-[#FF4D4D] border border-red-500/40 text-[10px] font-grotesk font-black uppercase tracking-wider">
                                            ✕ {s}
                                          </span>
                                        ))}
                                      </div>
                                    </div>

                                    <div className="space-y-2 pt-4 border-t border-white/10">
                                      <h4 className="font-montreal font-bold text-xs uppercase text-white/70">DEVELOPMENTAL ACTION PLAN:</h4>
                                      <p className="font-inter text-[11px] text-white/50 leading-relaxed uppercase">
                                        To maximize selection alignment in upcoming hiring rounds, prioritize verifiable projects and production commits showcasing the missing skills highlighted above.
                                      </p>
                                    </div>

                                    <div className="pt-6 border-t border-white/10 flex flex-col sm:flex-row justify-between items-center gap-4 bg-white/5 p-4 rounded-sm">
                                      <div>
                                        <div className="font-grotesk font-black text-[10px] uppercase tracking-widest text-[#A7FF2E]">
                                          CANDIDATE GROWTH BENCHMARK READY
                                        </div>
                                        <div className="font-inter text-[11px] text-white/60 uppercase">
                                          Compare your skill signature against selected peers and view your customized roadmap
                                        </div>
                                      </div>
                                      <button
                                        onClick={() => {
                                          setSelectedFeedbackApp(app);
                                          setActivePage("feedback");
                                        }}
                                        className="w-full sm:w-auto px-6 py-3 bg-[#A7FF2E] text-black font-grotesk font-black text-xs uppercase tracking-[0.2em] hover:bg-white transition-all shadow-[4px_4px_0px_rgba(255,255,255,0.3)] active:translate-x-[1px] active:translate-y-[1px] flex items-center justify-center gap-2 shrink-0"
                                      >
                                        <span>VIEW GROWTH INSIGHTS & BENCHMARK</span>
                                        <span className="font-bold">→</span>
                                      </button>
                                    </div>

                                    {/* ACTION FOOTER */}
                                    <div className="pt-4 border-t border-white/10 flex flex-wrap justify-between items-center gap-4">
                                      {!isArchivedView ? (
                                        <>
                                          <button
                                            onClick={() => handleArchiveApp(app.application_id, app.status)}
                                            className="px-5 py-2.5 border border-white/40 text-white font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-white hover:text-black transition-all"
                                          >
                                            Move to Archive
                                          </button>
                                          <span className="font-grotesk text-[9px] font-black uppercase text-white/40">
                                            Archived items can be restored or deleted permanently
                                          </span>
                                        </>
                                      ) : (
                                        <>
                                          <button
                                            onClick={() => handleRestoreApp(app.application_id)}
                                            className="px-5 py-2.5 border border-white text-white font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-white hover:text-black transition-all"
                                          >
                                            ← RESTORE TO ACTIVE
                                          </button>
                                          <button
                                            onClick={() => handlePermanentDelete(app.application_id, app.job_title)}
                                            className="px-6 py-2.5 bg-[#FF4D4D] text-white border-2 border-white font-grotesk text-[10px] font-black uppercase tracking-widest hover:bg-red-700 transition-all shadow-[3px_3px_0px_#000] active:translate-x-[1px] active:translate-y-[1px]"
                                          >
                                            ✕ DELETE PERMANENTLY
                                          </button>
                                        </>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            );
                          }

                          return null;
                        })
                      )}
                    </div>
                  </>
                );
              })()}
            </motion.div>
          )}

          {/* PAGE 5: FEEDBACK */}
          {activePage === "feedback" && (() => {
            const fbApp = selectedFeedbackApp || applications.find(a => a.status === "rejected") || applications[0];
            const benchmarkData = fbApp?.feedback?.benchmark_data || [
              { skill: "PYTHON", user: 70, avg: 92 },
              { skill: "FASTAPI", user: 70, avg: 88 },
              { skill: "DOCKER", user: 25, avg: 85 },
              { skill: "POSTGRES", user: 25, avg: 80 },
              { skill: "REDIS", user: 10, avg: 82 },
              { skill: "CLOUD/AWS", user: 25, avg: 78 }
            ];

            const rawMissing = fbApp?.feedback?.missing_skills || [];
            const detectedGaps = rawMissing.length > 0 ? rawMissing.map(m => {
              let desc = "Missing verifiable production implementations in repository evidence.";
              const lower = m.toLowerCase();
              if (lower.includes("docker") || lower.includes("container")) {
                desc = "Evidence lacked multi-stage Dockerfiles, compose environments, or container orchestration manifests.";
              } else if (lower.includes("cloud") || lower.includes("aws")) {
                desc = "No verifiable cloud infrastructure automation (AWS ECS/EC2/Lambda/Terraform) or production hosting.";
              } else if (lower.includes("redis") || lower.includes("caching")) {
                desc = "Distributed caching, key-value session stores, or cache invalidation layers not detected in active projects.";
              } else if (lower.includes("system") || lower.includes("distributed")) {
                desc = "Evidence showed architectural gaps in asynchronous queues (Celery/Kafka) and distributed state synchronization.";
              } else if (lower.includes("algorithm") || lower.includes("codeforces")) {
                desc = "Algorithmic problem-solving signals and edge-case execution depth below the lead engineer threshold.";
              }
              return { title: m.toUpperCase(), desc };
            }) : [
              { title: "DOCKER & CONTAINERIZATION", desc: "Evidence lacked multi-stage Dockerfiles and container orchestration manifests." },
              { title: "CLOUD DEPLOYMENT (AWS)", desc: "No verifiable cloud infrastructure automation or production workload hosting." },
              { title: "REDIS / CACHING ARCHITECTURE", desc: "Distributed caching and key-value session stores not detected in active projects." },
              { title: "HIGH-THROUGHPUT DISTRIBUTED SYSTEMS", desc: "Evidence showed architectural gaps in asynchronous queues and distributed state synchronization." }
            ];

            return (
              <motion.div
                key="feedback"
                {...pageTransition}
                className="max-w-5xl mx-auto space-y-16"
              >
                <div className="flex justify-between items-end border-b-4 border-black pb-8">
                  <div className="space-y-2">
                    <label className="font-grotesk text-xs uppercase font-black tracking-widest text-[#FF4D4D]">
                      ROLE: {fbApp?.job_title || "LEAD PYTHON ENGINEER"} • STATUS: NOT SELECTED
                    </label>
                    <h2 className="font-montreal font-black text-4xl md:text-6xl uppercase tracking-tighter">
                      Growth Insights & Benchmark
                    </h2>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
                  <div className="lg:col-span-7 space-y-12">
                    <div className="bg-[#101218] p-8 shadow-[12px_12px_0px_#ccc] border border-white/5">
                      <div className="flex justify-between items-baseline mb-12 border-b border-white/10 pb-4">
                        <h3 className="font-grotesk text-sm font-black uppercase tracking-widest text-white flex items-center gap-3">
                          <span className="w-2 h-2 bg-[#A7FF2E] rounded-full animate-pulse" />
                          Skill Benchmark
                        </h3>
                        <span className="text-[10px] font-black uppercase text-white/40">
                          You vs. Selected Candidates
                        </span>
                      </div>

                      <div className="h-[300px] w-full min-w-[200px]">
                        <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={100}>
                          <BarChart data={benchmarkData}>
                            <XAxis
                              dataKey="skill"
                              stroke="#fff"
                              fontSize={10}
                              tickLine={false}
                              axisLine={false}
                              tick={{ fontWeight: 900, opacity: 0.5 }}
                            />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: "#0B0D11",
                                border: "2px solid #333",
                                borderRadius: "0",
                                padding: "12px",
                              }}
                              itemStyle={{
                                fontSize: "10px",
                                fontWeight: 900,
                                textTransform: "uppercase",
                                color: "#fff",
                              }}
                              labelStyle={{
                                fontSize: "11px",
                                fontWeight: 900,
                                marginBottom: "8px",
                                color: "#00E5FF",
                                borderBottom: "1px solid #333",
                                paddingBottom: "4px",
                                textTransform: "uppercase",
                              }}
                              cursor={{ fill: "rgba(255,255,255,0.05)" }}
                            />
                            <Bar
                              dataKey="user"
                              radius={[2, 2, 0, 0]}
                              name="YOUR SCORE"
                            >
                              {benchmarkData.map((entry, index) => (
                                <Cell
                                  key={`cell-${index}`}
                                  fill={
                                    entry.user >= entry.avg
                                      ? "#A7FF2E"
                                      : "#00E5FF"
                                  }
                                />
                              ))}
                            </Bar>
                            <Bar
                              dataKey="avg"
                              fill="#1A1F26"
                              stroke="#ffffff33"
                              strokeWidth={1}
                              radius={[2, 2, 0, 0]}
                              name="TARGET LEVEL"
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="mt-8 flex gap-8 justify-center">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 bg-[#00E5FF]" />
                          <span className="font-grotesk text-[10px] font-black text-white/60">
                            YOUR SIGNATURE
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 bg-[#1A1F26] border border-white/20" />
                          <span className="font-grotesk text-[10px] font-black text-white/60">
                            SELECTED BENCHMARK
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="p-8 border-4 border-black space-y-8 bg-white">
                      <div className="space-y-4">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 bg-black rotate-45" />
                          <label className="font-grotesk text-xs font-black uppercase text-black tracking-widest">
                            WHY THIS DATA MATTERS
                          </label>
                        </div>
                        <p className="font-inter text-sm font-bold text-black opacity-60 leading-relaxed uppercase tracking-tight">
                          Our system evaluates your technical signatures globally. The gaps below represent direct differences between your verified evidence and the hiring team's specific requirements.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* RIGHT: SPECIFIC GAPS & PLAN */}
                  <div className="lg:col-span-5 space-y-12">
                    <section className="space-y-8">
                      <div className="space-y-6">
                        <div className="pb-2 border-b-2 border-black inline-block">
                          <label className="font-grotesk text-[11px] font-black uppercase text-black tracking-widest">
                            GAPS DETECTED
                          </label>
                        </div>
                        <div className="space-y-6">
                          {detectedGaps.map((gap) => (
                            <div key={gap.title} className="space-y-2 group">
                              <h4 className="font-montreal font-black text-lg uppercase tracking-tight group-hover:text-[#FF4D4D] transition-colors">
                                {gap.title}
                              </h4>
                              <p className="font-inter text-xs font-bold leading-relaxed opacity-60 uppercase tracking-tight">
                                {gap.desc}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-6">
                        <div className="pb-2 border-b-2 border-black inline-block">
                          <label className="font-grotesk text-[11px] font-black uppercase text-black tracking-widest">
                            HOW TO IMPROVE
                          </label>
                        </div>
                        <div className="space-y-6">
                          {[
                            {
                              title: "DEPLOY FULL-STACK CONTAINERIZED WORKLOAD",
                              desc: "Build and publish a repository with FastAPI, PostgreSQL connection pooling, and Redis caching orchestrated via Docker Compose.",
                            },
                            {
                              title: "AUTOMATE CLOUD CI/CD DEPLOYMENTS",
                              desc: "Configure GitHub Actions workflows deploying containerized microservices to AWS (ECS/EC2) or Render with health checks.",
                            },
                            {
                              title: "RE-VERIFY IN 30 DAYS",
                              desc: "Push commits demonstrating containerization and distributed state to automatically refresh your verified skill signatures.",
                            },
                          ].map((tip) => (
                            <div key={tip.title} className="space-y-2">
                              <h4 className="font-montreal font-black text-lg uppercase tracking-tight">
                                {tip.title}
                              </h4>
                              <p className="font-inter text-xs font-bold leading-relaxed opacity-60 uppercase tracking-tight">
                                {tip.desc}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </section>

                    <div className="pt-12 border-t border-black/10">
                      <button
                        onClick={() => setActivePage("status")}
                        className="w-full py-6 bg-black text-white font-grotesk font-black text-xs tracking-[0.3em] uppercase transition-all shadow-[6px_6px_0px_#ccc] hover:bg-white hover:text-black hover:-translate-y-1 active:shadow-none"
                      >
                        BACK TO APPLICATION STATUS
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })()}
        </AnimatePresence>
      </main>

      {/* JOB DETAILS MODAL */}
      {createPortal(
        <AnimatePresence>
          {selectedJobForDetails && (
            <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 md:p-6">
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setSelectedJobForDetails(null)}
                className="fixed inset-0 bg-black/90 backdrop-blur-xl"
              />
              <motion.div
                initial={{ scale: 0.95, opacity: 0, y: 30 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.95, opacity: 0, y: 30 }}
                className="relative w-full max-w-4xl max-h-full flex flex-col bg-[#E6E6E3] border-[4px] border-black shadow-[30px_30px_0px_rgba(0,0,0,0.5)] z-10"
                onClick={(e) => e.stopPropagation()}
              >
                {/* MODAL HEADER */}
                <div className="bg-white border-b-[4px] border-black p-6 md:px-10 flex justify-between items-center gap-6 shrink-0">
                  <div className="flex-1 min-w-0">
                    <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.4em] text-black/40 block mb-1">
                      AGENT VERIFIED ROLE
                    </label>
                    <h2 className="font-montreal font-black text-2xl md:text-4xl uppercase tracking-tighter leading-none text-black truncate">
                      {selectedJobForDetails.title}
                    </h2>
                  </div>
                  
                  <div className="flex items-center gap-4 shrink-0">
                    <button
                      onClick={() => {
                        setSelectedRoleForApply(selectedJobForDetails);
                        setActivePage("apply");
                        setSelectedJobForDetails(null);
                      }}
                      className="bg-black text-white px-6 md:px-10 py-3 md:py-4 font-grotesk text-[11px] font-black uppercase tracking-[0.3em] hover:bg-[#A7FF2E] hover:text-black transition-all shadow-[4px_4px_0px_#ccc] active:translate-y-1 active:shadow-none hidden sm:block"
                    >
                      APPLY NOW
                    </button>
                    <button 
                      onClick={() => setSelectedJobForDetails(null)}
                      className="p-3 border-2 border-black/10 hover:border-black hover:bg-black hover:text-white transition-all"
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="square">
                        <path d="M18 6L6 18M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* SCROLLABLE CONTENT */}
                <div 
                  className="flex-1 p-8 md:p-10 space-y-10 overflow-y-auto custom-scrollbar selection:bg-black selection:text-white"
                  data-lenis-prevent
                >
                  <div className="flex flex-wrap gap-2">
                    {selectedJobForDetails.tags?.map(tag => (
                      <span key={tag} className="font-grotesk text-[9px] font-black uppercase tracking-[0.2em] border-2 border-black/10 px-3 py-1 bg-black/5 text-black">
                        {tag}
                      </span>
                    ))}
                  </div>

                  <div className="space-y-12">
                    <div className="space-y-6">
                      <div className="flex items-center gap-4">
                        <label className="font-grotesk text-[11px] font-black uppercase tracking-[0.4em] text-black">
                          TECHNICAL SPECIFICATIONS
                        </label>
                        <div className="h-[2px] flex-1 bg-black/5" />
                      </div>
                      <div className="font-inter text-[14px] md:text-[16px] font-bold text-black/80 leading-[1.7] whitespace-pre-wrap tracking-normal bg-white border-l-[6px] border-black p-8 md:p-10 shadow-sm">
                        {selectedJobForDetails.desc || "Full technical signatures and agent-led validation required for this position."}
                      </div>
                    </div>
                  </div>

                  {/* MOBILE ONLY APPLY BUTTON */}
                  <div className="sm:hidden pt-4">
                    <button
                      onClick={() => {
                        setSelectedRoleForApply(selectedJobForDetails);
                        setActivePage("apply");
                        setSelectedJobForDetails(null);
                      }}
                      className="w-full bg-black text-white py-5 font-grotesk text-[12px] font-black uppercase tracking-[0.3em]"
                    >
                      APPLY NOW
                    </button>
                  </div>
                </div>

                {/* MODAL FOOTER STICKY (INTERNAL) */}
                <div className="bg-[#f0f0f0] border-t-[3px] border-black px-10 py-6 flex justify-between items-center shrink-0">
                  <div className="font-grotesk text-[9px] font-black uppercase tracking-[0.2em] opacity-40">
                    REF: {selectedJobForDetails.id} // HEUREKA_FHN_PROTECTED
                  </div>
                  <button
                    onClick={() => setSelectedJobForDetails(null)}
                    className="font-grotesk text-[10px] font-black uppercase tracking-[0.3em] hover:underline"
                  >
                    [ BACK TO LIST ]
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>,
        document.body
      )}

      <footer className="max-w-[1280px] mx-auto px-6 md:px-12 py-12 border-t border-[#1c1c1c]/10 text-center md:text-left">
        <div className="font-grotesk text-xs tracking-widest uppercase font-black text-[#1c1c1c]">
          POWERED BY FAIR HIRING NETWORK
        </div>
      </footer>

      <GridPlus className="fixed inset-0 pointer-events-none opacity-5 z-0" />
      <style>{`
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>

      {/* SKILL DETAIL MODAL REMOVED (Handled inside SkillPassport) */}
    </motion.div>
  );
}