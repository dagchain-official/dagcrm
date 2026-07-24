import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Boxes, ChevronRight, Users, Coins, Server, HardDrive, SlidersHorizontal } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
const num = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 4 });
const int = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });

function Stat({ icon: Icon, label, value, tint }) {
  return (
    <div className="card p-5">
      <div className={`grid place-items-center w-10 h-10 rounded-xl ${tint}`}><Icon size={18} /></div>
      <p className="text-2xl font-extrabold text-ink-900 mt-3 tabular-nums">{value}</p>
      <p className="text-xs text-ink-400 mt-0.5">{label}</p>
    </div>
  );
}

export default function DagChainByRm() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [employee, setEmployee] = useState("");
  const [employees, setEmployees] = useState([]);
  const [open, setOpen] = useState({});

  useEffect(() => {
    api.get("/employees/").then((r) => {
      const list = r.data?.results || r.data || [];
      setEmployees(list.map((e) => ({ id: e.id, name: e.user_name || e.name })));
    }).catch(() => setEmployees([]));
  }, []);

  usePolling(() => {
    const params = {};
    if (employee !== "") params.employee = employee;
    api.get("/reports/dagchain-rm/", { params })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load DAGChain RM report."));
  }, 8000, [employee]);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading DAGChain book…" />;

  const g = d.grand || {};
  const emps = d.employees || [];
  const toggle = (id) => setOpen((o) => ({ ...o, [id]: !o[id] }));

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
            <Boxes className="text-brand-600" /> DAGChain — Nodes &amp; Revenue
          </h1>
          <p className="text-sm text-ink-400">Each employee's assigned DAGChain users — nodes, node revenue, commission, rewards, DGC balance &amp; referrals</p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/commission-rules" className="chip !py-2 text-sm inline-flex items-center gap-1.5" title="Set commission per product + per-RM">
            <SlidersHorizontal size={14} /> Commission rules
          </Link>
          <select className="input !w-auto" value={employee} onChange={(e) => setEmployee(e.target.value)}>
            <option value="">All employees</option>
            {employees.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
          </select>
        </div>
      </div>

      {/* grand totals */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        <Stat icon={Users} label="Users" value={int(g.customers)} tint="bg-brand-100 text-brand-600" />
        <Stat icon={Server} label="Validator Nodes" value={int(g.validator_nodes)} tint="bg-violet-100 text-violet-600" />
        <Stat icon={HardDrive} label="Storage Nodes" value={int(g.storage_nodes)} tint="bg-indigo-100 text-indigo-600" />
        <Stat icon={Coins} label="Node Revenue" value={money(g.node_spend)} tint="bg-emerald-100 text-emerald-600" />
        <Stat icon={Coins} label="Commission" value={money(g.commission)} tint="bg-teal-100 text-teal-600" />
        <Stat icon={Coins} label="Staking Comm (DGC)" value={num(g.comm_staking)} tint="bg-amber-100 text-amber-600" />
      </div>

      {/* employee → users */}
      {emps.length === 0 && <EmptyState title="No DAGChain users" hint="Users appear here once DAGChain is synced and assigned to an RM." />}
      <div className="space-y-3">
        {emps.map((e) => (
          <div key={e.employee_id} className="card overflow-hidden">
            <button onClick={() => toggle(e.employee_id)}
              className="w-full flex items-center gap-3 p-4 hover:bg-ink-50/60 text-left">
              <ChevronRight size={18} className={`text-ink-400 transition-transform ${open[e.employee_id] ? "rotate-90" : ""}`} />
              <div className="flex-1 min-w-0">
                <p className="font-bold text-ink-900 truncate">{e.name}</p>
                <p className="text-xs text-ink-400">{e.customer_count} user{e.customer_count === 1 ? "" : "s"}</p>
              </div>
              <div className="hidden sm:flex items-center gap-6 text-right">
                <div><p className="text-[11px] text-ink-400 uppercase">Val / Sto</p><p className="font-bold text-violet-600 tabular-nums">{int(e.validator_nodes)}/{int(e.storage_nodes)}</p></div>
                <div><p className="text-[11px] text-ink-400 uppercase">Node Rev</p><p className="font-bold text-emerald-600 tabular-nums">{money(e.node_spend)}</p></div>
                <div><p className="text-[11px] text-ink-400 uppercase">Commission</p><p className="font-bold text-teal-600 tabular-nums">{money(e.commission)}</p></div>
                <div><p className="text-[11px] text-ink-400 uppercase">Stk Comm</p><p className="font-bold text-amber-600 tabular-nums">{num(e.comm_staking)}</p></div>
                <div><p className="text-[11px] text-ink-400 uppercase">Referrals</p><p className="font-bold text-ink-700 tabular-nums">{int(e.referrals)}</p></div>
              </div>
            </button>

            {open[e.employee_id] && (
              <div className="border-t border-ink-100 overflow-x-auto">
                <table className="w-full text-sm min-w-[1140px]">
                  <thead>
                    <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                      <th className="py-2.5 px-4 font-semibold">User</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Validator</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Storage</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Node Revenue</th>
                      <th className="py-2.5 px-4 font-semibold text-right" title="Validator node purchase × validator rate">Comm — Val</th>
                      <th className="py-2.5 px-4 font-semibold text-right" title="Storage node purchase × storage rate">Comm — Sto</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Commission</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Staked</th>
                      <th className="py-2.5 px-4 font-semibold text-right" title="Staked DGC × staking rate — paid in DGC">Stk Comm (DGC)</th>
                      <th className="py-2.5 px-4 font-semibold text-right">DGC Balance</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Referrals</th>
                    </tr>
                  </thead>
                  <tbody>
                    {e.customers.map((c) => (
                      <tr key={c.customer_id} className="border-t border-ink-100 hover:bg-ink-50/60">
                        <td className="py-2.5 px-4">
                          <Link to={`/dagchain-account/${c.customer_id}`} className="font-medium text-brand-700 hover:underline">{c.customer_name}</Link>
                        </td>
                        <td className="py-2.5 px-4 text-right tabular-nums text-violet-600">{int(c.validator_nodes)}</td>
                        <td className="py-2.5 px-4 text-right tabular-nums text-indigo-600">{int(c.storage_nodes)}</td>
                        <td className="py-2.5 px-4 text-right tabular-nums text-emerald-600">{money(c.node_spend)}</td>
                        <td className="py-2.5 px-4 text-right tabular-nums text-ink-500">{money(c.comm_validator)}</td>
                        <td className="py-2.5 px-4 text-right tabular-nums text-ink-500">{money(c.comm_storage)}</td>
                        <td className="py-2.5 px-4 text-right tabular-nums font-semibold text-teal-600">{money(c.commission)}</td>
                        <td className="py-2.5 px-4 text-right tabular-nums text-ink-500">{num(c.staked)}</td>
                        <td className="py-2.5 px-4 text-right tabular-nums font-semibold text-amber-600">{num(c.comm_staking)}</td>
                        <td className="py-2.5 px-4 text-right tabular-nums text-amber-600">{num(c.dgc_balance)}</td>
                        <td className="py-2.5 px-4 text-right tabular-nums text-ink-600">{int(c.referrals)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t-2 border-ink-200 bg-ink-50 font-bold text-ink-800">
                      <td className="py-2.5 px-4">Total</td>
                      <td className="py-2.5 px-4 text-right tabular-nums">{int(e.validator_nodes)}</td>
                      <td className="py-2.5 px-4 text-right tabular-nums">{int(e.storage_nodes)}</td>
                      <td className="py-2.5 px-4 text-right tabular-nums">{money(e.node_spend)}</td>
                      <td className="py-2.5 px-4 text-right tabular-nums">{money(e.comm_validator)}</td>
                      <td className="py-2.5 px-4 text-right tabular-nums">{money(e.comm_storage)}</td>
                      <td className="py-2.5 px-4 text-right tabular-nums text-teal-700">{money(e.commission)}</td>
                      <td className="py-2.5 px-4 text-right tabular-nums">{num(e.staked)}</td>
                      <td className="py-2.5 px-4 text-right tabular-nums text-amber-700">{num(e.comm_staking)}</td>
                      <td className="py-2.5 px-4 text-right tabular-nums">{num(e.dgc_balance)}</td>
                      <td className="py-2.5 px-4 text-right tabular-nums">{int(e.referrals)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
