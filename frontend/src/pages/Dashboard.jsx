import { useEffect, useState } from "react";
import { Building2, UserRound } from "lucide-react";
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
// Roles that may drill into any one employee's dashboard.
const EMPLOYEE_VIEW_ROLES = ["admin", "sales-manager", "team-leader"];
// An employee's RBAC role -> which dashboard they'd normally land on, so picking
// an HR person shows the HR dashboard, Finance shows Finance, etc.
const ROLE_TO_DASH = {
  "Super Admin": "admin", "Business Head": "admin", "Sales Director": "admin",
  "Sales Manager": "sales-manager", "Team Leader": "team-leader",
  "Sales Executive": "sales-exec", "Support": "support", "HR": "hr", "Finance": "finance",
};

export default function Dashboard() {
  const { user } = useAuth();
  const RoleDash = MAP[user?.dashboard] || UserDashboard;
  const [businesses, setBusinesses] = useState([]);
  const [biz, setBiz] = useState("");
  const [people, setPeople] = useState([]);
  const [emp, setEmp] = useState("");            // selected user id (employee dashboard)

  const canSwitch = SWITCHER_ROLES.includes(user?.dashboard);
  const canViewEmployee = EMPLOYEE_VIEW_ROLES.includes(user?.dashboard);
  useEffect(() => {
    if (canSwitch) {
      api.get("/businesses/")
        .then(({ data }) => setBusinesses(data.results || data))
        .catch(() => setBusinesses([]));
    }
    if (canViewEmployee) {
      // id + name + employee id so the picker reads like the Excel monitor
      api.get("/users/?page_size=500")
        .then(({ data }) => setPeople((data.results || data).filter((u) => !u.is_superuser)))
        .catch(() => setPeople([]));
    }
  }, [canSwitch, canViewEmployee]);

  const showBiz = canSwitch && businesses.length > 0;
  const showEmp = canViewEmployee && people.length > 0;
  if (!showBiz && !showEmp) return <RoleDash />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-end gap-2 flex-wrap">
        {showBiz && (
          <div className="flex items-center gap-1.5 flex-1 lg:flex-none min-w-0">
            <Building2 size={14} className="text-ink-400 shrink-0" />
            <select className="input !w-full lg:!w-auto min-w-0 lg:min-w-[180px]" value={biz}
              onChange={(e) => { setBiz(e.target.value); setEmp(""); }}>
              <option value="">All Businesses (overview)</option>
              {businesses.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </div>
        )}
        {showEmp && (
          <div className="flex items-center gap-1.5 flex-1 lg:flex-none min-w-0">
            <UserRound size={14} className="text-ink-400 shrink-0" />
            <select className="input !w-full lg:!w-auto min-w-0 lg:min-w-[210px]" value={emp}
              onChange={(e) => { setEmp(e.target.value); setBiz(""); }}>
              <option value="">— Select an employee —</option>
              {people.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.employee_id ? `${u.employee_id} · ` : ""}{u.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
      {emp ? <EmployeeDash userId={emp} person={people.find((u) => String(u.id) === String(emp))} />
        : biz ? <BusinessDashboard businessId={biz} />
          : <RoleDash />}
    </div>
  );
}

// Render the selected employee's role-appropriate dashboard. Sales-exec is
// personal and Team Leader is that leader's team (both scoped by ?user=); the
// company views (HR / Finance / Admin / Sales Manager / Support) render as-is.
function EmployeeDash({ userId, person }) {
  const key = ROLE_TO_DASH[person?.role_name] || "sales-exec";
  if (key === "sales-exec") return <UserDashboard userId={userId} />;
  if (key === "team-leader") return <TeamLeaderDashboard userId={userId} />;
  const Comp = MAP[key] || UserDashboard;
  return <Comp />;
}
