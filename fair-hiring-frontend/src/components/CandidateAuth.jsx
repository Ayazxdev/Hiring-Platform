import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { api } from "../api/backend";
import { useAuth } from "../auth/useAuth";

export default function CandidateAuth({ onExit }) {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [form, setForm] = useState({ name: "", email: "", password: "" });

  // Optional Auth0 SSO hook
  const { isAuthenticated, isLoading, loginWithRedirect, syncWithBackend } = useAuth();
  const auth0Domain = import.meta.env.VITE_AUTH0_DOMAIN;
  const isAuth0Configured = Boolean(
    auth0Domain &&
    !auth0Domain.includes("your_") &&
    import.meta.env.VITE_AUTH0_CLIENT_ID
  );

  // Sync if Auth0 redirect took place
  useEffect(() => {
    if (!isAuth0Configured || !isAuthenticated || isLoading) return;

    if (localStorage.getItem("fhn_candidate_anon_id")) {
      navigate("/candidate");
      return;
    }

    syncWithBackend()
      .then((data) => {
        localStorage.setItem("fhn_role", "candidate");
        localStorage.setItem("fhn_candidate_anon_id", data.anon_id);
        localStorage.setItem("fhn_candidate_email", data.email);
        localStorage.setItem("fhn_candidate_name", data.name || "Candidate");
        navigate("/candidate");
      })
      .catch((e) => {
        console.error("[Auth0 Sync Error]", e);
        navigate("/candidate");
      });
  }, [isAuthenticated, isLoading, navigate, syncWithBackend, isAuth0Configured]);

  const submit = async (e) => {
    e.preventDefault();
    setErr("");

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(form.email.trim())) {
      setErr("Please enter a valid email address.");
      return;
    }

    if (form.password.length < 8) {
      setErr("Password must be at least 8 characters long.");
      return;
    }

    if (mode === "signup") {
      if (form.name.trim().length < 2) {
        setErr("Full name must be at least 2 characters.");
        return;
      }
      if (!/[A-Z]/.test(form.password) || !/[0-9]/.test(form.password) || !/[!@#$%^&*(),.?":{}|<>]/.test(form.password)) {
        setErr("Password must contain at least 1 uppercase letter, 1 number, and 1 symbol (e.g. !@#$).");
        return;
      }
    }

    setLoading(true);
    try {
      if (mode === "signup") {
        const out = await api.candidateSignup({
          name: form.name.trim(),
          email: form.email.trim().toLowerCase(),
          password: form.password,
        });
        localStorage.setItem("fhn_role", "candidate");
        localStorage.setItem("fhn_candidate_id", String(out.id));
        localStorage.setItem("fhn_candidate_anon_id", out.anon_id);
        localStorage.setItem("fhn_candidate_email", out.email);
        localStorage.setItem("fhn_candidate_name", out.name);
      } else {
        const out = await api.candidateLogin({
          email: form.email.trim().toLowerCase(),
          password: form.password,
        });
        localStorage.setItem("fhn_role", "candidate");
        localStorage.setItem("fhn_candidate_id", String(out.id));
        localStorage.setItem("fhn_candidate_anon_id", out.anon_id);
        localStorage.setItem("fhn_candidate_email", out.email);
        localStorage.setItem("fhn_candidate_name", out.name);
      }
      navigate("/candidate");
    } catch (e2) {
      setErr(e2.message || "Authentication failed. Please check credentials.");
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
      {/* Header */}
      <header className="sticky top-0 left-0 w-full bg-[#E6E6E3] border-b-[3px] border-[#1c1c1c] z-50 px-6 md:px-12 py-6 flex justify-between items-center bg-opacity-95 backdrop-blur-sm">
        <div className="flex items-center gap-6">
          <button
            onClick={onExit}
            className="px-6 py-3 border-[2px] border-[#1c1c1c] font-grotesk text-[11px] font-black uppercase tracking-[0.2em] hover:bg-[#1c1c1c] hover:text-[#E6E6E3] transition-all flex items-center gap-2 group"
          >
            <span className="group-hover:-translate-x-1 transition-transform inline-block">←</span>{" "}
            BACK
          </button>
          <div className="h-10 w-[2px] bg-[#1c1c1c]/10 hidden md:block" />
          <span className="font-montreal font-black text-sm md:text-base tracking-[0.2em] uppercase text-[#1c1c1c]">
            CANDIDATE ACCESS
          </span>
        </div>

        <div className="flex gap-2">
          {["login", "signup"].map((m) => (
            <button
              key={m}
              onClick={() => {
                setMode(m);
                setErr("");
              }}
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

      {/* Main Container */}
      <main className="max-w-[980px] mx-auto px-6 md:px-12 py-14 space-y-10">
        <div className="space-y-2">
          <h1 className="font-montreal font-black text-5xl md:text-7xl uppercase tracking-tighter leading-[0.9]">
            {mode === "signup" ? "CREATE CANDIDATE ID" : "CANDIDATE LOGIN"}
          </h1>
          <p className="font-inter text-sm font-bold opacity-70">
            {mode === "signup"
              ? "Register directly to get your unique anonymous cryptographic ID and start applying."
              : "Sign in with your email and password to access your applications and Skill Passport."}
          </p>
        </div>

        <div className="relative group">
          <div className="absolute inset-0 bg-black translate-x-1 translate-y-1 transition-transform group-hover:translate-x-2 group-hover:translate-y-2" />
          <div className="relative bg-white border-2 border-black p-6 md:p-10 space-y-8">
            <form onSubmit={submit} className="space-y-8">
              {err && (
                <div className="border-2 border-black bg-black text-white px-5 py-4 font-grotesk text-[10px] font-black uppercase tracking-[0.25em]">
                  ERROR: {err}
                </div>
              )}

              {mode === "signup" && (
                <div className="space-y-3">
                  <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.25em] opacity-60">
                    Full Name
                  </label>
                  <input
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full bg-transparent border-b-4 border-black py-4 font-montreal text-3xl md:text-4xl uppercase tracking-tighter focus:outline-none placeholder:text-black/10 font-black"
                    placeholder="ALICE SMITH"
                    required
                  />
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-3">
                  <label className="font-grotesk text-[10px] font-black uppercase tracking-[0.25em] opacity-60">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="w-full bg-transparent border-b-4 border-black py-4 font-montreal text-2xl md:text-3xl uppercase tracking-tighter focus:outline-none placeholder:text-black/10 font-black"
                    placeholder="candidate@example.com"
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
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    className="w-full bg-transparent border-b-4 border-black py-4 font-montreal text-2xl md:text-3xl uppercase tracking-tighter focus:outline-none placeholder:text-black/10 font-black"
                    placeholder="••••••••"
                    required
                  />
                  {mode === "signup" && (
                    <p className="font-inter text-[9px] font-bold opacity-50 uppercase tracking-wider">
                      Min 8 chars, 1 uppercase, 1 number, 1 symbol (e.g. !@#$)
                    </p>
                  )}
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-black text-white px-10 py-5 font-grotesk text-[10px] font-black uppercase tracking-[0.3em] hover:bg-black/90 transition-all shadow-[0_10px_25px_rgba(0,0,0,0.2)] disabled:opacity-50"
                >
                  {loading
                    ? "AUTHENTICATING..."
                    : mode === "signup"
                    ? "CREATE CANDIDATE ACCOUNT"
                    : "LOG IN"}
                </button>

                {isAuth0Configured && (
                  <button
                    type="button"
                    onClick={() =>
                      loginWithRedirect({
                        appState: { returnTo: "/candidate" },
                        authorizationParams: { screen_hint: mode === "signup" ? "signup" : "login" },
                      })
                    }
                    className="bg-transparent border-2 border-black text-black px-8 py-5 font-grotesk text-[10px] font-black uppercase tracking-[0.3em] hover:bg-black hover:text-white transition-all"
                  >
                    CONTINUE WITH AUTH0
                  </button>
                )}
              </div>
            </form>

            {/* Info Badges */}
            <div className="border-t-2 border-black/10 pt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { icon: "🔒", label: "LOCAL & SECURE", desc: "Encrypted password storage" },
                { icon: "⚡", label: "INSTANT ACCESS", desc: "Automatic cryptographic Anon ID" },
                { icon: "🛡️", label: "ZERO BIAS", desc: "PII anonymization during audits" },
              ].map((item) => (
                <div key={item.label} className="flex items-start gap-3">
                  <span className="text-lg">{item.icon}</span>
                  <div>
                    <div className="font-grotesk text-[8px] font-black uppercase tracking-[0.3em]">
                      {item.label}
                    </div>
                    <div className="font-inter text-[10px] opacity-50 mt-0.5">
                      {item.desc}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="font-inter text-[10px] font-bold uppercase tracking-widest opacity-50">
              Personal identity details are stored only for verified audit records and never exposed in the scoring pipeline.
            </div>
          </div>
        </div>
      </main>
    </motion.div>
  );
}
