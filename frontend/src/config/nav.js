import {
  LayoutDashboard, Users, Shield, UsersRound, Building2, Package,
  Radio, UserPlus, Activity, Target, Briefcase, UserCheck, MessageSquare,
  Crosshair, DollarSign, LifeBuoy, Clock, CalendarOff, Wallet, Award,
  Receipt, Handshake, BarChart3, Sparkles, Settings2, ShieldCheck, Plug, FileText,
  TrendingUp, Gauge, BarChart4, ListPlus, Trophy, Coins, Layers,
} from "lucide-react";

// Derive the permission module key from a nav `to` path.
// null = always visible (dashboard, AI assistant).
export const moduleOf = (to) => {
  if (to === "/" || to === "/ai") return null;
  if (["/reports", "/pnl", "/target-board", "/kpi-board", "/performance", "/incentive-board"].includes(to)) return "reports";
  if (to === "/permissions" || to === "/integrations") return "__admin__";
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
      { to: "/m/targets", label: "Targets", icon: Crosshair },
      { to: "/target-board", label: "Target Board", icon: Gauge },
      { to: "/kpi-board", label: "KPI Board", icon: BarChart4 },
      { to: "/m/metric-entries", label: "KPI Entries", icon: ListPlus },
      { to: "/performance", label: "Performance", icon: Trophy },
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
      { to: "/m/employees", label: "Employees", icon: Briefcase },
      { to: "/m/hierarchy-levels", label: "Hierarchy Levels", icon: UsersRound },
      { to: "/m/cost-categories", label: "Cost Categories", icon: Receipt },
      { to: "/m/employee-costs", label: "Employee Costs", icon: Wallet },
      { to: "/m/departments", label: "Departments", icon: Building2 },
      { to: "/m/attendance", label: "Attendance", icon: Clock },
      { to: "/m/employee-activities", label: "Activity Tracking", icon: Activity },
      { to: "/m/leaves", label: "Leaves", icon: CalendarOff },
      { to: "/m/leave-types", label: "Leave Types", icon: Settings2 },
      { to: "/m/payrolls", label: "Payroll", icon: Wallet },
      { to: "/m/incentives", label: "Incentives", icon: Award },
      { to: "/incentive-board", label: "Incentive Board", icon: Coins },
      { to: "/m/incentive-slabs", label: "Incentive Slabs", icon: Layers },
      { to: "/m/activity-incentives", label: "Activity Incentives", icon: Coins },
      { to: "/m/incentive-rules", label: "Incentive Rules", icon: Settings2 },
      { to: "/m/target-multipliers", label: "Target Multipliers", icon: Gauge },
      { to: "/m/performance-weights", label: "Performance Weights", icon: Trophy },
    ],
  },
  {
    group: "Finance",
    items: [
      { to: "/m/expenses", label: "Expenses", icon: Receipt },
      { to: "/m/commissions", label: "Commissions", icon: Handshake },
      { to: "/pnl", label: "P&L Statement", icon: TrendingUp },
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
