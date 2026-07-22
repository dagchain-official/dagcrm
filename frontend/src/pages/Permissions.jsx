import { useEffect, useMemo, useState } from "react";
import { ShieldCheck, Building2, Check } from "lucide-react";
import api from "../api/client";
import { Spinner } from "../components/ui";
import { useToast } from "../context/ToastContext";

// Friendly labels for the split FX Artha / DAGChain per-page modules.
const MODULE_LABELS = {
  fxartha: "FX Artha · Overview",
  "fxartha-traders": "FX Artha · Traders",
  "fxartha-lots": "FX Artha · Lots & Commission",
  dagchain: "DAGChain · Overview",
  "dagchain-users": "DAGChain · Users",
  "dagchain-nodes": "DAGChain · Nodes",
};

function Toggle({ on, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-9 h-5 rounded-full relative transition shrink-0 ${on ? "bg-brand-600" : "bg-ink-200"}`}
    >
      <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all ${on ? "left-4" : "left-0.5"}`} />
    </button>
  );
}

const ACTIONS = [
  ["can_view", "View"], ["can_create", "Create"], ["can_edit", "Edit"], ["can_delete", "Delete"],
];

function ModulePerms() {
  const toast = useToast();
  const [meta, setMeta] = useState(null);
  const [roles, setRoles] = useState([]);
  const [roleId, setRoleId] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([api.get("/access/meta/"), api.get("/roles/")]).then(([m, r]) => {
      setMeta(m.data);
      const rl = r.data.results || r.data;
      setRoles(rl);
      if (rl.length) setRoleId(String(rl[0].id));
    });
  }, []);

  useEffect(() => {
    if (!roleId) return;
    setLoading(true);
    api.get(`/module-permissions/?role=${roleId}`)
      .then(({ data }) => setRows(data.results || data))
      .finally(() => setLoading(false));
  }, [roleId]);

  const byModule = useMemo(() => Object.fromEntries(rows.map((r) => [r.module, r])), [rows]);

  const toggle = async (module, field) => {
    const row = byModule[module];
    if (row) {
      // existing row -> PATCH the single field
      const next = { ...row, [field]: !row[field] };
      setRows((rs) => rs.map((r) => (r.module === module ? next : r))); // optimistic
      try {
        await api.patch(`/module-permissions/${row.id}/`, { [field]: next[field] });
      } catch {
        setRows((rs) => rs.map((r) => (r.module === module ? row : r))); // revert
        toast.error("Update failed");
      }
    } else {
      // no row yet for this role+module -> CREATE it with the toggled field on
      const optimistic = {
        id: `tmp-${module}`, role: Number(roleId), module,
        can_view: false, can_create: false, can_edit: false, can_delete: false,
        [field]: true,
      };
      setRows((rs) => [...rs, optimistic]); // optimistic
      try {
        const { data } = await api.post("/module-permissions/", {
          role: Number(roleId), module, [field]: true,
        });
        setRows((rs) => rs.map((r) => (r.module === module ? data : r)));
      } catch {
        setRows((rs) => rs.filter((r) => r !== optimistic)); // revert
        toast.error("Update failed");
      }
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <label className="label !mb-0">Role</label>
        <select className="input max-w-xs" value={roleId} onChange={(e) => setRoleId(e.target.value)}>
          {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
        </select>
      </div>

      {loading || !meta ? (
        <Spinner />
      ) : (
        <div className="card p-5 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                <th className="pb-3 pr-4 font-semibold">Module</th>
                {ACTIONS.map(([, l]) => <th key={l} className="pb-3 px-4 font-semibold text-center">{l}</th>)}
              </tr>
            </thead>
            <tbody>
              {meta.modules.map((m) => (
                <tr key={m} className="border-t border-ink-100">
                  <td className={`py-3 pr-4 font-medium text-ink-700 ${MODULE_LABELS[m] ? "" : "capitalize"}`}>{MODULE_LABELS[m] || m.replace(/-/g, " ")}</td>
                  {ACTIONS.map(([field]) => (
                    <td key={field} className="py-3 px-4">
                      <div className="flex justify-center">
                        <Toggle on={!!byModule[m]?.[field]} onClick={() => toggle(m, field)} />
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function BusinessAccess() {
  const [users, setUsers] = useState([]);
  const [businesses, setBusinesses] = useState([]);
  const [userId, setUserId] = useState("");
  const [grants, setGrants] = useState([]); // UserPermission rows
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([api.get("/users/?page_size=200"), api.get("/businesses/?page_size=200")])
      .then(([u, b]) => {
        const ul = u.data.results || u.data;
        setUsers(ul);
        setBusinesses(b.data.results || b.data);
        if (ul.length) setUserId(String(ul[0].id));
      });
  }, []);

  const load = (uid) => {
    setLoading(true);
    api.get(`/user-permissions/?user=${uid}`)
      .then(({ data }) => setGrants(data.results || data))
      .finally(() => setLoading(false));
  };
  useEffect(() => { if (userId) load(userId); }, [userId]);

  const grantFor = (bizId) => grants.find((g) => g.business === bizId);
  const allAllowed = grants.length === 0; // no rows = sees all

  const toggle = async (bizId) => {
    const existing = grantFor(bizId);
    if (existing) {
      await api.delete(`/user-permissions/${existing.id}/`);
    } else {
      await api.post("/user-permissions/", {
        user: Number(userId), business: bizId,
        can_view: true, can_create: true, can_edit: true,
      });
    }
    load(userId);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <label className="label !mb-0">User</label>
        <select className="input max-w-xs" value={userId} onChange={(e) => setUserId(e.target.value)}>
          {users.map((u) => <option key={u.id} value={u.id}>{u.name} — {u.role_name}</option>)}
        </select>
      </div>

      {allAllowed && !loading && (
        <div className="text-sm text-amber-700 bg-amber-50 border border-amber-100 rounded-xl px-4 py-2">
          No business restriction — this user can currently see <b>all businesses</b>. Toggle one or more
          below to restrict them to only those.
        </div>
      )}

      {loading ? <Spinner /> : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {businesses.map((b) => {
            const on = !!grantFor(b.id);
            return (
              <button
                key={b.id}
                onClick={() => toggle(b.id)}
                className={`flex items-center gap-3 p-4 rounded-2xl border text-left transition
                  ${on ? "border-brand-300 bg-brand-50 dark:bg-brand-500/15 dark:border-brand-500/40" : "border-ink-200 bg-ink-0 hover:bg-ink-50"}`}
              >
                <div className={`grid place-items-center w-10 h-10 rounded-xl ${on ? "bg-brand-600 text-white" : "bg-ink-100 text-ink-400"}`}>
                  {on ? <Check size={18} /> : <Building2 size={18} />}
                </div>
                <div>
                  <p className="font-semibold text-ink-800">{b.name}</p>
                  <p className="text-xs text-ink-400">{on ? "Allowed" : allAllowed ? "Allowed (all)" : "Hidden"}</p>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function Permissions() {
  const [tab, setTab] = useState("modules");
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
          <ShieldCheck className="text-brand-600" /> Permission Matrix
        </h1>
        <p className="text-sm text-ink-400">Control role module access (Layer 3) and per-user business access (Layer 2)</p>
      </div>

      <div className="flex gap-1 p-1 bg-ink-100 rounded-xl w-fit">
        {[["modules", "Module Permissions"], ["business", "Business Access"]].map(([k, l]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition
              ${tab === k ? "bg-ink-0 text-brand-700 shadow-sm" : "text-ink-500 hover:text-ink-700"}`}
          >
            {l}
          </button>
        ))}
      </div>

      {tab === "modules" ? <ModulePerms /> : <BusinessAccess />}
    </div>
  );
}
