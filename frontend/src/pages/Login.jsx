import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff, LogIn } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

// friendly 3D-style AI robot — inline SVG (radial-gradient shading, gloss
// highlights, drop shadows + a floating chat bubble) so it renders crisp anywhere
function Mascot() {
  return (
    <div className="mx-auto w-44 h-40 -mt-2">
      <svg viewBox="0 0 200 190" className="w-full h-full">
        <defs>
          <radialGradient id="m-head" cx="38%" cy="28%" r="85%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="55%" stopColor="#eef1f7" />
            <stop offset="100%" stopColor="#bcc3d4" />
          </radialGradient>
          <radialGradient id="m-body" cx="40%" cy="22%" r="95%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#b9c0d1" />
          </radialGradient>
          <linearGradient id="m-face" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#20326b" />
            <stop offset="100%" stopColor="#0b1330" />
          </linearGradient>
          <radialGradient id="m-eye" cx="50%" cy="38%" r="65%">
            <stop offset="0%" stopColor="#a9f4ff" />
            <stop offset="100%" stopColor="#22a7ff" />
          </radialGradient>
          <linearGradient id="m-bub" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#8ff2e2" />
            <stop offset="100%" stopColor="#37c8bf" />
          </linearGradient>
          <filter id="m-soft" x="-40%" y="-40%" width="180%" height="180%">
            <feDropShadow dx="0" dy="7" stdDeviation="7" floodColor="#0a0f2e" floodOpacity="0.35" />
          </filter>
        </defs>

        <ellipse cx="104" cy="176" rx="46" ry="8" fill="#05081f" opacity="0.25" />

        {/* chat bubble */}
        <g filter="url(#m-soft)">
          <path d="M20 30 h44 a14 14 0 0 1 14 14 v10 a14 14 0 0 1 -14 14 H40 l-11 12 l2 -12 h-11 a14 14 0 0 1 -14 -14 v-10 a14 14 0 0 1 14 -14 z" fill="url(#m-bub)" />
          <circle cx="30" cy="49" r="3.4" fill="#ffffff" opacity="0.9" />
          <circle cx="42" cy="49" r="3.4" fill="#ffffff" opacity="0.9" />
          <circle cx="54" cy="49" r="3.4" fill="#ffffff" opacity="0.9" />
        </g>

        {/* antenna */}
        <line x1="112" y1="44" x2="112" y2="28" stroke="#c9cfdd" strokeWidth="4.5" strokeLinecap="round" />
        <circle cx="112" cy="23" r="10" fill="#22a7ff" opacity="0.25" />
        <circle cx="112" cy="23" r="6" fill="url(#m-eye)" />

        {/* body + arms */}
        <rect x="80" y="126" width="70" height="48" rx="22" fill="url(#m-body)" filter="url(#m-soft)" />
        <circle cx="74" cy="144" r="11" fill="url(#m-body)" />
        <circle cx="156" cy="144" r="11" fill="url(#m-body)" />
        <rect x="98" y="138" width="34" height="16" rx="8" fill="#d9deea" />

        {/* head */}
        <rect x="66" y="48" width="92" height="80" rx="32" fill="url(#m-head)" filter="url(#m-soft)" />
        <rect x="58" y="76" width="10" height="26" rx="5" fill="#c9cfdd" />
        <rect x="156" y="76" width="10" height="26" rx="5" fill="#c9cfdd" />

        {/* face + eyes + smile */}
        <rect x="78" y="62" width="68" height="52" rx="24" fill="url(#m-face)" />
        <rect x="82" y="66" width="60" height="18" rx="12" fill="#ffffff" opacity="0.07" />
        <ellipse cx="100" cy="86" rx="8" ry="9" fill="url(#m-eye)" />
        <ellipse cx="124" cy="86" rx="8" ry="9" fill="url(#m-eye)" />
        <circle cx="102.5" cy="82.5" r="2.5" fill="#fff" />
        <circle cx="126.5" cy="82.5" r="2.5" fill="#fff" />
        <path d="M101 99 q11 8 22 0" stroke="#a9f4ff" strokeWidth="3" fill="none" strokeLinecap="round" />
        <ellipse cx="94" cy="62" rx="20" ry="10" fill="#ffffff" opacity="0.55" />
      </svg>
    </div>
  );
}

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("admin@dagos.com");
  const [password, setPassword] = useState("admin123");
  const [remember, setRemember] = useState(true);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const [forgot, setForgot] = useState(false);
  const [forgotMsg, setForgotMsg] = useState("");
  const [showPw, setShowPw] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      await login(email, password);
      nav("/");
    } catch {
      setErr("Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  const sendReset = async () => {
    setForgotMsg("");
    try {
      const { data } = await api.post("/auth/forgot-password/", { email });
      setForgotMsg(data.status);
    } catch {
      setForgotMsg("Could not send reset link. Try again.");
    }
  };

  return (
    <div className="relative min-h-screen grid place-items-center p-4 overflow-hidden
                    bg-gradient-to-br from-indigo-700 via-violet-700 to-blue-800">
      {/* decorative glows */}
      <div className="absolute -top-32 -left-24 w-96 h-96 rounded-full bg-white/10 blur-3xl" />
      <div className="absolute -bottom-40 -right-24 w-[28rem] h-[28rem] rounded-full bg-brand-400/20 blur-3xl" />

      <div className="relative w-full max-w-sm">
        <div className="bg-white/10 backdrop-blur-xl border border-white/15 rounded-[2rem] p-8 shadow-2xl">
          <Mascot />

          <div className="text-center mt-4 mb-6">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">DAGOS</h1>
            <p className="text-sm text-white/60 mt-0.5">AI Business CRM · sign in to your workspace</p>
          </div>

          {err && <div className="mb-4 px-3 py-2 rounded-xl bg-rose-500/20 text-rose-100 text-sm text-center">{err}</div>}

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-white/70 mb-1.5">Username / Email</label>
              <input
                className="w-full px-4 py-2.5 rounded-xl bg-white/90 text-ink-900 text-sm placeholder-ink-400
                           outline-none focus:ring-2 focus:ring-white/60 transition"
                type="email" placeholder="you@company.com"
                value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-white/70">Password</label>
                <button type="button" onClick={() => { setForgot(!forgot); setForgotMsg(""); }}
                  className="text-xs font-semibold text-white/70 hover:text-white">Forgot password?</button>
              </div>
              <div className="relative">
                <input
                  className="w-full px-4 py-2.5 pr-10 rounded-xl bg-white/90 text-ink-900 text-sm placeholder-ink-400
                             outline-none focus:ring-2 focus:ring-white/60 transition"
                  type={showPw ? "text" : "password"} placeholder="••••••••"
                  value={password} onChange={(e) => setPassword(e.target.value)} required />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  aria-label={showPw ? "Hide password" : "Show password"}
                  className="absolute inset-y-0 right-3 grid place-items-center text-ink-400 hover:text-ink-600">
                  {showPw ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm text-white/70 select-none cursor-pointer">
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)}
                className="w-4 h-4 rounded accent-brand-500" />
              Remember me
            </label>

            {forgot && (
              <div className="p-3 rounded-xl bg-white/10 border border-white/15">
                <p className="text-xs text-white/70 mb-2">Enter your email above, then send a reset link.</p>
                {forgotMsg && <p className="text-xs text-emerald-200 mb-2">{forgotMsg}</p>}
                <button type="button" onClick={sendReset}
                  className="w-full text-sm font-semibold py-2 rounded-xl bg-white/15 text-white hover:bg-white/25 transition">
                  Send reset link
                </button>
              </div>
            )}

            <button
              className="w-full inline-flex items-center justify-center gap-2 py-2.5 rounded-xl font-bold text-white
                         bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700
                         shadow-lg shadow-brand-900/30 disabled:opacity-60 transition"
              disabled={loading}>
              <LogIn size={17} /> {loading ? "Signing in…" : "Sign In"}
            </button>
          </form>

          <p className="text-[11px] text-white/40 text-center mt-5">Demo: admin@dagos.com / admin123</p>
        </div>
        <p className="text-center text-white/40 text-xs mt-4">© 2026 DAGOS. All rights reserved.</p>
      </div>
    </div>
  );
}
