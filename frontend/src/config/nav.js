import {
  LayoutDashboard, Users, Shield, UsersRound, Building2, Package,
  Radio, UserPlus, Activity, Target, Briefcase, UserCheck, MessageSquare,
  Crosshair, DollarSign, LifeBuoy, Clock, CalendarOff, Wallet, Award,
  Receipt, Handshake, BarChart3, Sparkles, Settings2, ShieldCheck, Plug, FileText,
  TrendingUp, Gauge, BarChart4, ListPlus, Trophy, Coins, Layers, Wand2, Calculator,
  Landmark, PiggyBank, Scale, CandlestickChart, LineChart, Boxes, Server, Network,
} from "lucide-react";

// Derive the permission module key from a nav `to` path.
// null = always visible (dashboard, AI assistant).
export const moduleOf = (to) => {
  if (to === "/" || to === "/ai") return null;
  if (["/reports", "/pnl", "/target-board", "/kpi-board", "/kpi", "/performance", "/incentive-board"].includes(to)) return "reports";
  // FX Artha & DAGChain: each sub-page has its own permission module so access
  // can be granted/denied per page (Overview / Traders / Lots, Users / Nodes…).
  if (to === "/fxartha") return "fxartha";                                   // Overview
  if (to === "/fxartha-traders" || to.startsWith("/fxartha-account")) return "fxartha-traders";
  if (to === "/traders-lots") return "fxartha-lots";                         // Lots & Commission
  if (to === "/dagchain") return "dagchain";                                 // Overview
  if (to === "/dagchain-users" || to.startsWith("/dagchain-account") || to === "/dagchain-rm") return "dagchain-users";
  if (to === "/dagchain-nodes") return "dagchain-nodes";
  if (to === "/permissions" || to === "/integrations") return "__admin__";
  if (to === "/formula-builder") return "formula-rules";
  if (to === "/formula-board" || to === "/aum-board" || to === "/contribution-board") return "reports";
  if (to === "/targets" || to === "/assign-target") return "targets";
  if (to === "/team-requests") return "teams";
  if (to === "/hr/people") return "employees";
  if (to === "/hr/hierarchy") return "employees";
  if (to === "/recruitment") return "employees";
  if (to === "/hr/attendance") return "attendance";
  if (to === "/hr/costs") return "cost-categories";
  if (to === "/hr/payroll") return "payrolls";
  if (to === "/hr/rules") return "formula-rules";
  if (to === "/finance") return "reports";
  if (to === "/aum") return "aum-entries";
  if (to === "/contribution") return "contribution-entries";
  if (to === "/config") return "businesses";
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
    group: "FX Artha",
    items: [
      { to: "/fxartha", label: "Overview", icon: LineChart },
      { to: "/fxartha-traders", label: "Traders", icon: Users },
      { to: "/traders-lots", label: "Lots & Commission", icon: CandlestickChart },
    ],
  },
  {
    group: "DAGChain",
    items: [
      { to: "/dagchain", label: "Overview", icon: Boxes },
      { to: "/dagchain-users", label: "Users", icon: Users },
      { to: "/dagchain-nodes", label: "Nodes", icon: Server },
      { to: "/dagchain-rm", label: "Nodes & Revenue", icon: Coins },
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
      { to: "/hr/hierarchy", label: "Org Hierarchy", icon: Network },
      { to: "/recruitment", label: "Recruitment", icon: UserPlus },
      { to: "/hr/attendance", label: "Attendance & Leave", icon: Clock },
      { to: "/hr/costs", label: "Cost & CTC", icon: Wallet },
      { to: "/hr/payroll", label: "Payroll & Incentives", icon: Award },
      { to: "/hr/rules", label: "Rules & Config", icon: Wand2 },
    ],
  },
  {
    group: "Finance",
    items: [
      { to: "/finance", label: "Finance (P&L)", icon: TrendingUp },
      { to: "/aum", label: "AUM", icon: Landmark },
      { to: "/contribution", label: "Contribution", icon: Scale },
    ],
  },
  {
    group: "Administration",
    items: [
      { to: "/m/users", label: "Users", icon: Users },
      { to: "/m/roles", label: "Roles", icon: Shield },
      { to: "/m/teams", label: "Teams", icon: UsersRound },
      { to: "/permissions", label: "Permission Matrix", icon: ShieldCheck },
      { to: "/config", label: "Configuration", icon: Settings2 },
      { to: "/integrations", label: "Integration Hub", icon: Plug },
      { to: "/reports", label: "Reports", icon: BarChart3 },
    ],
  },
];
