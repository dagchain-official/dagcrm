// Product-tour content. One entry per sidebar item we walk through. `route`
// matches the NavLink `to` (and its data-tour attribute); the tour only shows
// entries whose element is actually on the page — i.e. modules this user can see.
// Keep the copy short: what the module is + what you do there.

export const TOUR = [
  {
    route: "/",
    label: "Dashboard",
    content:
      "This is your home base — an overview of leads, customers, revenue and pipeline. Each role sees a dashboard tailored to them.",
  },
  {
    route: "/ai",
    label: "AI Assistant",
    content:
      "Ask questions about your CRM data directly — 'How many leads came in this month?', 'Who's the top RM?' — and the AI answers in real time.",
  },
  {
    route: "/m/leads",
    label: "Leads",
    content:
      "New leads land here (WhatsApp/Google/manual). Add, search/filter, assign an RM, CSV import — all in one place. Click any lead to see its full history.",
  },
  {
    route: "/m/opportunities",
    label: "Opportunities",
    content:
      "Leads that have turned into deals — their opportunities. Track the stage (proposal → negotiation → won) and expected revenue here.",
  },
  {
    route: "/proposals",
    label: "Proposals",
    content:
      "Build a quotation/proposal for a customer — line items, tax/discount, and PDF. Once accepted, the customer and revenue are created automatically.",
  },
  {
    route: "/m/customers",
    label: "Customers",
    content:
      "Your own (converted) customer book. Click any customer → Customer 360 (full details + RM reassignment).",
  },
  {
    route: "/targets",
    label: "Targets",
    content:
      "Set and track the revenue target for each RM/team. Target = CTC × multiplier (configured in Rules).",
  },
  {
    route: "/kpi",
    label: "KPI & Performance",
    content:
      "Each employee's KPIs (calls, meetings, lots…) and performance score. Everything is admin-configurable — nothing is hardcoded.",
  },
  {
    route: "/fxartha",
    label: "FX Artha",
    content:
      "Live data from the FX Artha trading platform — traders, deposits, lots, revenue. In 'Traders', click any trader → their live account (positions, trades, ledger).",
  },
  {
    route: "/dagchain",
    label: "DAGChain",
    content:
      "Live data from the DAGChain platform — users, wallet/DGC balance, validator & storage nodes, and node-purchase revenue.",
  },
  {
    route: "/hr/people",
    label: "HR — People",
    content:
      "Employees, departments, hierarchy. All HR tools — Attendance, Leave, Payroll and Recruitment — live in this group.",
  },
  {
    route: "/finance",
    label: "Finance (P&L)",
    content:
      "The business P&L — revenue vs expenses vs commissions. AUM and Contribution are also in this Finance group.",
  },
  {
    route: "/integrations",
    label: "Integration Hub",
    content:
      "Connect every platform (Meta/Google/WhatsApp/FXArtha/DAGChain) from here. Add the webhook URL on that platform → leads/data flow straight into the CRM.",
  },
  {
    route: "/permissions",
    label: "Permission Matrix",
    content:
      "Which role can view/edit which module (Layer 3), and which user can see which business's data (Layer 2) — it's all controlled here.",
  },
  {
    route: "/config",
    label: "Configuration",
    content:
      "Businesses, products, lead sources and the rest of the setup — add new items from here.",
  },
];
