import { useEffect, useState } from "react";
import { Mail, Plus, Pencil, Trash2, Star, Send } from "lucide-react";
import api from "../api/client";
import { Modal } from "../components/ui";
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

const BLANK_ACCOUNT = {
  label: "", from_name: "", from_email: "", smtp_host: "", smtp_port: 587,
  smtp_username: "", smtp_password: "", use_tls: true, is_default: false, is_active: true,
};

function EmailAccountsCard() {
  const [accounts, setAccounts] = useState([]);
  const [editing, setEditing] = useState(null); // form object or null
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(null); // id being tested
  const [msg, setMsg] = useState(null);

  const load = () => api.get("/email-accounts/").then((r) => setAccounts(r.data)).catch(() => setAccounts([]));
  useEffect(() => { load(); }, []);

  const openNew = () => { setMsg(null); setEditing({ ...BLANK_ACCOUNT }); };
  const openEdit = (a) => { setMsg(null); setEditing({ ...a, smtp_password: "" }); };
  const set = (k) => (e) => {
    const v = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setEditing((f) => ({ ...f, [k]: v }));
  };

  const save = async () => {
    if (!editing.label || !editing.from_email) {
      setMsg({ type: "err", text: "Label and from-email are required" });
      return;
    }
    setSaving(true);
    setMsg(null);
    try {
      const body = { ...editing };
      if (editing.id && !body.smtp_password) delete body.smtp_password; // keep existing password
      if (editing.id) await api.patch(`/email-accounts/${editing.id}/`, body);
      else await api.post("/email-accounts/", body);
      setEditing(null);
      await load();
      setMsg({ type: "ok", text: "Email account saved" });
    } catch (err) {
      setMsg({ type: "err", text: err.response?.data?.detail || "Could not save account" });
    } finally {
      setSaving(false);
    }
  };

  const remove = async (a) => {
    if (!window.confirm(`Delete "${a.label}"?`)) return;
    await api.delete(`/email-accounts/${a.id}/`);
    await load();
  };

  const test = async (a) => {
    setTesting(a.id);
    setMsg(null);
    try {
      const { data } = await api.post(`/email-accounts/${a.id}/test/`);
      setMsg({ type: data.ok ? "ok" : "err", text: data.detail });
    } catch (err) {
      setMsg({ type: "err", text: err.response?.data?.detail || "SMTP test failed" });
    } finally {
      setTesting(null);
    }
  };

  return (
    <div className="card p-6 space-y-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-extrabold text-ink-900 flex items-center gap-2">
            <Mail size={18} className="text-brand-600" /> Business Email Accounts
          </h2>
          <p className="text-sm text-ink-400">
            Add the mailboxes you send leads from. You'll pick one when emailing a lead.
          </p>
        </div>
        <button className="btn-primary shrink-0" onClick={openNew}><Plus size={15} /> Add</button>
      </div>

      {accounts.length === 0 && (
        <p className="text-sm text-ink-400 rounded-xl border border-dashed border-ink-200 px-4 py-6 text-center">
          No email accounts yet. Add one to send emails from your own business address.
        </p>
      )}

      <div className="space-y-2">
        {accounts.map((a) => (
          <div key={a.id} className="flex items-center gap-3 rounded-xl border border-ink-100 px-4 py-3">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-ink-800 truncate">{a.label}</span>
                {a.is_default && (
                  <span className="inline-flex items-center gap-1 text-xs text-amber-600 bg-amber-50 rounded-full px-2 py-0.5">
                    <Star size={11} /> Default
                  </span>
                )}
                {!a.is_active && <span className="text-xs text-ink-400 bg-ink-50 rounded-full px-2 py-0.5">Inactive</span>}
              </div>
              <p className="text-sm text-ink-500 truncate">{a.from_email} · {a.smtp_host || "no SMTP"}</p>
            </div>
            <button className="btn-ghost px-2" title="Test SMTP" disabled={testing === a.id} onClick={() => test(a)}>
              <Send size={15} />
            </button>
            <button className="btn-ghost px-2" title="Edit" onClick={() => openEdit(a)}><Pencil size={15} /></button>
            <button className="btn-ghost px-2 text-rose-600" title="Delete" onClick={() => remove(a)}><Trash2 size={15} /></button>
          </div>
        ))}
      </div>

      <Message msg={msg} />

      <Modal
        open={!!editing}
        onClose={() => setEditing(null)}
        title={editing?.id ? "Edit email account" : "Add email account"}
        footer={<>
          <button className="btn-ghost" onClick={() => setEditing(null)}>Cancel</button>
          <button className="btn-primary" disabled={saving} onClick={save}>{saving ? "Saving…" : "Save"}</button>
        </>}
      >
        {editing && (
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Label</label>
              <input className="input" placeholder="FX Artha Sales" value={editing.label} onChange={set("label")} />
            </div>
            <div>
              <label className="label">Display name</label>
              <input className="input" placeholder="Your Name" value={editing.from_name} onChange={set("from_name")} />
            </div>
            <div className="sm:col-span-2">
              <label className="label">From email</label>
              <input className="input" type="email" placeholder="you@business.com" value={editing.from_email} onChange={set("from_email")} />
            </div>
            <div>
              <label className="label">SMTP host</label>
              <input className="input" placeholder="smtp.gmail.com" value={editing.smtp_host} onChange={set("smtp_host")} />
            </div>
            <div>
              <label className="label">SMTP port</label>
              <input className="input" type="number" value={editing.smtp_port} onChange={set("smtp_port")} />
            </div>
            <div>
              <label className="label">SMTP username</label>
              <input className="input" placeholder="you@business.com" value={editing.smtp_username} onChange={set("smtp_username")} />
            </div>
            <div>
              <label className="label">SMTP password {editing.id && <span className="text-ink-400 font-normal">(blank = keep)</span>}</label>
              <input className="input" type="password" placeholder="app password" value={editing.smtp_password} onChange={set("smtp_password")} />
            </div>
            <label className="flex items-center gap-2 text-sm text-ink-600">
              <input type="checkbox" checked={editing.use_tls} onChange={set("use_tls")} /> Use TLS
            </label>
            <label className="flex items-center gap-2 text-sm text-ink-600">
              <input type="checkbox" checked={editing.is_default} onChange={set("is_default")} /> Set as default
            </label>
            <label className="flex items-center gap-2 text-sm text-ink-600 sm:col-span-2">
              <input type="checkbox" checked={editing.is_active} onChange={set("is_active")} /> Active
            </label>
            <p className="text-xs text-ink-400 sm:col-span-2">
              For Gmail use an App Password (host <b>smtp.gmail.com</b>, port <b>587</b>, TLS on). Use “Test SMTP” after saving.
            </p>
          </div>
        )}
      </Modal>
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
      <EmailAccountsCard />
      <PasswordCard />
    </div>
  );
}
