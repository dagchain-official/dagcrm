# DAGOS CRM — Complete Usage & Flow (Client Guide)

A simple, step-by-step guide to the whole system: **what to do first, and what comes next.**
Written in easy words so anyone can follow it.

---

## What is DAGOS? (one line)
> DAGOS is **one system** to run everything — sales, customers, support, HR, salary, targets, incentives and profit — for **all your businesses** (FX Artha, DAGChain, DAGGPT, DAGDB, Energy DAO, DAG Army) under **one login**.

**How work flows in one line:**
`A lead comes in → your team turns it into a deal → the deal makes money → the system tracks everything (sales, support, HR, salary, targets, profit) automatically.`

---

# PART 1 — ONE-TIME SETUP (do this first, only once)

You set up the "shape" of your company. Do these in order.

### Step 1 — Add your Businesses
Sidebar → **Setup → Businesses** → add each company (FX Artha, DAGChain, etc.).

### Step 2 — Add Products & Prices
Sidebar → **Setup → Products** → under each business, add its products with prices
(e.g. Forex "VIP Account", DAGChain "Developer Node $3,000").

### Step 3 — Add your Team (Users)
Sidebar → **Administration → Users** → create each employee and give them a **role**:
```
Super Admin → Business Head → Sales Director → Sales Manager → Team Leader → Sales Executive
                                                              (+ Support, HR, Finance)
```

### Step 4 — Set the Reporting Structure
Sidebar → **HR & People → People → Employees** → for each person set their
**Manager (reports to)** and **Level**. This decides how targets and profit roll up
(RM → Team Leader → Sales Manager → Sales Director → Business Head).

### Step 5 — Control who can see/sell what (Permissions)
Sidebar → **Administration → Permission Matrix**:
- **Module Permissions** → per role, tick what they can View/Create/Edit/Delete.
- **Business Access** → e.g. "RM A can sell only Forex + DAGChain, not Energy DAO."

### Step 6 — HR & Cost setup (needed for salary + targets)
Sidebar → **HR & People**:
- **People** → Departments, Hierarchy Levels
- **Cost & CTC** → Cost Categories (Visa, Laptop, Internet…) + Employee Costs
  → this builds each person's **CTC** (Cost To Company = salary + costs).
- **Attendance & Leave** → Leave Types (Casual, Sick, Unpaid…)

### Step 7 — Rules setup (so the system runs itself, no coding)
Sidebar → **HR & People → Rules & Config** + **Setup**:
- **Target Multipliers** → Target = CTC × Multiplier (e.g. 2×).
- **Incentive Slabs** → e.g. 100%–200% of target = 10% incentive.
- **Activity Incentives** → e.g. 100 lots = $2/lot, 10 meetings = $200.
- **Formula Builder** → any custom rule: "if Revenue > Cost × 2 → 10% incentive".
- **Performance Weights** → Revenue 60% / Growth 25% / Activity 15%.
- **KPI Definitions** (Setup) → define what to measure (Lots, Nodes, Meetings…).
- **Contribution Formula** (Finance) → how to calculate net client value.

> ✅ After setup, the system is ready and shaped around **your** business.

---

# PART 2 — DAILY SALES FLOW (the heart of the system)

### Step 1 — Leads arrive
Leads come in 3 ways (Sidebar → **Sales & CRM → Leads**):
- **Automatically** from Facebook / Google ads (via Integrations)
- **CSV upload** (bulk)
- **Manual entry** (one by one)

### Step 2 — Give leads to the team
Leads page → **Distribute** → choose:
- Round-robin (equal), Performance-based (top reps get more), or Manual.

### Step 3 — The salesperson works the lead
Open a lead → **Lead Detail**:
- **Call / WhatsApp / Email** the customer (buttons).
- After each contact, **save remarks + next follow-up date** (mandatory — keeps everyone honest).
- Every action is saved on the **timeline**, and the lead status moves forward:
  `New → Contacted → Qualified → Converted`

### Step 4 — Track the deal (Opportunity)
One lead can have many deals (opportunities). A deal moves through stages:
`Active → Proposal → Negotiation → Won / Lost`
- **Negotiation** = you sent a proposal and are discussing price/terms before closing.

### Step 5 — Send a Proposal
From Lead Detail (or **Proposals**) → build the proposal:
- Pick a product → **price auto-fills** → add quantity/discount/tax.
- Send it by **WhatsApp** or **Email** directly (or Save & Send).

### Step 6 — Close the deal
When the client says yes → **Accept** the proposal. The system then **automatically**:
- Converts the lead into a **Customer**
- Books the **Revenue**
- Marks the deal **Won**

### Step 7 — Customer 360
Sidebar → **Sales & CRM → Customers** → open a customer to see **everything in one place**:
products, revenue, support tickets, all communication, documents, timeline.

### Step 8 — Support
If a customer has a problem → a **Ticket** is created → Assigned → In Progress → Resolved.
Sidebar → **Support → Support Desk**.

---

# PART 3 — TARGETS & TEAM MANAGEMENT

### Step 1 — Assign Targets (based on cost)
Sidebar → **Sales & CRM → Targets → Assign Target** tab:
- Choose **Individual / Team / Business** → the system shows the **CTC automatically**
  → apply a **multiplier** → it suggests the **target** (Target = CTC × multiplier).
- **Who can assign whom:**
  - **Admin** → anyone (even other businesses)
  - **Business Head / Sales Director** → only their own team/business
  - **Sales Manager** → cannot assign; instead they **request** (see below)

### Step 2 — See target progress
**Targets → Target Board** tab → a tree showing each person/team/business:
target vs achieved, rolled up the hierarchy.

### Step 3 — Build the team (with approval)
Sidebar → **Sales & CRM → Team Requests**:
- A **Sales Manager** cannot pick their own team members directly.
- They **raise a request** for a person → the **higher authority** (Sales Director /
  Business Head / Admin) **Approves or Rejects** → on approval, the person joins the team.

---

# PART 4 — KPI & PERFORMANCE (mostly automatic)

Sidebar → **Sales & CRM → KPI & Performance** (all in one, switch by tabs):
- **KPI Board** → all KPIs per person/team, rolled up.
- **Auto Performance** → the system **automatically detects** performance (calls, meetings,
  leads converted) from real activity. **Filter by year / month / metric / employee.**
- **KPI Entries** → for KPIs the system can't auto-read (e.g. lots), enter them by a **simple form**.
- **Performance** → each person's scorecard (Revenue / Growth / Activity, weighted).

---

# PART 5 — HR (attendance, leave, salary, incentives)

### Attendance & Leave
- **My Attendance** → employee checks **In / Out**; active/idle time is tracked.
- **My Leaves** → employee applies → manager approves/rejects.

### Payroll (salary)
Sidebar → **HR & People → Payroll & Incentives → Payroll**:
- Pick an employee → **basic salary, incentive, deduction auto-fill**
  → `Net Pay = Basic + Incentive + Bonus − Deduction`.

### Incentives (automatic)
- **Incentives** are calculated **automatically** from revenue using your rules
  (slabs + activity rewards + formulas) and flow into payroll.

---

# PART 6 — FINANCE & PROFIT

Sidebar → **Finance**:
- **Expenses / Commissions** → record company costs and partner payouts.
- **P&L Statement** → profit = revenue − cost, for **every level** (RM → Team → Business).
- **AUM Board** (for Forex) → how much money clients hold: New Deposits − Withdrawals = **Net New AUM**.
- **Contribution** → net value each client brings (brokerage + insurance − trading loss…), by a formula you control.

---

# PART 7 — CONNECT YOUR BUSINESSES (Integrations)
Sidebar → **Integrations** → connect each platform (FX Artha, Meta, Google, WhatsApp…).
Once connected, data (leads, customers, revenue, deposits) flows into DAGOS **on its own**.

---

# PART 8 — OWNER / BOSS VIEW
- **Dashboards** → each role gets its own (leads, revenue, tickets, team performance).
- **Reports** → sales, revenue, P&L, AUM, contribution — the whole ecosystem in one place.

---

# THE FULL FLOW — IN ONE PICTURE
```
SETUP (once): Businesses → Products → Team+Roles → Permissions → Hierarchy → HR/Cost → Rules
      │
      ▼
DAILY: Lead arrives → Distribute → Call/Follow-up → Proposal → Deal Won
      │
      ▼
Customer created → Revenue booked → Support if needed
      │
      ▼
MANAGE: Assign Targets (CTC×multiplier) → Team Requests/Approvals → KPI auto-tracked
      │
      ▼
HR: Attendance → Leaves → Incentives (auto) → Payroll
      │
      ▼
MONEY: Revenue → Expenses → P&L (per level) → AUM & Contribution (Forex)
      │
      ▼
OWNER: Dashboards + Reports (whole ecosystem, one screen)
```

---

# DEMO SCRIPT — how to show the client (suggested order)
Say this while clicking through the app:

1. **"One login for everything."** Log in → show the dashboard.
2. **"All your businesses live here."** Setup → Businesses & Products.
3. **"You control who sees and sells what."** Permission Matrix → toggle a role.
4. **"Leads come in and get shared to the team."** Leads → Distribute.
5. **"Your team works each lead — and can't fake it."** Lead Detail → Call/WhatsApp,
   show the mandatory remarks + follow-up + timeline.
6. **"Send a professional proposal in seconds."** Build proposal (price auto-fills) →
   send by WhatsApp/Email.
7. **"One click turns a deal into money."** Accept proposal → show it became a Customer +
   Revenue automatically.
8. **"See a customer's whole story in one place."** Customer 360.
9. **"Targets are based on real cost, and roll up."** Targets → Assign Target (CTC shows
   automatically) → Target Board.
10. **"Managers request team members; seniors approve."** Team Requests.
11. **"Performance is tracked automatically."** KPI & Performance → Auto Performance → filter.
12. **"Salary and incentives calculate themselves."** Payroll → pick employee (auto-fills).
13. **"See profit at every level."** Finance → P&L.
14. **"Connect your existing systems and data flows in."** Integrations.
15. **Close:** "One system — sales, support, HR, salary, targets, and profit — for your
    entire ecosystem, running mostly on its own."

---

**Golden line to end with:**
> *"A lead comes in, your team turns it into money, and DAGOS handles the rest — sales,
> support, HR, salary, targets and profit — all in one place, mostly automatic."*
