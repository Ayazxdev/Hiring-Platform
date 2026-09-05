import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { api } from "../api/backend";

export default function CompanyAuth({ onExit }) {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login"); // login | signup
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const [form, setForm] = useState({ name: "", email: "", password: "" });

  const submit = async (e) => {
    e.preventDefault();
    setErr("");

    // Client-side validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(form.email)) {
      setErr("Please enter a valid email address");
      return;
    }
    if (form.password.length < 8) {
      setErr("Password must be at least 8 characters");
      return;
    }
    if (mode === "signup") {
      if (form.name.trim().length < 2) {
        setErr("Company name must be at least 2 characters");
        return;
      }
      if (!/[A-Z]/.test(form.password) || !/[0-9]/.test(form.password)) {
        setErr("Password must contain at least one uppercase letter and one number");
        return;
      }
    }

    setLoading(true);
    try {
      if (mode === "signup") {
        const out = await api.companySignup(form);
        localStorage.setItem("fhn_role", "company");
        localStorage.setItem("fhn_company_id", String(out.company_id));
        localStorage.setItem("fhn_company_email", out.email);
        localStorage.setItem("fhn_company_name", out.name);
      } else {
        const out = await api.companyLogin({
          email: form.email,
          password: form.password,
        });
        localStorage.setItem("fhn_role", "company");
        localStorage.setItem("fhn_company_id", String(out.company_id));
        localStorage.setItem("fhn_company_email", out.email);
        localStorage.setItem("fhn_company_name", out.name);
      }
      navigate("/company");
    } catch (e2) {
      setErr(e2.message || "Auth failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ x: "100%" }}
      animate={{ x: 0 }}
      exit={{ x: "100%" }}
      transition={{ duration: 0.7, ease: [0.4, 0, 0.2, 1] }}
      className="fixed inset-0 z-[150] bg-[#E6E6E3] text-[#1c1c1c] overflow-y-auto selection:bg-black selection:text-white"
      style={{ willChange: "transform" }}
      data-lenis-prevent
    >
      <header className="sticky top-0 left-0 w-full bg-[#E6E6E3] border-b-[3px] border-[#1c1c1c] z-50 px-6 md:px-12 py-6 flex justify-between items-center bg-opacity-95 backdrop-blur-sm">
        <div className="flex items-center gap-6">
          <button
            onClick={onExit}
            className="px-6 py-3 border-[2px] border-[#1c1c1c] font-grotesk text-[11px] font-black uppercase tracking-[0.2em] hover:bg-[#1c1c1c] hover:text-[#E6E6E3] transition-all flex items-center gap-2 group"
          >
            <span className="group-hover:-translate-x-1 transition-transform inline-block">
              ←
            </span>{" "}
            BACK
          </button>
          <div className="h-10 w-[2px] bg-[#1c1c1c]/10 hidden md:block" />
          <span className="font-montreal font-black text-sm md:text-base tracking-[0.2em] uppercase text-[#1c1c1c]">
            COMPANY AUTH
          </span>
        </div>

        <div className="flex gap-2">
          {["login", "signup"].map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-5 py-2 font-grotesk text-[10px] font-black uppercase tracking-[0.25em] border-2 transition-all ${
                mode === m
                  ? "bg-black text-white border-black"
                  : "bg-transparent text-black border-black/20 hover:border-black"
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-[980px] mx-auto px-6 md:px-12 py-14 space-y-10">
        <h1 className="font-montreal font-black text-5xl md:text-7xl uppercase tracking-tighter leading-[0.9]">
          {mode === "signup" ? "CREATE COMPANY ACCESS" : "COMPANY LOGIN"}
        </h1>

        <div className="relative group">
          <div className="absolute inset-0 bg-black translate-x-1 translate-y-1 transition-transform group-hover:translate-x-2 group-hover:translate-y-2" />
          <div className="relative bg-white border-2 border-black p-6 md:p-10">
            <form onSubmit={submit} className="space-y-8">
              {err && (
                <div className="border-2 border-black bg-black text-white px-5 py-4 font-grotesk text-[10px] font-black uppercase tracking-[0.25em]">
                  ERROR: {err}
                </div>
              )}

              {mode === "signup" && (
                <div className="space-y-3">
                  <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.25em] opacity-60">
                    Company name
                  </label>
                  <input
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full bg-transparent border-b-4 border-black py-4 font-montreal text-4xl uppercase tracking-tighter focus:outline-none placeholder:text-black/10 font-black"
                    placeholder="ACME INC"
                    required
                  />
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-3">
                  <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.25em] opacity-60">
                    Email
                  </label>
                  <input
                    value={form.email}
                    onChange={(e) =>
                      setForm({ ...form, email: e.target.value })
                    }
                    className="w-full bg-transparent border-b-4 border-black py-4 font-montreal text-3xl uppercase tracking-tighter focus:outline-none placeholder:text-black/10 font-black"
                    placeholder="hr@company.com"
                    required
                  />
                </div>

                <div className="space-y-3">
                  <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.25em] opacity-60">
                    Password
                  </label>
                  <input
                    type="password"
                    value={form.password}
                    onChange={(e) =>
                      setForm({ ...form, password: e.target.value })
                    }
                    className="w-full bg-transparent border-b-4 border-black py-4 font-montreal text-3xl uppercase tracking-tighter focus:outline-none placeholder:text-black/10 font-black"
                    placeholder="••••••"
                    required
                  />
                </div>
              </div>

              <button
                disabled={loading}
                className="bg-black text-white px-10 py-4 font-grotesk text-[10px] font-black uppercase tracking-[0.3em] hover:bg-black/90 transition-all whitespace-nowrap shadow-[0_10px_25px_rgba(0,0,0,0.2)] disabled:opacity-50"
              >
                {loading
                  ? "PROCESSING..."
                  : mode === "signup"
                    ? "CREATE COMPANY"
                    : "LOGIN"}
              </button>
            </form>
          </div>
        </div>
      </main>
    </motion.div>
  );
}
