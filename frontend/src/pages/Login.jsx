import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Hexagon, LogIn } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("admin@dagos.com");
  const [password, setPassword] = useState("admin123");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const [forgot, setForgot] = useState(false);
  const [forgotMsg, setForgotMsg] = useState("");

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
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* brand panel */}
      <div className="hidden lg:flex flex-col justify-between p-12 bg-[#0f172a] text-white relative overflow-hidden">
        <div className="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-brand-600/30 blur-3xl" />
        <div className="absolute bottom-0 -left-24 w-96 h-96 rounded-full bg-brand-400/20 blur-3xl" />
        <div className="flex items-center gap-3 relative">
          <div className="grid place-items-center w-11 h-11 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600">
            <Hexagon size={24} />
          </div>
          <span className="text-2xl font-extrabold tracking-tight">DAGOS</span>
        </div>
        <div className="relative">
          <h1 className="text-4xl font-extrabold leading-tight">
            Run your entire business<br />from one command center.
          </h1>
          <p className="mt-4 text-ink-300 max-w-md">
            Leads, sales, support, HR, payroll, finance and an AI layer — unified
            in a single modern CRM built for scale.
          </p>
          <div className="mt-8 flex gap-6 text-sm text-ink-400">
            <span>● 20+ Modules</span>
            <span>● AI Lead Scoring</span>
            <span>● Real-time Reports</span>
          </div>
        </div>
        <p className="text-ink-500 text-sm relative">© 2026 DAGOS. All rights reserved.</p>
      </div>

      {/* form */}
      <div className="flex items-center justify-center p-6 lg:p-12 bg-ink-100">
        <form onSubmit={submit} className="card w-full max-w-md p-8">
          <div className="lg:hidden flex items-center gap-2 mb-6">
            <div className="grid place-items-center w-9 h-9 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 text-white">
              <Hexagon size={20} />
            </div>
            <span className="text-xl font-extrabold">DAGOS</span>
          </div>
          <h2 className="text-2xl font-extrabold text-ink-900">Welcome back</h2>
          <p className="text-sm text-ink-400 mt-1 mb-6">Sign in to your workspace</p>

          {err && <div className="mb-4 px-3 py-2 rounded-xl bg-rose-50 text-rose-600 text-sm">{err}</div>}

          <div className="space-y-4">
            <div>
              <label className="label">Email</label>
              <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <div className="flex items-center justify-between">
                <label className="label">Password</label>
                <button type="button" onClick={() => { setForgot(!forgot); setForgotMsg(""); }} className="text-xs font-semibold text-brand-600 hover:underline mb-1">
                  Forgot password?
                </button>
              </div>
              <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
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
            <LogIn size={17} /> {loading ? "Signing in…" : "Sign in"}
          </button>
          <p className="text-xs text-ink-400 text-center mt-4">
            Demo: admin@dagos.com / admin123
          </p>
        </form>
      </div>
    </div>
  );
}
