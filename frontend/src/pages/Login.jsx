import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff, LogIn } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

// 3D-style waving AI robot — inline SVG (glossy white body, dark face screen,
// glowing bar eyes + smile, raised waving arm) recreated from the reference art.
function Robot({ className = "" }) {
  return (
    <svg viewBox="0 0 260 285" className={className} fill="none">
      <defs>
        <linearGradient id="r-white" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="100%" stopColor="#dbe1ec" />
        </linearGradient>
        <linearGradient id="r-screen" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1b2542" />
          <stop offset="100%" stopColor="#060a15" />
        </linearGradient>
        <linearGradient id="r-eye" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="100%" stopColor="#a9e8ff" />
        </linearGradient>
        <filter id="r-glow" x="-70%" y="-70%" width="240%" height="240%">
          <feGaussianBlur stdDeviation="2.4" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id="r-soft" x="-40%" y="-40%" width="180%" height="180%">
          <feDropShadow dx="0" dy="8" stdDeviation="9" floodColor="#03060f" floodOpacity="0.4" />
        </filter>
      </defs>

      {/* left arm (hanging) */}
      <path d="M96 192 q-28 4 -36 42" stroke="#0e1630" strokeWidth="9" fill="none" strokeLinecap="round" />
      <rect x="50" y="224" width="18" height="30" rx="9" fill="url(#r-white)" />
      <circle cx="59" cy="258" r="9" fill="url(#r-white)" />
      <line x1="55" y1="264" x2="53" y2="272" stroke="#0e1630" strokeWidth="3" strokeLinecap="round" />
      <line x1="59" y1="265" x2="59" y2="273" stroke="#0e1630" strokeWidth="3" strokeLinecap="round" />
      <line x1="63" y1="264" x2="65" y2="272" stroke="#0e1630" strokeWidth="3" strokeLinecap="round" />

      {/* right arm (waving up) */}
      <path d="M170 176 q36 -2 44 -36" stroke="#0e1630" strokeWidth="9" fill="none" strokeLinecap="round" />
      <rect x="203" y="120" width="18" height="30" rx="9" fill="url(#r-white)" />
      <circle cx="212" cy="116" r="10" fill="url(#r-white)" />
      <line x1="207" y1="110" x2="205" y2="100" stroke="#0e1630" strokeWidth="3.4" strokeLinecap="round" />
      <line x1="212" y1="109" x2="212" y2="99" stroke="#0e1630" strokeWidth="3.4" strokeLinecap="round" />
      <line x1="217" y1="110" x2="219" y2="100" stroke="#0e1630" strokeWidth="3.4" strokeLinecap="round" />

      {/* body */}
      <path d="M92 172 h76 a30 30 0 0 1 30 30 v4 a68 68 0 0 1 -136 0 v-4 a30 30 0 0 1 30 -30 z" fill="url(#r-white)" filter="url(#r-soft)" />
      <ellipse cx="130" cy="190" rx="42" ry="11" fill="#ffffff" opacity="0.55" />

      {/* antenna */}
      <line x1="130" y1="46" x2="130" y2="22" stroke="#0e1630" strokeWidth="6" strokeLinecap="round" />
      <circle cx="130" cy="16" r="9" fill="#0e1630" />

      {/* head */}
      <rect x="50" y="46" width="160" height="134" rx="54" fill="url(#r-white)" filter="url(#r-soft)" />
      <rect x="38" y="94" width="22" height="44" rx="11" fill="#0e1630" />
      <rect x="200" y="94" width="22" height="44" rx="11" fill="#0e1630" />

      {/* face screen */}
      <rect x="72" y="68" width="116" height="90" rx="36" fill="url(#r-screen)" />
      <path d="M82 82 q44 -16 88 4 q-44 -7 -88 -1 z" fill="#ffffff" opacity="0.2" />

      {/* glowing bar eyes + smile */}
      <rect x="103" y="94" width="11" height="36" rx="5.5" fill="url(#r-eye)" filter="url(#r-glow)" />
      <rect x="146" y="94" width="11" height="36" rx="5.5" fill="url(#r-eye)" filter="url(#r-glow)" />
      <path d="M118 137 q12 12 24 0" stroke="url(#r-eye)" strokeWidth="4.5" fill="none" strokeLinecap="round" filter="url(#r-glow)" />

      {/* head gloss */}
      <ellipse cx="90" cy="68" rx="27" ry="13" fill="#ffffff" opacity="0.6" />
    </svg>
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
    <div className="min-h-screen grid lg:grid-cols-2 bg-ink-50">
      {/* left — big robot showcase */}
      <div className="relative hidden lg:grid place-items-center overflow-hidden bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900">
        <div className="absolute w-[38rem] h-[38rem] rounded-full bg-brand-400/20 blur-3xl" />
        <div className="absolute w-[24rem] h-[24rem] rounded-full bg-white/10 blur-3xl" />
        <div className="relative flex flex-col items-center gap-6 px-10">
          <Robot className="w-[74%] max-w-md drop-shadow-2xl" />
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-white tracking-tight">DAGOS</h2>
            <p className="text-white/60 mt-1 max-w-xs">Your AI Business CRM — run leads, sales, HR &amp; finance from one place.</p>
          </div>
        </div>
      </div>

      {/* right — login form (adapts to light / dark theme) */}
      <div className="grid place-items-center p-6 lg:p-12">
        <form onSubmit={submit} className="w-full max-w-sm">
          <div className="lg:hidden flex flex-col items-center mb-4">
            <Robot className="w-36" />
            <h1 className="text-2xl font-extrabold text-ink-900 mt-1">DAGOS</h1>
          </div>

          <h2 className="text-2xl font-extrabold text-ink-900">Welcome back 👋</h2>
          <p className="text-sm text-ink-400 mt-1 mb-6">Sign in to your workspace</p>

          {err && <div className="mb-4 px-3 py-2 rounded-xl bg-rose-50 text-rose-600 text-sm">{err}</div>}

          <div className="space-y-4">
            <div>
              <label className="label">Username / Email</label>
              <input className="input" type="email" placeholder="you@company.com"
                value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <div className="flex items-center justify-between">
                <label className="label">Password</label>
                <button type="button" onClick={() => { setForgot(!forgot); setForgotMsg(""); }}
                  className="text-xs font-semibold text-brand-600 hover:underline mb-1">Forgot password?</button>
              </div>
              <div className="relative">
                <input className="input pr-10" type={showPw ? "text" : "password"} placeholder="••••••••"
                  value={password} onChange={(e) => setPassword(e.target.value)} required />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  aria-label={showPw ? "Hide password" : "Show password"}
                  className="absolute inset-y-0 right-3 grid place-items-center text-ink-400 hover:text-ink-600">
                  {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm text-ink-500 select-none cursor-pointer">
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)}
                className="w-4 h-4 rounded accent-brand-600" />
              Remember me
            </label>
          </div>

          {forgot && (
            <div className="mt-4 p-3 rounded-xl bg-ink-50 border border-ink-100">
              <p className="text-xs text-ink-500 mb-2">Enter your email above, then send a reset link.</p>
              {forgotMsg && <p className="text-xs text-emerald-600 mb-2">{forgotMsg}</p>}
              <button type="button" onClick={sendReset} className="btn-ghost text-sm w-full border border-ink-200">
                Send reset link
              </button>
            </div>
          )}

          <button className="btn-primary w-full mt-6" disabled={loading}>
            <LogIn size={17} /> {loading ? "Signing in…" : "Sign In"}
          </button>
          <p className="text-xs text-ink-400 text-center mt-4">Demo: admin@dagos.com / admin123</p>
        </form>
      </div>
    </div>
  );
}
