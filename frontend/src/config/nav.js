import {
  LayoutDashboard, Users, Shield, UsersRound, Building2, Package,
  Radio, UserPlus, Activity, Target, Briefcase, UserCheck, MessageSquare,
  Crosshair, DollarSign, LifeBuoy, Clock, CalendarOff, Wallet, Award,
  Receipt, Handshake, BarChart3, Sparkles, Settings2, ShieldCheck, Plug, FileText,
  TrendingUp, Gauge, BarChart4, ListPlus, Trophy, Coins, Layers, Wand2, Calculator,
  Landmark, PiggyBank, Scale,
} from "lucide-react";

// Derive the permission module key from a nav `to` path.
// null = always visible (dashboard, AI assistant).
export const moduleOf = (to) => {
  if (to === "/" || to === "/ai") return null;
  if (["/reports", "/pnl", "/target-board", "/kpi-board", "/kpi", "/performance", "/incentive-board"].includes(to)) return "reports";
  if (to === "/permissions" || to === "/integrations") return "__admin__";
  if (to === "/formula-builder") return "formula-rules";
  if (to === "/formula-board" || to === "/aum-board" || to === "/contribution-board") return "reports";
  if (to === "/targets" || to === "/assign-target") return "targets";
  if (to === "/team-requests") return "teams";
  if (to === "/hr/people") return "employees";
  if (to === "/hr/attendance") return "attendance";
  if (to === "/hr/costs") return "cost-categories";
  if (to === "/hr/payroll") return "payrolls";
  if (to === "/hr/rules") return "formula-rules";
  if (to === "/proposals") return "proposals";
  if (to.startsWith("/m/")) return to.slice(3);
  return null;
};

// group -> items. `to` matches a key in RESOURCES (or a custom route).
export const NAV = [
  {
    group: "Overview",
    items: [
      { to: "/", label: "Dashboard", icon: LayoutDashboard, exact: true },
      { to: "/attendance-clock", label: "My Attendance", icon: Clock, hideForSuper: true },
      { to: "/leaves-mine", label: "My Leaves", icon: CalendarOff, hideForSuper: true },
      { to: "/ai", label: "AI Assistant", icon: Sparkles },
    ],
  },
  {
    group: "Sales & CRM",
    items: [
      { to: "/m/leads", label: "Leads", icon: UserPlus },
      { to: "/m/lead-activities", label: "Lead Activities", icon: Activity },
      { to: "/m/opportunities", label: "Opportunities", icon: Target },
      { to: "/proposals", label: "Proposals", icon: FileText },
      { to: "/m/customers", label: "Customers", icon: UserCheck },
      { to: "/m/communications", label: "Communications", icon: MessageSquare },
      { to: "/targets", label: "Targets", icon: Crosshair },
      { to: "/team-requests", label: "Team Requests", icon: UserPlus },
      { to: "/kpi", label: "KPI & Performance", icon: BarChart4 },
      { to: "/m/revenues", label: "Revenue", icon: DollarSign },
    ],
  },
  {
    group: "Setup",
    items: [
      { to: "/m/businesses", label: "Businesses", icon: Building2 },
      { to: "/m/products", label: "Products", icon: Package },
      { to: "/m/metric-definitions", label: "KPI Definitions", icon: BarChart4 },
      { to: "/m/lead-sources", label: "Lead Sources", icon: Radio },
    ],
  },
  {
    group: "Support",
    items: [{ to: "/m/tickets", label: "Support Desk", icon: LifeBuoy }],
  },
  {
    group: "HR & People",
    items: [
      { to: "/hr/people", label: "People", icon: Briefcase },
      { to: "/hr/attendance", label: "Attendance & Leave", icon: Clock },
      { to: "/hr/costs", label: "Cost & CTC", icon: Wallet },
      { to: "/hr/payroll", label: "Payroll & Incentives", icon: Award },
      { to: "/hr/rules", label: "Rules & Config", icon: Wand2 },
    ],
  },
  {
    group: "Finance",
    items: [
      { to: "/m/expenses", label: "Expenses", icon: Receipt },
      { to: "/m/commissions", label: "Commissions", icon: Handshake },
      { to: "/pnl", label: "P&L Statement", icon: TrendingUp },
      { to: "/aum-board", label: "AUM Board", icon: Landmark },
      { to: "/m/aum-entries", label: "AUM Entries", icon: PiggyBank },
      { to: "/contribution-board", label: "Contribution", icon: Scale },
      { to: "/m/contribution-entries", label: "Contribution Entries", icon: Coins },
      { to: "/m/contribution-weights", label: "Contribution Formula", icon: Settings2 },
    ],
  },
  {
    group: "Administration",
    items: [
      { to: "/m/users", label: "Users", icon: Users },
      { to: "/m/roles", label: "Roles", icon: Shield },
      { to: "/m/teams", label: "Teams", icon: UsersRound },
      { to: "/permissions", label: "Permission Matrix", icon: ShieldCheck },
      { to: "/integrations", label: "Integration Hub", icon: Plug },
      { to: "/reports", label: "Reports", icon: BarChart3 },
    ],
  },
];
