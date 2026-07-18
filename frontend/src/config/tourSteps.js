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

// "What's next" suggestion shown as the final step of a page tour. Used for the
// generic /m/* list screens; custom pages carry their own `next` in PAGE_TOURS.
const NEXT = {
  "/m/leads": { label: "Opportunities", route: "/m/opportunities" },
  "/m/opportunities": { label: "Proposals", route: "/proposals" },
  "/m/customers": { label: "Communications", route: "/m/communications" },
  "/m/revenues": { label: "Finance (P&L)", route: "/finance" },
  "/m/tickets": { label: "Customers", route: "/m/customers" },
};

// Feature tours for individual custom pages, keyed by exact route. Each entry is
// { steps: [{ selector, title, content }], next: { label, route } | null }. Every
// selector must match a data-tour attribute rendered on that page.
const PAGE_TOURS = {
  // Admin / business-head dashboard at "/"
  "/": {
    steps: [
      { selector: '[data-tour="dash-kpis"]', title: "Your headline numbers", content: "Leads, customers, open opportunities and support tickets — the health of the business at a glance." },
      { selector: '[data-tour="dash-revenue"]', title: "Revenue trend", content: "Net revenue with its month-by-month trend, so you can see momentum over time." },
      { selector: '[data-tour="dash-recent-revenue"]', title: "Recent revenue", content: "The latest revenue records — customer, business and net value." },
      { selector: '[data-tour="dash-ai"]', title: "AI insights", content: "Automatically generated observations about what's changing in your numbers." },
    ],
    next: { label: "Leads", route: "/m/leads" },
  },

  // FX Artha — Overview
  "/fxartha": {
    steps: [
      { selector: '[data-tour="fxo-tiles"]', title: "Platform snapshot", content: "Traders, active accounts, lots, deposits, withdrawals and revenue from the last FX Artha sync." },
      { selector: '[data-tour="fxo-revenue"]', title: "Revenue", content: "FX Artha's own authoritative revenue figures — commission and swap for today, this week, this month and all time." },
      { selector: '[data-tour="fxo-chart"]', title: "Revenue by month", content: "Brokerage (commission + swap) plotted month by month." },
      { selector: '[data-tour="fxo-traders"]', title: "All Traders", content: "Open the full trader list — lots, brokerage, deposits and assigned RM." },
    ],
    next: { label: "FX Artha Traders", route: "/fxartha-traders" },
  },

  // FX Artha — Traders list
  "/fxartha-traders": {
    steps: [
      { selector: '[data-tour="fxt-search"]', title: "Search traders", content: "Find any trader by name or email." },
      { selector: '[data-tour="fxt-dates"]', title: "Date range", content: "Use the From and To filters to scope every figure to a specific period." },
      { selector: '[data-tour="fxt-export"]', title: "Export CSV", content: "Download the current trader view — with all metrics — as a CSV." },
      { selector: '[data-tour="fxt-table"]', title: "Open a trader", content: "Click any trader's name to open their live FX Artha account — positions, trades and ledger." },
    ],
    next: { label: "Traders & Lots", route: "/traders-lots" },
  },

  // DAGChain — Overview
  "/dagchain": {
    steps: [
      { selector: '[data-tour="dc-tiles"]', title: "Platform snapshot", content: "Total users, node revenue, and the count of validator and storage nodes." },
      { selector: '[data-tour="dc-validator"]', title: "Validator nodes", content: "Nodes sold, revenue, blocks validated, rewards earned and how many are active now." },
      { selector: '[data-tour="dc-storage"]', title: "Storage nodes", content: "Storage node sales, rewards, active nodes and total capacity." },
      { selector: '[data-tour="dc-users"]', title: "All Users", content: "Open the full DAGChain user list — wallet, DGC balance, referrals, KYC and nodes." },
    ],
    next: { label: "DAGChain Users", route: "/dagchain-users" },
  },

  // DAGChain — Users list
  "/dagchain-users": {
    steps: [
      { selector: '[data-tour="dcu-search"]', title: "Search users", content: "Find a user by name, email or wallet address." },
      { selector: '[data-tour="dcu-kyc"]', title: "Filter by KYC", content: "Narrow the list to a KYC status — not started, pending, approved or rejected." },
      { selector: '[data-tour="dcu-export"]', title: "Export CSV", content: "Download every user and their full details as a CSV." },
      { selector: '[data-tour="dcu-table"]', title: "Open a user", content: "Click any user's name to open their Customer 360 profile." },
    ],
    next: { label: "DAGChain Nodes", route: "/dagchain-nodes" },
  },

  // KPI & Performance
  "/kpi": {
    steps: [
      { selector: '[data-tour="kpi-tabs"]', title: "Switch views", content: "Move between the KPI Board, Auto Performance, raw KPI Entries and the Performance score." },
      { selector: '[data-tour="kpi-business"]', title: "Filter by business", content: "Scope the KPI board to a single business unit, or view all of them together." },
      { selector: '[data-tour="kpi-period"]', title: "Choose the period", content: "Pick the month and year — every KPI is recalculated for that period, rolled up the org tree." },
    ],
    next: { label: "Traders & Lots", route: "/traders-lots" },
  },

  // Proposals
  "/proposals": {
    steps: [
      { selector: '[data-tour="prop-new"]', title: "Build a proposal", content: "Open the proposal builder — add line items, tax and discount, then generate a PDF. Once accepted, the customer and revenue are created automatically." },
      { selector: '[data-tour="prop-search"]', title: "Search proposals", content: "Find an existing proposal by title or reference." },
      { selector: '[data-tour="prop-stats"]', title: "At a glance", content: "How many proposals are total, sent and still in draft." },
      { selector: '[data-tour="prop-list"]', title: "Manage proposals", content: "Send, accept, reject, download, revise or delete each proposal from the list." },
    ],
    next: { label: "Customers", route: "/m/customers" },
  },

  // Org hierarchy
  "/hr/hierarchy": {
    steps: [
      { selector: '[data-tour="hier-people"]', title: "Org summary", content: "The total number of people in the org, across every hierarchy level." },
      { selector: '[data-tour="hier-heads"]', title: "Top-level heads", content: "How many people sit at the very top of the tree, with no manager above them." },
      { selector: '[data-tour="hier-tree"]', title: "The reporting tree", content: "Who reports to whom, built from each employee's manager. Use the chevron on any node to expand or collapse their reports." },
    ],
    next: { label: "HR — People", route: "/hr/people" },
  },
};

// Feature tours for dynamic routes, matched by path prefix (e.g. the real path
// is /fxartha-account/123). Keys must end with a slash.
const PREFIX_TOURS = {
  // FX Artha — single trader account
  "/fxartha-account/": {
    steps: [
      { selector: '[data-tour="fxa-metrics"]', title: "Account metrics", content: "Balance, equity, credit, margin and leverage — the live state of this trading account." },
      { selector: '[data-tour="fxa-trades"]', title: "Trades", content: "Every open and closed trade. Filter by symbol, or switch between all, open and closed." },
      { selector: '[data-tour="fxa-ledger"]', title: "Ledger", content: "Every balance movement. Search it, or filter by type and date range." },
      { selector: '[data-tour="fxa-ib"]', title: "IB / Referral", content: "The trader's introducing-broker status — level, upline, commissions, referrals and followers." },
    ],
    next: { label: "FX Artha Traders", route: "/fxartha-traders" },
  },
};

// route -> index in TOUR, so every page can fall back to a one-line description
// and a "next module" pointer even without a hand-built feature tour.
const TOUR_INDEX = Object.fromEntries(TOUR.map((t, i) => [t.route, i]));

// The module that naturally comes after this one in the sidebar order.
const nextInTour = (pathname) => {
  const i = TOUR_INDEX[pathname];
  if (i == null) return null;
  const n = TOUR[i + 1];
  return n ? { label: n.label, route: n.route } : null;
};

// A minimal, always-safe tour for any page without a hand-built one: a single
// centered card describing the page, plus a pointer to the next module. `center`
// steps need no on-page target, so they can never land on a blank area.
function genericPageTour(pathname) {
  const i = TOUR_INDEX[pathname];
  if (i != null) {
    const e = TOUR[i];
    return { steps: [{ center: true, title: e.label, content: e.content }], next: nextInTour(pathname) };
  }
  return {
    steps: [{
      center: true,
      title: "This page",
      content: "This screen shows the full details for the item you opened. Press the “?” Help button on any page for a guided walkthrough of its features.",
    }],
    next: null,
  };
}

// Returns { steps, next } for a page. Never null — every page gets at least the
// generic walkthrough, so the Help button always does something useful.
export function pageTour(pathname) {
  // Generic list screens (/m/*) share the ResourceTable toolbar tour.
  if (pathname.startsWith("/m/")) {
    return { steps: RESOURCE_STEPS, next: NEXT[pathname] || nextInTour(pathname) };
  }
  // Exact custom page, then a dynamic-route prefix match.
  let entry = PAGE_TOURS[pathname];
  if (!entry) {
    const key = Object.keys(PREFIX_TOURS).find((k) => pathname.startsWith(k));
    if (key) entry = PREFIX_TOURS[key];
  }
  if (entry && entry.steps && entry.steps.length) {
    return { steps: entry.steps, next: entry.next ?? NEXT[pathname] ?? nextInTour(pathname) };
  }
  return genericPageTour(pathname);
}

