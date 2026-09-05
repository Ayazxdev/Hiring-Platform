import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { generateSkillTest } from "../api/generateTest";
import { api } from "../api/backend";

export default function CompanyHiringFlow({ onExit, onComplete }) {
  const containerRef = useRef(null);
  const [roleData, setRoleData] = useState({
    title: "",
    type: "Full-time Permanent",
    experience: "Mid",
    maxParticipants: 50,
    applicationWindow: {
      start: new Date().toISOString().split("T")[0],
      end: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0],
    },
  });

  const [jobDescription, setJobDescription] = useState("");
  const [skillsArr, setSkillsArr] = useState([
    {
      name: "Frontend Architecture",
      importance: "Strong",
      evidenceRequired: true,
      evidenceTypes: ["GitHub / Code Repository", "Portfolio / Case Study"],
    },
  ]);
  const importanceLevels = [
    { id: "Core", label: "Core", type: "filtering" },
    { id: "Strong", label: "Strong", type: "filtering" },
    { id: "Optional", label: "Optional", type: "filtering" },
    { id: "Signal-only", label: "Signal-only", type: "non-filtering" },
  ];

  const [evalRules, setEvalRules] = useState({
    anonymousScreening: true,
    humanReview: true,
    threshold: 0.65,
  });

  const [published, setPublished] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [biasResult, setBiasResult] = useState(null);

  const experienceMapping = {
    Junior: "baseline depth",
    Mid: "applied reasoning",
    Senior: "architectural judgment",
  };

  const handleJobDescriptionChange = (e) => {
    const text = e.target.value;
    setJobDescription(text);
    console.log("SENT EVENT: JOB_DESCRIPTION_UPDATED", {
      role_id: "temp-uuid-001",
      text: text,
      timestamp: new Date().toISOString(),
    });
  };

  useEffect(() => {
    if (!jobDescription || jobDescription.trim().length < 20) {
      setBiasResult(null);
      return;
    }

    const timer = setTimeout(async () => {
      setIsAnalyzing(true);
      try {
        const result = await api.analyzeJobDescription(jobDescription);
        setBiasResult(result);
      } catch (err) {
        console.error("Bias analysis failed:", err);
      } finally {
        setIsAnalyzing(false);
      }
    }, 1500);

    return () => clearTimeout(timer);
  }, [jobDescription]);

  const addSkill = () => {
    setSkillsArr([
      ...skillsArr,
      {
        name: "",
        importance: "Strong",
        evidenceRequired: false,
        evidenceTypes: [],
      },
    ]);
  };

  const updateSkill = (index, field, value) => {
    const newArr = [...skillsArr];
    newArr[index][field] = value;
    setSkillsArr(newArr);
  };

  const handlePublish = async () => {
    // Basic frontend validation (optional)
    if (!roleData.title?.trim()) return;

    // setPublished(true); // Moved to after API call success

    console.log("SENT EVENT: ROLE_PUBLISHED", {
      role_id: "temp-uuid-001",
      status: "active",
      application_window: {
        start: roleData.applicationWindow.start,
        end: roleData.applicationWindow.end,
      },
    });

    const jobPayload = {
      role: roleData.title,
      level: roleData.experience,
      mapped_depth: experienceMapping[roleData.experience],
      skills: skillsArr.map((s) => ({
        name: s.name,
        importance_type:
          importanceLevels.find((l) => l.label === s.importance)?.type ||
          "filtering",
      })),
      verification: {
        mandatory: skillsArr.some((s) => s.evidenceRequired),
      },
    };

    localStorage.setItem(
      "fhn_active_role_data",
      JSON.stringify({
        id: "r_custom_001",
        title: roleData.title,
        level: roleData.experience,
        alignment: "98%",
        tags: jobPayload.skills.slice(0, 3).map((s) => s.name),
      }),
    );

    // Move setPublished(true) into the try block to ensure we only show success if backend persists.
    try {
      const companyId = localStorage.getItem("fhn_company_id");

      if (!companyId) {
        alert("Session expired. Please log in again.");
        return;
      }

      await api.createJob({
        company_id: companyId,
        title: roleData.title,
        description: jobDescription || "No description provided",
        published: true,
        max_participants: parseInt(roleData.maxParticipants) || 50,
      });
      console.log("✅ Job persisted to backend");
      setPublished(true); // Only now show the success screen

    } catch (e) {
      console.error("❌ Failed to persist job to backend:", e);
      alert(`Failed to publish role: ${e.message}. Check console for details.`);
      // Do not setPublished(true) so user can retry
    }

    generateSkillTest(jobPayload).then(() => {
      console.log("✅ Candidate Test Pre-Cached Successfully");
    });
  };

  return (
    <motion.div
      ref={containerRef}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="fixed inset-0 z-[200] bg-[#E6E6E3] text-[#1c1c1c] overflow-y-auto selection:bg-black selection:text-white pb-32"
      style={{ willChange: "opacity" }}
      data-lenis-prevent
    >
      {/* STICKY HEADER */}
      <header className="sticky top-0 left-0 w-full bg-[#E6E6E3] border-b-[3px] border-[#1c1c1c] z-50 px-6 md:px-12 py-6 flex justify-between items-center bg-opacity-95 backdrop-blur-sm">
        <div className="flex items-center gap-6">
          <button
            onClick={onExit}
            className="px-6 py-3 border-[2px] border-[#1c1c1c] font-grotesk text-[11px] font-black uppercase tracking-[0.2em] hover:bg-[#1c1c1c] hover:text-[#E6E6E3] transition-all flex items-center gap-2 group"
          >
            <span className="group-hover:-translate-x-1 transition-transform inline-block">
              ←
            </span>{" "}
            BACK TO COMPANY MENU
          </button>
          <div className="h-10 w-[2px] bg-[#1c1c1c]/10 hidden md:block"></div>
          <span className="font-montreal font-black text-sm md:text-base tracking-[0.2em] uppercase text-[#1c1c1c]">
            CREATE NEW ROLE
          </span>
        </div>
      </header>

      <div className="max-w-[1440px] mx-auto px-6 md:px-12 pt-12">
        {!published ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
            {/* LEFT COLUMN: Role Details & Requirements */}
            <div className="lg:col-span-7 space-y-16">
              {/* ROLE BASICS */}
              <section className="space-y-10">
                <div className="flex items-center gap-4 border-b-[2px] border-[#1c1c1c] pb-4">
                  <span className="font-grotesk text-[10px] font-black bg-[#1c1c1c] text-[#E6E6E3] px-2 py-1">
                    01
                  </span>
                  <h2 className="font-montreal font-black text-xl md:text-2xl uppercase tracking-tighter">
                    ROLE BASICS
                  </h2>
                </div>

                <div className="space-y-12">
                  <div className="space-y-4">
                    <label className="font-grotesk text-[11px] font-black tracking-[0.2em] uppercase text-[#1c1c1c]">
                      ROLE TITLE
                    </label>
                    <input
                      type="text"
                      value={roleData.title}
                      onChange={(e) =>
                        setRoleData({ ...roleData, title: e.target.value })
                      }
                      placeholder="Lead Interface Engineer"
                      className="w-full bg-transparent border-b-[2px] border-[#1c1c1c]/20 py-4 font-montreal text-3xl md:text-5xl focus:outline-none focus:border-[#1c1c1c] transition-colors placeholder:text-[#1c1c1c]/20 font-black uppercase"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                    <div className="space-y-4">
                      <label className="font-grotesk text-[11px] font-black tracking-[0.2em] uppercase text-[#1c1c1c]">
                        ROLE TYPE
                      </label>
                      <div className="relative">
                        <select
                          value={roleData.type}
                          onChange={(e) =>
                            setRoleData({ ...roleData, type: e.target.value })
                          }
                          className="w-full bg-white border-[2px] border-[#1c1c1c] px-4 py-4 font-montreal text-lg font-bold focus:outline-none appearance-none cursor-pointer uppercase"
                        >
                          <option>Full-time Permanent</option>
                          <option>Contract / Interim</option>
                          <option>Partial Remote</option>
                        </select>
                        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none font-black opacity-30">
                          ↓
                        </div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <label className="font-grotesk text-[11px] font-black tracking-[0.2em] uppercase text-[#1c1c1c]">
                        EXPERIENCE LEVEL
                      </label>
                      <div className="flex gap-2">
                        {["Junior", "Mid", "Senior"].map((level) => (
                          <button
                            key={level}
                            onClick={() =>
                              setRoleData({ ...roleData, experience: level })
                            }
                            className={`flex-1 py-4 border-[2px] font-grotesk text-[11px] font-black uppercase tracking-widest transition-all ${roleData.experience === level ? "bg-[#1c1c1c] text-[#E6E6E3] border-[#1c1c1c]" : "bg-transparent border-[#1c1c1c]/20 hover:border-[#1c1c1c]"}`}
                          >
                            {level}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                    <div className="space-y-4">
                      <label className="font-grotesk text-[11px] font-black tracking-[0.2em] uppercase text-[#1c1c1c]">
                        MAX PARTICIPANTS
                      </label>
                      <div className="relative">
                        <select
                          value={roleData.maxParticipants}
                          onChange={(e) =>
                            setRoleData({
                              ...roleData,
                              maxParticipants: parseInt(e.target.value),
                            })
                          }
                          className="w-full bg-white border-[2px] border-[#1c1c1c] px-4 py-4 font-montreal text-lg font-bold focus:outline-none appearance-none cursor-pointer uppercase"
                        >
                          {[10, 25, 50, 100, 250, 500].map((n) => (
                            <option key={n} value={n}>
                              {n} CANDIDATES
                            </option>
                          ))}
                        </select>
                        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none font-black opacity-30">
                          ↓
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              {/* APPLICATION WINDOW */}
              <section className="space-y-10 p-8 border-[2px] border-[#1c1c1c] bg-[#1c1c1c]/[0.02]">
                <div className="flex items-center gap-4 border-b-[2px] border-[#1c1c1c] pb-4">
                  <span className="font-grotesk text-[10px] font-black bg-[#1c1c1c] text-[#E6E6E3] px-2 py-1">
                    02
                  </span>
                  <h2 className="font-montreal font-black text-xl md:text-2xl uppercase tracking-tighter">
                    APPLICATION WINDOW
                  </h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-4">
                    <label className="font-grotesk text-[11px] font-black tracking-[0.2em] uppercase text-[#1c1c1c]">
                      START DATE
                    </label>
                    <input
                      type="date"
                      value={roleData.applicationWindow.start}
                      onChange={(e) =>
                        setRoleData({
                          ...roleData,
                          applicationWindow: {
                            ...roleData.applicationWindow,
                            start: e.target.value,
                          },
                        })
                      }
                      className="w-full bg-white border-[2px] border-[#1c1c1c] px-4 py-4 font-montreal font-bold focus:outline-none"
                    />
                  </div>
                  <div className="space-y-4">
                    <label className="font-grotesk text-[11px] font-black tracking-[0.2em] uppercase text-[#1c1c1c]">
                      END DATE
                    </label>
                    <input
                      type="date"
                      value={roleData.applicationWindow.end}
                      onChange={(e) =>
                        setRoleData({
                          ...roleData,
                          applicationWindow: {
                            ...roleData.applicationWindow,
                            end: e.target.value,
                          },
                        })
                      }
                      className="w-full bg-white border-[2px] border-[#1c1c1c] px-4 py-4 font-montreal font-bold focus:outline-none"
                    />
                  </div>
                </div>
              </section>

              {/* JOB DESCRIPTION */}
              <section className="space-y-10">
                <div className="flex items-center gap-4 border-b-[2px] border-[#1c1c1c] pb-4">
                  <span className="font-grotesk text-[10px] font-black bg-[#1c1c1c] text-[#E6E6E3] px-2 py-1">
                    03
                  </span>
                  <div className="flex items-center gap-4 justify-between w-full">
                    <h2 className="font-montreal font-black text-xl md:text-2xl uppercase tracking-tighter">
                      JOB DESCRIPTION
                    </h2>
                    <div className="font-grotesk text-[9px] font-black uppercase tracking-widest text-black/40 border border-black/10 px-2 py-1 bg-black/5">
                      Bias-safe language scan enabled
                    </div>
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="flex flex-col gap-2">
                    <label className="font-grotesk text-[11px] font-black tracking-[0.2em] uppercase text-[#1c1c1c]">
                      DETAILED MANDATE
                    </label>
                    <p className="font-inter text-[11px] font-bold text-[#1c1c1c]/60 max-w-lg">
                      Describe the mission and impact. Our system will analyze
                      this text for bias and skill markers in real-time.
                    </p>
                  </div>
                  <textarea
                    rows="8"
                    value={jobDescription}
                    onChange={handleJobDescriptionChange}
                    placeholder="FOCUS ON OUTCOMES, NOT CREDENTIALS..."
                    className="w-full bg-white border-[2px] border-[#1c1c1c] p-6 font-inter text-lg md:text-xl font-medium leading-[1.6] focus:outline-none focus:ring-4 focus:ring-[#1c1c1c]/5 transition-all placeholder:text-[#1c1c1c]/10 resize-none min-h-[320px]"
                  />
                  {jobDescription.length > 0 && (
                    <div className="flex flex-col gap-4">
                      <div className="flex gap-4 p-4 bg-black/[0.03] border-[1px] border-[#1c1c1c]/10 items-center">
                        <div className={`w-2 h-2 rounded-full ${isAnalyzing ? "bg-yellow-500 animate-pulse" : "bg-green-500"}`}></div>
                        <span className="font-grotesk text-[9px] font-black uppercase tracking-widest text-[#1c1c1c]">
                          {isAnalyzing ? "Analyzing JD for Inclusive Language..." : "Inclusive Language scan active"}
                        </span>
                      </div>

                      {biasResult && (
                        <motion.div
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className={`p-6 border-[2px] ${biasResult.bias_score > 0 ? "border-red-500 bg-red-50" : "border-green-500 bg-green-50"} space-y-4`}
                        >
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <span className="font-grotesk text-[10px] font-black uppercase tracking-widest text-[#1c1c1c]">
                                Bias Audit Score:
                              </span>
                              <span className={`font-montreal font-black text-xl ${biasResult.bias_score > 4 ? "text-red-600" : "text-green-600"}`}>
                                {biasResult.bias_score}/10
                              </span>
                            </div>
                            {biasResult.bias_score > 0 && (
                              <span className="font-grotesk text-[8px] font-black bg-red-600 text-white px-2 py-1 uppercase animate-pulse">
                                Bias Detected
                              </span>
                            )}
                          </div>

                          <p className="font-inter text-xs font-medium text-[#1c1c1c]/70 leading-relaxed uppercase">
                            {biasResult.reasoning}
                          </p>

                          {biasResult.findings && biasResult.findings.length > 0 && (
                            <div className="space-y-3 pt-4 border-t border-black/10">
                              <span className="font-grotesk text-[9px] font-black uppercase tracking-[0.2em] text-black/40">
                                Specific Improvements:
                              </span>
                              <div className="grid gap-3">
                                {biasResult.findings.map((finding, fIdx) => (
                                  <div key={fIdx} className="bg-white/50 p-4 border border-black/5 space-y-2">
                                    <div className="flex justify-between items-start">
                                      <span className="font-grotesk text-[10px] font-black text-red-600 uppercase">
                                        Flag: "{finding.phrase}"
                                      </span>
                                      <span className="font-grotesk text-[8px] font-bold bg-black/5 px-2 py-0.5 rounded text-black/60 uppercase">
                                        {finding.category}
                                      </span>
                                    </div>
                                    <div className="font-inter text-[11px] font-bold text-green-700 uppercase">
                                      Better Alternative: {finding.fix}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </div>
                  )}
                </div>
              </section>

              {/* SKILL DEFINITION */}
              <section className="space-y-10">
                <div className="flex items-center gap-4 border-b-[2px] border-[#1c1c1c] pb-4">
                  <span className="font-grotesk text-[10px] font-black bg-[#1c1c1c] text-[#E6E6E3] px-2 py-1">
                    04
                  </span>
                  <h2 className="font-montreal font-black text-xl md:text-2xl uppercase tracking-tighter">
                    SKILL EVIDENCE PROTOCOL
                  </h2>
                </div>

                <div className="space-y-8">
                  {skillsArr.map((skill, idx) => (
                    <div
                      key={idx}
                      className="p-8 border-[2px] border-[#1c1c1c] bg-white space-y-8 relative group"
                    >
                      <div className="flex flex-col md:flex-row gap-8">
                        <div className="flex-1 space-y-4">
                          <label className="font-grotesk text-[10px] font-black tracking-widest uppercase text-[#1c1c1c]">
                            SKILL NAME
                          </label>
                          <input
                            type="text"
                            value={skill.name}
                            onChange={(e) =>
                              updateSkill(idx, "name", e.target.value)
                            }
                            placeholder="e.g. DISTRIBUTED SYSTEMS"
                            className="w-full bg-transparent border-b-[2px] border-[#1c1c1c]/20 py-2 font-montreal font-black text-2xl focus:outline-none focus:border-[#1c1c1c] uppercase"
                          />
                        </div>
                        <div className="w-full md:w-80 space-y-4">
                          <label className="font-grotesk text-[10px] font-black tracking-widest uppercase text-[#1c1c1c]">
                            IMPORTANCE
                          </label>
                          <div className="flex border-[2px] border-[#1c1c1c]">
                            {importanceLevels.map((level) => (
                              <button
                                key={level.id}
                                onClick={() =>
                                  updateSkill(idx, "importance", level.label)
                                }
                                className={`flex-1 py-3 text-[9px] font-grotesk font-black uppercase transition-colors ${skill.importance === level.label ? "bg-[#1c1c1c] text-white" : "hover:bg-black/5"}`}
                              >
                                {level.id === "Signal-only"
                                  ? "!!!"
                                  : level.id.slice(0, 1)}
                              </button>
                            ))}
                          </div>
                          <p className="font-inter text-[9px] font-bold text-black/40 uppercase tracking-tight">
                            Signal-only skills inform ranking but never
                            disqualify candidates.
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between border-t-[1px] border-[#1c1c1c]/10 pt-6">
                        <div className="flex items-center gap-4">
                          <div className="space-y-1">
                            <div className="flex items-center gap-4">
                              <button
                                onClick={() =>
                                  updateSkill(
                                    idx,
                                    "evidenceRequired",
                                    !skill.evidenceRequired,
                                  )
                                }
                                className={`w-12 h-6 border-[2px] border-[#1c1c1c] p-1 transition-colors ${skill.evidenceRequired ? "bg-black" : "bg-transparent"}`}
                              >
                                <motion.div
                                  animate={{
                                    x: skill.evidenceRequired ? 20 : 0,
                                  }}
                                  className={`w-4 h-4 ${skill.evidenceRequired ? "bg-white" : "bg-black"}`}
                                />
                              </button>
                              <span className="font-grotesk text-[10px] font-black uppercase tracking-widest text-[#1c1c1c]">
                                Mandatory Verification
                              </span>
                            </div>
                            <p className="font-inter text-[9px] font-bold text-black/40 uppercase tracking-tight ml-16">
                              Candidates below the confidence threshold must
                              complete verification before review.
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() =>
                            setSkillsArr(skillsArr.filter((_, i) => i !== idx))
                          }
                          className="font-grotesk text-[9px] font-black uppercase opacity-20 hover:opacity-100 transition-opacity"
                        >
                          [ REMOVE ]
                        </button>
                      </div>
                    </div>
                  ))}
                  <button
                    onClick={addSkill}
                    className="w-full py-6 border-[2px] border-dashed border-[#1c1c1c]/30 font-grotesk font-black text-[11px] uppercase tracking-[0.3em] hover:border-[#1c1c1c] hover:bg-black/5 transition-all"
                  >
                    + ADD REQUIREMENT
                  </button>
                </div>
              </section>
            </div>

            {/* RIGHT COLUMN: Fair Hiring Configuration & Review */}
            <div className="lg:col-span-5">
              <div className="sticky top-32 space-y-12">
                {/* FAIR HIRING PROTOCOL (READ-ONLY) */}
                <section className="p-8 bg-[#1c1c1c] text-[#E6E6E3] border-[4px] border-[#1c1c1c] space-y-10 shadow-[8px_8px_0px_rgba(28,28,28,0.1)]">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 bg-[#00E5FF] rounded-full"></div>
                        <h2 className="font-montreal font-black text-xl uppercase tracking-tighter">
                          FAIR HIRING PROTOCOL
                        </h2>
                      </div>
                      <span className="font-grotesk text-[8px] font-black tracking-widest text-[#00E5FF]/40 uppercase">
                        SYSTEM ENFORCED — NOT CONFIGURABLE
                      </span>
                    </div>
                    <p className="font-inter text-[11px] font-medium opacity-60 leading-relaxed uppercase tracking-wider">
                      These rules are enforced by system agents to ensure
                      zero-bias ranking.
                    </p>
                  </div>

                  <div className="space-y-8">
                    {[
                      {
                        label: "ANONYMOUS SCREENING",
                        desc: "IDENTITY MASKED UNTIL VERIFIED RANKING",
                      },
                      {
                        label: "BIAS DETECTION",
                        desc: "SYSTEM-LEVEL AUTOMATED SCAN (POST-WINDOW)",
                      },
                      {
                        label: "SKILL-BASED RANKING",
                        desc: "RANKING BASED ON EVIDENCE, NOT PEDIGREE",
                      },
                      {
                        label: "CONFIDENCE VERIFICATION",
                        desc: "AGENTS VERIFY DEPTH AND AUTHENTICITY",
                      },
                    ].map((rule, idx) => (
                      <div
                        key={idx}
                        className="flex justify-between items-start gap-8"
                      >
                        <div className="space-y-1.5">
                          <div className="font-grotesk font-black text-sm uppercase tracking-tight">
                            {rule.label}
                          </div>
                          <div className="font-inter text-[9px] font-bold opacity-40 uppercase tracking-widest">
                            {rule.desc}
                          </div>
                        </div>
                        <div className="flex items-center gap-2 px-3 py-1 border border-[#00E5FF]/20 bg-[#00E5FF]/5">
                          <div className="w-1.5 h-1.5 bg-[#00E5FF] rounded-full"></div>
                          <span className="font-grotesk text-[9px] font-black text-[#00E5FF] uppercase tracking-widest">
                            LOCKED
                          </span>
                        </div>
                      </div>
                    ))}

                    <div className="space-y-6 pt-6 border-t border-white/10">
                      <div className="flex justify-between items-end">
                        <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.2em] text-[#00E5FF]">
                          MINIMUM CONFIDENCE THRESHOLD
                        </label>
                        <span className="font-montreal font-black text-3xl text-white">
                          75%
                        </span>
                      </div>
                      <div className="w-full h-1.5 bg-white/10 relative overflow-hidden">
                        <div
                          className="absolute top-0 left-0 h-full bg-[#00E5FF]"
                          style={{ width: "75%" }}
                        ></div>
                        <div className="absolute top-1/2 -translate-y-1/2 left-[75%] w-3 h-3 bg-white border-2 border-[#1c1c1c] z-10"></div>
                      </div>
                      <div className="flex justify-between text-[8px] font-black text-[#E6E6E3]/30 uppercase tracking-widest">
                        <span>SYSTEM OPTIMIZED</span>
                        <span className="text-[#00E5FF]/40">
                          LOCKED FOR BIAS SAFETY
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-6 border-t border-white/10">
                    <div className="bg-white/5 p-4 space-y-4">
                      <div className="font-grotesk text-[9px] font-black text-[#00E5FF] uppercase tracking-widest underline">
                        SYSTEM GUARANTEE
                      </div>
                      <div className="space-y-2">
                        <p className="font-inter text-[10px] font-bold text-white/50 uppercase leading-relaxed tracking-wide">
                          Bias checks run post-window. No candidate is penalized
                          individually. System-level fairness is audited and
                          traceable.
                        </p>
                        <div className="space-y-1 pt-2 border-t border-white/5">
                          <div className="font-grotesk text-[8px] font-black text-white/40 uppercase tracking-widest">
                            Agents Activated:
                          </div>
                          <ul className="font-inter text-[9px] font-bold text-[#00E5FF]/60 uppercase tracking-wide list-disc pl-4 space-y-1">
                            <li>Skill Verification</li>
                            <li>Bias Detection (post-window)</li>
                            <li>Transparent Matching</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </section>

                {/* REVIEW ROLE SECTION */}
                <section className="p-8 border-[2px] border-[#1c1c1c] bg-white space-y-8">
                  <div className="flex justify-between items-center border-b border-black/10 pb-4">
                    <h2 className="font-montreal font-black text-xl uppercase tracking-tighter">
                      SUMMARY
                    </h2>
                    <div className="font-grotesk text-[9px] font-black bg-black/5 px-2 py-1 uppercase">
                      READ-ONLY PREVIEW
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="space-y-1">
                      <span className="font-grotesk text-[9px] font-black opacity-30 uppercase tracking-widest">
                        IDENTITY
                      </span>
                      <div className="font-montreal font-bold text-lg uppercase truncate">
                        {roleData.title || "UNTITLED ROLE"}
                      </div>
                    </div>
                    <div className="flex gap-8">
                      <div className="space-y-1">
                        <span className="font-grotesk text-[9px] font-black opacity-30 uppercase tracking-widest">
                          TIER
                        </span>
                        <div className="font-montreal font-bold text-sm uppercase">
                          {roleData.experience}
                        </div>
                      </div>
                      <div className="space-y-1">
                        <span className="font-grotesk text-[9px] font-black opacity-30 uppercase tracking-widest">
                          SKILLS
                        </span>
                        <div className="font-montreal font-bold text-sm uppercase">
                          {skillsArr.length} DEFINED
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <p className="font-inter text-[9px] font-black text-black/40 uppercase text-center tracking-widest leading-relaxed">
                      Role requirements become immutable after activation.
                    </p>
                    <button
                      onClick={handlePublish}
                      disabled={!roleData.title}
                      className="w-full py-8 bg-[#1c1c1c] text-[#E6E6E3] font-grotesk font-black text-sm tracking-[0.5em] uppercase hover:bg-black active:scale-95 disabled:opacity-20 disabled:pointer-events-none transition-all shadow-[8px_8px_0px_rgba(28,28,28,0.1)]"
                    >
                      ACTIVATE INFRASTRUCTURE →
                    </button>
                  </div>
                </section>
              </div>
            </div>
          </div>
        ) : (
          /* POST-PUBLISH VIEW */
          <div className="max-w-3xl mx-auto py-24 text-center space-y-12">
            <div className="space-y-6">
              <motion.div
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="w-32 h-32 bg-[#1c1c1c] text-[#E6E6E3] flex items-center justify-center mx-auto rounded-full text-4xl font-black"
              >
                ✓
              </motion.div>
              <h3 className="font-montreal font-black text-6xl uppercase tracking-tighter">
                ROLE IS LIVE
              </h3>
              <p className="font-inter text-xl font-medium opacity-60">
                The automated agent is now pre-caching evaluation environments.
              </p>
            </div>

            <div className="p-12 border-[3px] border-[#1c1c1c] bg-white space-y-8">
              <div className="space-y-2">
                <div className="font-grotesk text-[10px] font-black uppercase tracking-[0.3em]">
                  CANDIDATE ENTRYPOINT
                </div>
                <div className="font-montreal font-bold text-lg bg-black/5 p-4 break-all uppercase">
                  fair-hiring.network/v1/apply/r_custom_001
                </div>
              </div>
              <button
                onClick={onComplete || onExit}
                className="w-full py-6 bg-[#1c1c1c] text-[#E6E6E3] font-grotesk font-black text-xs tracking-[0.4em] uppercase hover:bg-black transition-all"
              >
                RETURN TO DASHBOARD
              </button>
            </div>
          </div>
        )}
      </div>

      {/* GRID OVERLAY */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03] z-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]" />
    </motion.div>
  );
}
