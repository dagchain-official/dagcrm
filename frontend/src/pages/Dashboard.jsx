import { useAuth } from "../context/AuthContext";
import AdminDashboard from "./AdminDashboard";
import UserDashboard from "./UserDashboard";
import HRDashboard from "./dashboards/HRDashboard";
import FinanceDashboard from "./dashboards/FinanceDashboard";
import TeamLeaderDashboard from "./dashboards/TeamLeaderDashboard";
import SalesManagerDashboard from "./dashboards/SalesManagerDashboard";
import SupportDashboard from "./dashboards/SupportDashboard";

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

export default function Dashboard() {
  const { user } = useAuth();
  const Component = MAP[user?.dashboard] || UserDashboard;
  return <Component />;
}
