// Product-tour content. One entry per sidebar item we walk through. `route`
// matches the NavLink `to` (and its data-tour attribute); the tour only shows
// entries whose element is actually on the page — i.e. modules this user can see.
// Keep the copy short: what the module is + what you do there.

export const TOUR = [
  {
    route: "/",
    label: "Dashboard",
    content:
      "Yahi tumhaara home hai — leads, customers, revenue aur pipeline ka overview. Har role ko apne hisaab se dashboard dikhta hai.",
  },
  {
    route: "/ai",
    label: "AI Assistant",
    content:
      "Apne CRM data se seedha sawaal poochho — 'is mahine kitne leads aaye?', 'top RM kaun?' — AI live jawab deta hai.",
  },
  {
    route: "/m/leads",
    label: "Leads",
    content:
      "Naye leads yahan aate hain (WhatsApp/Google/manual). Add, search/filter, RM ko assign, CSV import — sab yahin. Kisi lead pe click karke uski poori history dekho.",
  },
  {
    route: "/m/opportunities",
    label: "Opportunities",
    content:
      "Jo leads deal me badle — unki opportunities. Stage (proposal → negotiation → won) aur expected revenue yahan track karo.",
  },
  {
    route: "/proposals",
    label: "Proposals",
    content:
      "Customer ke liye quotation/proposal banao — line items, tax/discount, aur PDF. Accept hone pe customer + revenue auto ban jaata hai.",
  },
  {
    route: "/m/customers",
    label: "Customers",
    content:
      "Tumhaare apne (converted) customers ka book. Kisi customer pe click → Customer 360 (poori detail + RM reassign).",
  },
  {
    route: "/targets",
    label: "Targets",
    content:
      "Har RM/team ka revenue target set aur track karo. Target = CTC × multiplier (Rules me configure hota hai).",
  },
  {
    route: "/kpi",
    label: "KPI & Performance",
    content:
      "Har employee ke KPIs (calls, meetings, lots…) aur performance score. Sab admin-configurable hai, koi cheez hardcoded nahi.",
  },
  {
    route: "/fxartha",
    label: "FX Artha",
    content:
      "FX Artha trading platform ka live data — traders, deposits, lots, revenue. 'Traders' me kisi trader pe click → uska live account (positions, trades, ledger).",
  },
  {
    route: "/dagchain",
    label: "DAGChain",
    content:
      "DAGChain platform ka live data — users, wallet/DGC balance, validator & storage nodes, aur node-purchase revenue.",
  },
  {
    route: "/hr/people",
    label: "HR — People",
    content:
      "Employees, departments, hierarchy. Attendance, Leave, Payroll aur Recruitment ke saare HR tools isi group me hain.",
  },
  {
    route: "/finance",
    label: "Finance (P&L)",
    content:
      "Business ka P&L — revenue vs expenses vs commissions. AUM aur Contribution bhi isi Finance group me.",
  },
  {
    route: "/integrations",
    label: "Integration Hub",
    content:
      "Har platform (Meta/Google/WhatsApp/FXArtha/DAGChain) yahan se jodo. Webhook URL us platform pe daalo → leads/data seedhe CRM me.",
  },
  {
    route: "/permissions",
    label: "Permission Matrix",
    content:
      "Kaunsa role kaunsa module dekh/edit kar sake (Layer 3), aur kaunsa user kaunse business ka data dekhe (Layer 2) — sab yahan control hota hai.",
  },
  {
    route: "/config",
    label: "Configuration",
    content:
      "Businesses, products, lead sources aur baaki setup — nayi cheezein yahan se add karo.",
  },
];
