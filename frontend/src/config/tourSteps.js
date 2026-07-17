// Product-tour content. One entry per sidebar item we walk through. `route`
// matches the NavLink `to` (and its data-tour attribute); the tour only shows
// entries whose element is actually on the page — i.e. modules this user can see.
// `inPage` (optional) = steps that highlight controls INSIDE the module's page.
// Keep the copy short: what the module is + what you do there.

export const TOUR = [
  // ---- Overview ----
  {
    route: "/",
    label: "Dashboard",
    content:
      "This is your home base — an overview of leads, customers, revenue and pipeline. Each role sees a dashboard tailored to them.",
  },
  {
    route: "/attendance-clock",
    label: "My Attendance",
    content: "Clock in and out, and review your own attendance record.",
  },
  {
    route: "/leaves-mine",
    label: "My Leaves",
    content: "Apply for leave and track its approval status.",
  },
  {
    route: "/ai",
    label: "AI Assistant",
    content:
      "Ask questions about your CRM data directly — 'How many leads came in this month?', 'Who's the top RM?' — and get answers in real time.",
  },

  // ---- Sales & CRM ----
  {
    route: "/m/leads",
    label: "Leads",
    content:
      "New leads land here (WhatsApp / Google / manual). Add, search/filter, assign an RM, import from CSV — all in one place. Click any lead to see its full history.",
  },
  {
    route: "/m/lead-activities",
    label: "Lead Activities",
    content:
      "Every call, meeting, email and note logged against your leads — with follow-up dates so nothing slips.",
  },
  {
    route: "/m/opportunities",
    label: "Opportunities",
    content:
      "Leads that have turned into deals. Track the stage (proposal → negotiation → won) and expected revenue here.",
  },
  {
    route: "/proposals",
    label: "Proposals",
    content:
      "Build a quotation/proposal — line items, tax/discount, and a PDF. Once accepted, the customer and revenue are created automatically.",
  },
  {
    route: "/m/customers",
    label: "Customers",
    content:
      "Your own (converted) customer book. Click any customer to open Customer 360 — full details plus RM reassignment.",
  },
  {
    route: "/m/communications",
    label: "Communications",
    content:
      "Every message exchanged with customers — WhatsApp, email, SMS — inbound and outbound.",
  },
  {
    route: "/targets",
    label: "Targets",
    content:
      "Set and track the revenue target for each RM/team. Target = CTC × multiplier (configured in HR → Rules).",
  },
  {
    route: "/team-requests",
    label: "Team Requests",
    content:
      "Managers request team members; the approval flows up the management chain.",
  },
  {
    route: "/kpi",
    label: "KPI & Performance",
    content:
      "Each employee's KPIs (calls, meetings, lots…) and performance score. Everything is admin-configurable — nothing is hardcoded.",
  },
  {
    route: "/traders-lots",
    label: "Traders & Lots",
    content:
      "Per-employee lots traded and the commission earned from them.",
  },
  {
    route: "/m/revenues",
    label: "Revenue",
    content:
      "Every revenue record — gross, commission and net — by customer and business.",
  },

  // ---- Support ----
  {
    route: "/m/tickets",
    label: "Support Desk",
    content:
      "Customer support tickets — priority, status, assignment and comment threads.",
  },

  // ---- HR & People ----
  {
    route: "/hr/people",
    label: "HR — People",
    content:
      "Employees, departments and the org hierarchy. All HR tools live in this group.",
  },
  {
    route: "/recruitment",
    label: "Recruitment",
    content:
      "Post jobs, collect applications via a public link, and auto-score resumes against the required skills.",
  },
  {
    route: "/hr/attendance",
    label: "Attendance & Leave",
    content: "Team attendance and leave approvals (HR view).",
  },
  {
    route: "/hr/costs",
    label: "Cost & CTC",
    content:
      "Configure cost categories and per-employee costs that build each employee's CTC.",
  },
  {
    route: "/hr/payroll",
    label: "Payroll & Incentives",
    content:
      "Monthly payroll — basic, incentive, bonus, deductions — plus incentive payouts.",
  },
  {
    route: "/hr/rules",
    label: "Rules & Config",
    content:
      "Incentive slabs, activity incentives, target multipliers, performance weights and the formula builder — all configurable, no code.",
  },

  // ---- Finance ----
  {
    route: "/finance",
    label: "Finance (P&L)",
    content:
      "The business P&L — revenue vs expenses vs commissions. AUM and Contribution are in this Finance group too.",
  },
  {
    route: "/aum",
    label: "AUM",
    content:
      "Assets under management — deposits and withdrawals that drive Net New AUM.",
  },
  {
    route: "/contribution",
    label: "Contribution",
    content:
      "Each client's business-contribution components — brokerage, insurance, staking and more.",
  },

  // ---- FX Artha ----
  {
    route: "/fxartha",
    label: "FX Artha",
    content:
      "Live data from the FX Artha trading platform — traders, deposits, lots and revenue.",
  },
  {
    route: "/fxartha-traders",
    label: "FX Artha Traders",
    content:
      "Every trader's detail — lots, brokerage, deposits, RM. Click a trader to open their live account (positions, trades, ledger).",
  },

  // ---- DAGChain ----
  {
    route: "/dagchain",
    label: "DAGChain",
    content:
      "Live data from the DAGChain platform — users, wallet/DGC balance, validator & storage nodes, and node-purchase revenue.",
  },
  {
    route: "/dagchain-users",
    label: "DAGChain Users",
    content:
      "All DAGChain platform users — wallet, DGC balance, referrals, KYC and node counts.",
  },
  {
    route: "/dagchain-nodes",
    label: "DAGChain Nodes",
    content:
      "Validator and storage nodes with their rewards and blocks validated.",
  },

  // ---- Administration ----
  {
    route: "/m/users",
    label: "Users",
    content: "Create and manage user accounts, their roles and managers.",
  },
  {
    route: "/m/roles",
    label: "Roles",
    content: "The roles that define each user's access level.",
  },
  {
    route: "/m/teams",
    label: "Teams",
    content: "Sales teams and their members.",
  },
  {
    route: "/permissions",
    label: "Permission Matrix",
    content:
      "Which role can view/edit which module (Layer 3), and which user can see which business's data (Layer 2) — all controlled here.",
  },
  {
    route: "/config",
    label: "Configuration",
    content:
      "Businesses, products, lead sources and the rest of the setup — add new items from here.",
  },
  {
    route: "/integrations",
    label: "Integration Hub",
    content:
      "Connect every platform (Meta / Google / WhatsApp / FX Artha / DAGChain) from here. Add the webhook URL on that platform and leads/data flow straight into the CRM.",
  },
  {
    route: "/reports",
    label: "Reports",
    content: "Cross-business analytics and detailed reports.",
  },
];

// ---------------------------------------------------------------------------
// Per-page feature tours — opened by the "?" (Help) button on each page. These
// are self-contained (every step is on the current page) and end with a pointer
// to a sensible next page. Add a page here (or extend the generic resource tour)
// to give any screen its own walkthrough.
// ---------------------------------------------------------------------------

// Generic tour for any list screen (/m/*), driven by ResourceTable's toolbar.
const RESOURCE_STEPS = [
  { selector: '[data-tour="rt-search"]', title: "Search", content: "Search this list by name, email, phone or code." },
  { selector: '[data-tour="rt-new"]', title: "Add a record", content: "Create a new entry here — or use Import to bring many in from a CSV." },
  { selector: '[data-tour="rt-export"]', title: "Export", content: "Download exactly what you're viewing as CSV or PDF." },
];

// "What's next" suggestion shown as the final step of a page tour.
const NEXT = {
  "/m/leads": { label: "Opportunities", route: "/m/opportunities" },
  "/m/opportunities": { label: "Proposals", route: "/proposals" },
  "/m/customers": { label: "Communications", route: "/m/communications" },
  "/m/revenues": { label: "Finance (P&L)", route: "/finance" },
  "/m/tickets": { label: "Customers", route: "/m/customers" },
};

// Returns { steps, next } for a page, or null if that page has no tour yet.
export function pageTour(pathname) {
  let steps = null;
  if (pathname.startsWith("/m/")) steps = RESOURCE_STEPS;
  // (custom page tours can be registered here by exact route)
  if (!steps || !steps.length) return null;
  return { steps, next: NEXT[pathname] || null };
}

