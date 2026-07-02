import { useState } from "react";
import { UserPlus, Check, X } from "lucide-react";
import api from "../api/client";
import RefSelect from "../components/RefSelect";
import usePolling from "../hooks/usePolling";
import { Badge, Spinner, EmptyState } from "../components/ui";
import { STATUS_COLORS } from "../config/resources";
import { useToast } from "../context/ToastContext";

export default function TeamRequests() {
  const toast = useToast();
  const [rows, setRows] = useState(null);
  const [member, setMember] = useState("");
  const [team, setTeam] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);

  usePolling(() => {
    api.get("/team-requests/").then(({ data }) => setRows(data.results || data)).catch(() => setRows([]));
  }, 3000, []);

  const raise = async () => {
    if (!member) return toast.error("Select a person to request");
    setBusy(true);
    try {
      await api.post("/team-requests/", { member, team: team || null, reason });
      toast.success("Request sent for approval");
      setMember(""); setTeam(""); setReason("");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Request failed");
    } finally { setBusy(false); }
  };

  const decide = async (id, action) => {
    try {
      await api.post(`/team-requests/${id}/${action}/`);
      toast.success(`Request ${action === "approve" ? "approved" : "rejected"}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Action failed");
    }
  };

  return (
    <div className="space-y-5 max-w-4xl">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
          <UserPlus className="text-brand-600" /> Team Member Requests
        </h1>
        <p className="text-sm text-ink-400">A Sales Manager requests a person; a higher authority approves. Approved → added to the team.</p>
      </div>

      {/* raise a request */}
      <div className="card p-5">
        <h3 className="font-bold text-ink-800 mb-3">Request a team member</h3>
        <div className="grid sm:grid-cols-3 gap-3">
          <div>
            <label className="label">Person</label>
            <RefSelect field={{ ref: "users", labelKey: "name", label: "Person" }} value={member} onChange={setMember} />
          </div>
          <div>
            <label className="label">Into team</label>
            <RefSelect field={{ ref: "teams", labelKey: "name", label: "Team" }} value={team} onChange={setTeam} />
          </div>
          <div>
            <label className="label">Reason (optional)</label>
            <input className="input" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Why?" />
          </div>
        </div>
        <div className="flex justify-end mt-3">
          <button className="btn-primary" disabled={busy || !member} onClick={raise}>
            {busy ? "Sending…" : "Send Request"}
          </button>
        </div>
      </div>

      {/* list */}
      <div className="card p-5">
        <h3 className="font-bold text-ink-800 mb-3">Requests</h3>
        {rows === null ? <Spinner /> : rows.length === 0 ? (
          <EmptyState title="No requests" hint="Raised requests + your team's requests show here." />
        ) : (
          <div className="divide-y divide-ink-100">
            {rows.map((r) => (
              <div key={r.id} className="flex items-center gap-3 py-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-ink-800">
                    {r.requested_by_name} → wants <b>{r.member_name}</b>
                    {r.team_name && <span className="text-ink-400"> in {r.team_name}</span>}
                  </p>
                  {r.reason && <p className="text-xs text-ink-400">{r.reason}</p>}
                  {r.decided_by_name && <p className="text-[11px] text-ink-400">Decided by {r.decided_by_name}</p>}
                </div>
                <Badge value={r.status} map={STATUS_COLORS} />
                {r.status === "pending" && (
                  <div className="flex gap-1.5">
                    <button className="btn-ghost border border-emerald-200 text-emerald-700 !px-2.5 !py-1.5" onClick={() => decide(r.id, "approve")}><Check size={15} /></button>
                    <button className="btn-ghost border border-rose-200 text-rose-600 !px-2.5 !py-1.5" onClick={() => decide(r.id, "reject")}><X size={15} /></button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
