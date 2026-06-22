import { useEffect, useState } from "react";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";

function initials(name) {
  return (name || "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0])
    .join("")
    .toUpperCase() || "?";
}

function Message({ msg }) {
  if (!msg) return null;
  return (
    <p
      className={`text-sm rounded-xl px-4 py-2 border ${
        msg.type === "ok"
          ? "text-emerald-700 bg-emerald-50 border-emerald-100"
          : "text-rose-700 bg-rose-50 border-rose-100"
      }`}
    >
      {msg.text}
    </p>
  );
}

function ProfileCard() {
  const { user, refreshUser } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", phone: "" });
  const [msg, setMsg] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user) {
      setForm({
        name: user.name || "",
        email: user.email || "",
        phone: user.phone || "",
      });
    }
  }, [user]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const save = async () => {
    setSaving(true);
    setMsg(null);
    try {
      await api.patch("/auth/profile/", form);
      await refreshUser();
      setMsg({ type: "ok", text: "Profile updated" });
    } catch (err) {
      setMsg({
        type: "err",
        text: err.response?.data?.detail || "Could not update profile",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card p-6 space-y-5">
      <div>
        <h2 className="text-lg font-extrabold text-ink-900">Profile</h2>
        <p className="text-sm text-ink-400">Your account details</p>
      </div>

      <div className="flex items-center gap-4">
        <div className="grid place-items-center w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 text-white text-2xl font-extrabold">
          {initials(user?.name)}
        </div>
        <div>
          <p className="font-semibold text-ink-800">{user?.name}</p>
          <p className="text-sm text-ink-400">{user?.role_name}</p>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Name</label>
          <input className="input" value={form.name} onChange={set("name")} />
        </div>
        <div>
          <label className="label">Email</label>
          <input className="input" type="email" value={form.email} onChange={set("email")} />
        </div>
        <div>
          <label className="label">Phone</label>
          <input className="input" value={form.phone} onChange={set("phone")} />
        </div>
        <div>
          <label className="label">Role</label>
          <input className="input opacity-70" value={user?.role_name || ""} disabled />
        </div>
        <div>
          <label className="label">Employee ID</label>
          <input className="input opacity-70" value={user?.employee_id || ""} disabled />
        </div>
      </div>

      <Message msg={msg} />

      <div className="flex justify-end">
        <button className="btn-primary" onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save changes"}
        </button>
      </div>
    </div>
  );
}

function PasswordCard() {
  const [fields, setFields] = useState({ current: "", next: "", confirm: "" });
  const [msg, setMsg] = useState(null);
  const [saving, setSaving] = useState(false);

  const set = (k) => (e) => setFields((f) => ({ ...f, [k]: e.target.value }));

  const update = async () => {
    setMsg(null);
    if (fields.next !== fields.confirm) {
      setMsg({ type: "err", text: "New passwords do not match" });
      return;
    }
    if (fields.next.length < 6) {
      setMsg({ type: "err", text: "New password must be at least 6 characters" });
      return;
    }
    setSaving(true);
    try {
      await api.post("/auth/change-password/", {
        old_password: fields.current,
        new_password: fields.next,
      });
      setMsg({ type: "ok", text: "Password changed successfully" });
      setFields({ current: "", next: "", confirm: "" });
    } catch (err) {
      setMsg({
        type: "err",
        text: err.response?.data?.detail || "Could not change password",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card p-6 space-y-5">
      <div>
        <h2 className="text-lg font-extrabold text-ink-900">Change Password</h2>
        <p className="text-sm text-ink-400">Update your account password</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="label">Current password</label>
          <input className="input" type="password" value={fields.current} onChange={set("current")} />
        </div>
        <div>
          <label className="label">New password</label>
          <input className="input" type="password" value={fields.next} onChange={set("next")} />
        </div>
        <div>
          <label className="label">Confirm new password</label>
          <input className="input" type="password" value={fields.confirm} onChange={set("confirm")} />
        </div>
      </div>

      <Message msg={msg} />

      <div className="flex justify-end">
        <button className="btn-primary" onClick={update} disabled={saving}>
          {saving ? "Updating…" : "Update password"}
        </button>
      </div>
    </div>
  );
}

export default function ProfileSettings() {
  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900">Settings</h1>
        <p className="text-sm text-ink-400">Manage your profile and account security</p>
      </div>

      <ProfileCard />
      <PasswordCard />
    </div>
  );
}
