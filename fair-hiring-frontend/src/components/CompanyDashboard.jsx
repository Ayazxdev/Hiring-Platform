import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { api } from "../api/backend";


const MOCK_CHART_DATA = [
  { range: "0.0-0.2", count: 4 },
  { range: "0.2-0.4", count: 8 },
  { range: "0.4-0.6", count: 18 },
  { range: "0.6-0.8", count: 12 },
  { range: "0.8-1.0", count: 6 },
];

export default function CompanyDashboard({ onNavigateToRole, onExit }) {
  const [statsVisible, setStatsVisible] = useState(false);
  const [roles, setRoles] = useState([]);
  const [companyStats, setCompanyStats] = useState({
    active_roles: 0,
    candidates_in_flow: 0,
    fairness_status: "VERIFIED",
  });

  // Company auth helpers
  const companyName = localStorage.getItem("fhn_company_name") || "COMPANY";
  const companyEmail = localStorage.getItem("fhn_company_email") || "";

  const logoutCompany = () => {
    localStorage.removeItem("fhn_role");
    localStorage.removeItem("fhn_company_id");
    localStorage.removeItem("fhn_company_email");
    localStorage.removeItem("fhn_company_name");
    window.location.href = "/company";
  };

  useEffect(() => {
    const timer = setTimeout(() => setStatsVisible(true), 200);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const cid = localStorage.getItem("fhn_company_id");
    if (!cid) return;

    api.getCompanyStats(cid).then(setCompanyStats).catch(console.warn);

    api
      .listCompanyJobs(cid)
      .then((jobs) => {
        if (!jobs.length) return;
        setRoles(
          jobs.map((j) => ({
            id: String(j.id),
            title: j.title,
            status: j.published ? "Open" : "Draft",
            candidates: j.candidates_count || 0,
            fairness: j.fairness_status || "Verified",
          })),
        );
      })
      .catch((err) => {
        console.warn("Failed to load company jobs", err);
      });
  }, []);

  return (
    <motion.div
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
            COMPANY DASHBOARD
          </span>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="font-grotesk text-[10px] font-black uppercase tracking-[0.25em] text-black/50">
            COMPANY: <span className="text-black">{companyName}</span>
          </div>

          <button
            onClick={logoutCompany}
            className="px-4 py-2 border-2 border-black/20 font-grotesk text-[10px] font-black uppercase tracking-[0.25em] hover:border-black hover:bg-black hover:text-white transition-all"
          >
            LOGOUT
          </button>
        </div>
      </header>

      <main className="max-w-[1280px] mx-auto px-6 md:px-12 py-10 space-y-12">
        {/* SECTION 1: STATUS OVERVIEW — CLEAR & COMPACT */}
        <section className="bg-white border-[2px] border-[#1c1c1c] p-8 md:p-10 shadow-[8px_8px_0px_rgba(0,0,0,0.05)]">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
            {[
              { label: "ACTIVE ROLES", value: String(companyStats.active_roles) },
              { label: "CANDIDATES IN FLOW", value: String(companyStats.candidates_in_flow) },
              { label: "FAIRNESS STATUS", value: companyStats.fairness_status, isText: true },
            ].map((stat, i) => (
              <div
                key={stat.label}
                className="space-y-1 border-l-2 border-[#1c1c1c]/5 pl-6 first:border-l-0 first:pl-0"
              >
                <label className="font-grotesk text-[10px] tracking-[0.25em] uppercase font-black text-[#1c1c1c]/60">
                  {stat.label}
                </label>
                <AnimatePresence>
                  {statsVisible && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.6, delay: i * 0.15 }}
                      className={`font-montreal font-black uppercase tracking-tighter text-[#1c1c1c] ${stat.isText ? "text-2xl md:text-3xl" : "text-6xl md:text-7xl leading-[0.9]"}`}
                    >
                      {stat.value}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          {/* SECTION 2: ACTIVE ROLES — INDIVIDUAL CONTAINERS */}
          <section className="lg:col-span-12 space-y-6">
            <div className="flex justify-between items-end border-b-[2px] border-[#1c1c1c] pb-4 mb-4">
              <h2 className="font-grotesk text-[10px] tracking-[0.3em] uppercase font-black text-[#1c1c1c]">
                ACTIVE ROLES
              </h2>
              <span className="font-inter text-[10px] font-bold opacity-30 uppercase tracking-widest">
                {roles.length} TOTAL
              </span>
            </div>

            <div className="grid grid-cols-1 gap-6">
              {roles.map((role) => (
                <div
                  key={role.id}
                  onClick={() => onNavigateToRole && onNavigateToRole(role.id)}
                  className="group flex flex-col md:flex-row md:items-center justify-between bg-white border-[2px] border-[#1c1c1c] p-8 shadow-[4px_4px_0px_rgba(0,0,0,0.02)] hover:shadow-[12px_12px_0px_rgba(0,0,0,0.04)] cursor-pointer transition-all duration-300 rounded-sm"
                >
                  <div className="space-y-1">
                    <div className="font-montreal font-black text-xl md:text-2xl uppercase tracking-tight text-[#1c1c1c] group-hover:text-black transition-colors">
                      {role.title}
                    </div>
                    <div className="flex items-center gap-3 font-inter text-[10px] font-black uppercase tracking-wider opacity-60">
                      <span className="px-2 py-0.5 bg-[#1c1c1c] text-white rounded-[2px] font-bold">
                        {role.status}
                      </span>
                      <span className="w-1.5 h-1.5 bg-[#1c1c1c]/20 rounded-full" />
                      <span>{role.candidates} Candidates</span>
                      <span className="w-1.5 h-1.5 bg-[#1c1c1c]/20 rounded-full" />
                      <span className="text-green-700 font-bold">
                        Fairness {role.fairness}
                      </span>
                    </div>
                  </div>
                  <div className="mt-6 md:mt-0 font-grotesk text-[11px] font-black tracking-[0.2em] uppercase opacity-100 flex items-center gap-3 group-hover:translate-x-1 transition-transform">
                    VIEW PIPELINE <span className="text-xl">→</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* SECTION 3: HIRING INTELLIGENCE — VISUALLY EXPLAINED */}
          <div className="lg:col-span-12 grid grid-cols-1 md:grid-cols-2 gap-12">
            <section className="bg-[#1c1c1c] text-[#E6E6E3] p-8 space-y-8">
              <h2 className="font-grotesk text-[10px] tracking-[0.3em] uppercase font-black border-b border-white/10 pb-4">
                FAIRNESS & HEALTH
              </h2>
              <div className="space-y-6">
                <div className="space-y-3">
                  <label className="font-grotesk text-[9px] tracking-[0.2em] uppercase font-black text-[#D4D478]">
                    SYSTEM MONITOR
                  </label>
                  <p className="font-inter text-sm font-bold leading-relaxed opacity-90">
                    No bias markers detected. Infrastructure monitoring remains
                    active across all evidence channels with 100% data
                    integrity.
                  </p>
                </div>
                <div className="space-y-3">
                  <label className="font-grotesk text-[9px] tracking-[0.2em] uppercase font-black text-[#D4D478]">
                    REVIEW LOAD
                  </label>
                  <div className="flex items-center gap-6">
                    <div className="font-montreal font-black text-4xl">03</div>
                    <p className="font-inter text-[10px] font-bold leading-tight opacity-70 uppercase tracking-widest">
                      Candidates pending
                      <br />
                      human review escalation
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <section className="bg-white border-[2px] border-[#1c1c1c] p-8 space-y-6">
              <label className="font-grotesk text-[10px] tracking-[0.2em] uppercase font-black text-[#1c1c1c]">
                SKILL CONFIDENCE DISTRIBUTION
              </label>
              <div className="h-[140px] w-full pt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={MOCK_CHART_DATA}
                    margin={{ top: 0, right: 0, left: -25, bottom: 0 }}
                  >
                    <XAxis
                      dataKey="range"
                      axisLine={false}
                      tickLine={false}
                      tick={{
                        fill: "#1c1c1c",
                        opacity: 0.5,
                        fontSize: 8,
                        fontWeight: "bold",
                        fontFamily: "monospace",
                      }}
                    />
                    <Tooltip
                      cursor={{ fill: "rgba(0,0,0,0.03)" }}
                      contentStyle={{
                        backgroundColor: "#1c1c1c",
                        border: "none",
                        borderRadius: "0px",
                        fontSize: "10px",
                        color: "#fff",
                        fontFamily: "monospace",
                      }}
                      itemStyle={{ color: "#fff" }}
                    />
                    <Bar
                      dataKey="count"
                      radius={[0, 0, 0, 0]}
                      isAnimationActive={true}
                    >
                      {MOCK_CHART_DATA.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill="#1c1c1c"
                          fillOpacity={0.2 + index * 0.18}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-between items-center opacity-40 font-inter text-[8px] font-black uppercase tracking-widest border-t border-[#1c1c1c]/10 pt-4">
                <span>SANITIZED DATA</span>
                <span>v2.0.4 AGENT</span>
              </div>
            </section>
          </div>
        </div>
      </main>

      <footer className="max-w-[1280px] mx-auto px-6 md:px-12 py-12 border-t border-[#1c1c1c]/5 flex justify-between items-center opacity-30">
        <div className="font-grotesk text-[9px] tracking-widest uppercase">
          Fair Hiring Network · Infrastructure for Trust
        </div>
        <div className="font-grotesk text-[9px] tracking-widest uppercase">
          © 2026
        </div>
      </footer>

      {/* GRID OVERLAY */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03] z-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]" />

      <style>{`
                .custom-scrollbar-dashboard::-webkit-scrollbar { width: 6px; }
                .custom-scrollbar-dashboard::-webkit-scrollbar-thumb { background: #1c1c1c; border-radius: 10px; }
                .custom-scrollbar-dashboard::-webkit-scrollbar-track { background: rgba(0,0,0,0.05); }
            `}</style>
    </motion.div>
  );
}
