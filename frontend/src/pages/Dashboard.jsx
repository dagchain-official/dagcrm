import { useEffect, useState } from "react";
import { Building2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";
import AdminDashboard from "./AdminDashboard";
import UserDashboard from "./UserDashboard";
import HRDashboard from "./dashboards/HRDashboard";
import FinanceDashboard from "./dashboards/FinanceDashboard";
import TeamLeaderDashboard from "./dashboards/TeamLeaderDashboard";
import SalesManagerDashboard from "./dashboards/SalesManagerDashboard";
import SupportDashboard from "./dashboards/SupportDashboard";
import BusinessDashboard from "./BusinessDashboard";

// Layer 1 — each role lands on its own dashboard (driven by user.dashboard).
const MAP = {
  admin: AdminDashboard,
  "sales-exec": UserDashboard,
  "sales-manager": SalesManagerDashboard,
  "team-leader": TeamLeaderDashboard,
  hr: HRDashboard,
  finance: FinanceDashboard,
  support: SupportDashboard,
};

// Roles that get the per-business switcher (management overview).
const SWITCHER_ROLES = ["admin", "sales-manager", "team-leader", "finance"];

export default function Dashboard() {
  const { user } = useAuth();
  const RoleDash = MAP[user?.dashboard] || UserDashboard;
  const [businesses, setBusinesses] = useState([]);
  const [biz, setBiz] = useState("");

  const canSwitch = SWITCHER_ROLES.includes(user?.dashboard);
  useEffect(() => {
    if (!canSwitch) return;
    // fetch live so the list always reflects current businesses (no stale cache)
    api.get("/businesses/")
      .then(({ data }) => setBusinesses(data.results || data))
      .catch(() => setBusinesses([]));
  }, [canSwitch]);

  const showSwitcher = canSwitch && businesses.length > 0;
  if (!showSwitcher) return <RoleDash />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <p className="text-xs text-ink-400 flex items-center gap-1.5">
          <Building2 size={14} /> View a single business unit, or keep the overall CRM view.
        </p>
        <select className="input !w-auto min-w-[190px]" value={biz} onChange={(e) => setBiz(e.target.value)}>
          <option value="">All Businesses (CRM overview)</option>
          {businesses.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
      </div>
      {biz ? <BusinessDashboard businessId={biz} /> : <RoleDash />}
    </div>
  );
}
