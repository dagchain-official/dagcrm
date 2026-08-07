import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Reports from "./pages/Reports";
import EmployeeReport from "./pages/EmployeeReport";
import ProductReport from "./pages/ProductReport";
import PnL from "./pages/PnL";
import TargetBoard from "./pages/TargetBoard";
import AssignTarget from "./pages/AssignTarget";
import TeamRequests from "./pages/TeamRequests";
import TargetsHub from "./pages/TargetsHub";
import KpiHub from "./pages/KpiHub";
import { PeopleHub, AttendanceHub, CostHub, PayrollHub, RulesHub } from "./pages/HrHubs";
import EmployeeProfile from "./pages/EmployeeProfile";
import HrRequests from "./pages/HrRequests";
import HierarchyTree from "./pages/HierarchyTree";
import { FinanceHub, AumHub, ContributionHub } from "./pages/FinanceHubs";
import ConfigHub from "./pages/ConfigHub";
import TrainingHub from "./pages/TrainingHub";
import TrainingModuleDetail from "./pages/TrainingModuleDetail";
import KpiBoard from "./pages/KpiBoard";
import TradersLots from "./pages/TradersLots";
import CommissionRules from "./pages/CommissionRules";
import Settings from "./pages/Settings";
import FxArthaTraders from "./pages/FxArthaTraders";
import FxArthaOverview from "./pages/FxArthaOverview";
import FxArthaAccount from "./pages/FxArthaAccount";
import DagChainOverview from "./pages/DagChainOverview";
import DagChainUsers from "./pages/DagChainUsers";
import DagChainAccount from "./pages/DagChainAccount";
import DagChainByRm from "./pages/DagChainByRm";
import DagChainNodes from "./pages/DagChainNodes";
import Recruitment from "./pages/Recruitment";
import ApplyPage from "./pages/ApplyPage";
import Performance from "./pages/Performance";
import IncentiveBoard from "./pages/IncentiveBoard";
import FormulaBuilder from "./pages/FormulaBuilder";
import FormulaBoard from "./pages/FormulaBoard";
import AumBoard from "./pages/AumBoard";
import ContributionBoard from "./pages/ContributionBoard";
import AIAssistant from "./pages/AIAssistant";
import ResourceTable from "./pages/ResourceTable";
import Permissions from "./pages/Permissions";
import Integrations from "./pages/Integrations";
import Customer360 from "./pages/Customer360";
import LeadDetail from "./pages/LeadDetail";
import TicketDetail from "./pages/TicketDetail";
import MyAttendance from "./pages/MyAttendance";
import MyLeaves from "./pages/MyLeaves";
import ProfileSettings from "./pages/ProfileSettings";
import ResetPassword from "./pages/ResetPassword";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading)
    return (
      <div className="h-screen grid place-items-center text-ink-400">
        <span className="w-6 h-6 border-2 border-ink-300 border-t-brand-600 rounded-full animate-spin" />
      </div>
    );
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/apply/:token" element={<ApplyPage />} />
      <Route
        path="/"
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="attendance-clock" element={<MyAttendance />} />
        <Route path="leaves-mine" element={<MyLeaves />} />
        <Route path="hr-requests" element={<HrRequests />} />
        <Route path="ai" element={<AIAssistant />} />
        <Route path="reports" element={<Reports />} />
        <Route path="employee-report" element={<EmployeeReport />} />
        <Route path="product-report" element={<ProductReport />} />
        <Route path="pnl" element={<PnL />} />
        <Route path="target-board" element={<TargetBoard />} />
        <Route path="assign-target" element={<AssignTarget />} />
        <Route path="team-requests" element={<TeamRequests />} />
        <Route path="targets" element={<TargetsHub />} />
        <Route path="kpi" element={<KpiHub />} />
        <Route path="hr/people" element={<PeopleHub />} />
        <Route path="hr/employee/:id" element={<EmployeeProfile />} />
        <Route path="hr/training" element={<TrainingHub />} />
        <Route path="hr/training/module/:id" element={<TrainingModuleDetail />} />
        <Route path="hr/hierarchy" element={<HierarchyTree />} />
        <Route path="hr/attendance" element={<AttendanceHub />} />
        <Route path="hr/costs" element={<CostHub />} />
        <Route path="hr/payroll" element={<PayrollHub />} />
        <Route path="hr/rules" element={<RulesHub />} />
        <Route path="recruitment" element={<Recruitment />} />
        <Route path="finance" element={<FinanceHub />} />
        <Route path="aum" element={<AumHub />} />
        <Route path="contribution" element={<ContributionHub />} />
        <Route path="config" element={<ConfigHub />} />
        <Route path="kpi-board" element={<KpiBoard />} />
        <Route path="traders-lots" element={<TradersLots />} />
        <Route path="fxartha" element={<FxArthaOverview />} />
        <Route path="fxartha-traders" element={<FxArthaTraders />} />
        <Route path="fxartha-account/:id" element={<FxArthaAccount />} />
        <Route path="dagchain" element={<DagChainOverview />} />
        <Route path="dagchain-users" element={<DagChainUsers />} />
        <Route path="dagchain-account/:id" element={<DagChainAccount />} />
        <Route path="dagchain-nodes" element={<DagChainNodes />} />
        <Route path="dagchain-rm" element={<DagChainByRm />} />
        <Route path="commission-rules" element={<CommissionRules />} />
        <Route path="settings" element={<Settings />} />
        <Route path="performance" element={<Performance />} />
        <Route path="incentive-board" element={<IncentiveBoard />} />
        <Route path="formula-builder" element={<FormulaBuilder />} />
        <Route path="formula-board" element={<FormulaBoard />} />
        <Route path="aum-board" element={<AumBoard />} />
        <Route path="contribution-board" element={<ContributionBoard />} />
        <Route path="permissions" element={<Permissions />} />
        <Route path="integrations" element={<Integrations />} />
        <Route path="profile" element={<ProfileSettings />} />
        <Route path="customers/:id" element={<Customer360 />} />
        <Route path="leads/:id" element={<LeadDetail />} />
        <Route path="tickets/:id" element={<TicketDetail />} />
        <Route path="m/:resource" element={<ResourceTable />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
