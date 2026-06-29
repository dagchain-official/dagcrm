import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Reports from "./pages/Reports";
import PnL from "./pages/PnL";
import TargetBoard from "./pages/TargetBoard";
import AIAssistant from "./pages/AIAssistant";
import ResourceTable from "./pages/ResourceTable";
import Permissions from "./pages/Permissions";
import Integrations from "./pages/Integrations";
import Proposals from "./pages/Proposals";
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
        <Route path="ai" element={<AIAssistant />} />
        <Route path="reports" element={<Reports />} />
        <Route path="pnl" element={<PnL />} />
        <Route path="target-board" element={<TargetBoard />} />
        <Route path="permissions" element={<Permissions />} />
        <Route path="integrations" element={<Integrations />} />
        <Route path="proposals" element={<Proposals />} />
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
