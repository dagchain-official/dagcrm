import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff, LogIn, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

// friendly AI mascot — inline SVG so it renders crisp in any theme
function Mascot() {
  return (
    <div className="relative mx-auto w-24 h-24">
      <div className="absolute inset-0 rounded-[1.75rem] bg-gradient-to-br from-brand-400 to-brand-600 shadow-lg shadow-brand-600/40" />
      <svg viewBox="0 0 64 64" className="absolute inset-0 w-full h-full p-3.5 text-white" fill="none">
        <line x1="32" y1="7" x2="32" y2="15" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
        <circle cx="32" cy="6" r="3" fill="currentColor" />
        <rect x="12" y="15" width="40" height="30" rx="11" fill="white" />
        <circle cx="25" cy="30" r="4.5" fill="#4f46e5" />
        <circle cx="39" cy="30" r="4.5" fill="#4f46e5" />
        <circle cx="26.4" cy="28.6" r="1.4" fill="white" />
        <circle cx="40.4" cy="28.6" r="1.4" fill="white" />
        <path d="M27 37 q5 4 10 0" stroke="#4f46e5" strokeWidth="2.4" strokeLinecap="round" fill="none" />
        <rect x="22" y="46" width="20" height="10" rx="5" fill="white" opacity="0.9" />
      </svg>
      <div className="absolute -right-1 -top-1 grid place-items-center w-7 h-7 rounded-xl bg-white text-brand-600 shadow">
        <Sparkles size={15} />
      </div>
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
