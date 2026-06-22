import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Hexagon, KeyRound } from "lucide-react";
import api from "../api/client";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const nav = useNavigate();
  const uid = params.get("uid");
  const token = params.get("token");
  const [pw, setPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setMsg(null);
    if (pw.length < 6) return setMsg({ type: "err", text: "Password must be at least 6 characters." });
    if (pw !== confirm) return setMsg({ type: "err", text: "Passwords do not match." });
    setLoading(true);
    try {
      await api.post("/auth/reset-password/", { uid, token, new_password: pw });
      setMsg({ type: "ok", text: "Password reset! Redirecting to sign in…" });
      setTimeout(() => nav("/login"), 1500);
    } catch (e2) {
      setMsg({ type: "err", text: e2.response?.data?.detail || "Reset failed." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid place-items-center bg-ink-100 p-6">
      <form onSubmit={submit} className="card w-full max-w-md p-8">
        <div className="flex items-center gap-2 mb-6">
          <div className="grid place-items-center w-9 h-9 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 text-white"><Hexagon size={20} /></div>
          <span className="text-xl font-extrabold text-ink-900">DAGOS</span>
        </div>
        <h2 className="text-2xl font-extrabold text-ink-900">Reset password</h2>
        <p className="text-sm text-ink-400 mt-1 mb-6">Enter your new password below.</p>

        {!uid || !token ? (
          <div className="px-3 py-2 rounded-xl bg-rose-50 text-rose-600 text-sm">
            Invalid or missing reset link. <Link to="/login" className="font-semibold underline">Back to login</Link>
          </div>
        ) : (
          <>
            {msg && <div className={`mb-4 px-3 py-2 rounded-xl text-sm ${msg.type === "ok" ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-600"}`}>{msg.text}</div>}
            <div className="space-y-4">
              <div>
                <label className="label">New password</label>
                <input className="input" type="password" value={pw} onChange={(e) => setPw(e.target.value)} required />
              </div>
              <div>
                <label className="label">Confirm password</label>
                <input className="input" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
              </div>
            </div>
            <button className="btn-primary w-full mt-6" disabled={loading}>
              <KeyRound size={17} /> {loading ? "Resetting…" : "Reset password"}
            </button>
            <Link to="/login" className="block text-center text-sm text-ink-500 mt-4 hover:text-ink-800">Back to sign in</Link>
          </>
        )}
      </form>
    </div>
  );
}
