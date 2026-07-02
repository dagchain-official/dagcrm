# DAGOS CRM — DETAILED SYSTEM FLOW

Har module ka poora detail: **kahan hai, kaun use karta hai, kya bharna hai, click ke baad kya hota hai, aur peeche-peeche system kya automatic karta hai.**

Legend: 🔵 = aap karte ho · ⚙️ = system automatic karta hai · 🔗 = kis module se juda hai

---

## 0. LOGIN & DASHBOARDS
- 🔵 `admin@dagos.com / admin123` (ya koi bhi user) se login.
- ⚙️ Login pe system aapka **role** dekhta hai aur uske hisaab se:
  - Sidebar mein sirf allowed modules dikhata hai (permission ke hisaab se).
  - Role ke hisaab se dashboard kholta hai (Admin, Sales Manager, Team Leader, HR, Finance, Support).
- **Hierarchy (roles):** Super Admin → Business Head → Sales Director → Sales Manager → Team Leader → Sales Executive (+ Support, HR, Finance).

---

# PHASE A — SETUP (ek baar, is exact order mein)

### A1. Businesses
- 🔵 Setup → **Businesses** → New → naam + description + status.
- 🔗 Har cheez (products, leads, revenue, targets) inhi businesses se judti hai.

### A2. Products
- 🔵 Setup → **Products** → New → business choose + naam + **Type** (dropdown, "add new" bhi) + **price** + **revenue type** (one-time / recurring / per-unit / token).
- ⚙️ **Duplicate block:** ek business mein same naam ka product dobara nahi banega.
- 🔗 Product ka price aage **Proposal** mein auto-aata hai.

### A3. Users + Roles
- 🔵 Administration → **Users** → New → naam, email, **role**, password.
- 🔵 Administration → **Roles** → agar naya role chahiye.

### A4. Reporting Hierarchy (bahut important)
- 🔵 HR & People → **People → Employees** tab → har employee edit → **Reports to (manager)** + **Org Level** set karo.
- ⚙️ Yahi manager-chain se **Target roll-up, P&L tree, KPI roll-up, aur delegation** kaam karte hain.
- Structure: RM → Team Leader → Sales Manager → Sales Director → Business Head.

### A5. Permissions (2 layers)
- 🔵 Administration → **Permission Matrix**:
  - **Module Permissions** tab → role choose → har module ke View/Create/Edit/Delete toggle.
  - **Business Access** tab → user choose → sirf kuch businesses tick (jaise "RM sirf Forex+DAGChain").
- ⚙️ System har API call pe ye check karta hai — bina permission ke action block.

### A6. HR & Cost (CTC banane ke liye)
- 🔵 HR & People → **People** → Departments, Hierarchy Levels.
- 🔵 HR & People → **Cost & CTC**:
  - **Cost Categories** (Visa, Laptop, Internet, Office…).
  - **Employee Costs** → per employee per month cost rows.
- ⚙️ **CTC = Employee.salary + saare Employee Costs.** (Ye Target + P&L dono mein use hota hai.)
- 🔵 HR & People → **Attendance & Leave → Leave Types** (Casual, Sick, Unpaid…).

### A7. Rules (system automatic banane ke liye — no coding)
- 🔵 HR & People → **Rules & Config**:
  - **Target Multipliers** → `Target = CTC × multiplier` (global / level / employee).
  - **Performance Weights** → Revenue% / Growth% / Activity% (default 60/25/15).
  - **Formula Builder** → custom rule: "if Revenue > Cost × 2 → 10%".
  - **Formula Payouts** → formula ka preview + payroll mein daalna.
- 🔵 HR & People → **Payroll & Incentives**:
  - **Incentive Slabs** → 0–100% no incentive, 100–200% → 10%, 200–400% → 20%…
  - **Activity Incentives** → KPI × rate (100 lots × $2, 10 meetings → $200).
  - **Incentive Rules** → simple %/fixed/slab per business/product.
- 🔵 Setup → **KPI Definitions** → kya measure karna hai (Lots, Nodes, Meetings, Deposits…), unit, aggregation (sum/count/avg/latest), category (growth/activity), source (**manual** ya **derived**).
- 🔵 Finance → **Contribution Formula** → net client value ke weights (brokerage×1, trading_loss×−1…).

> ✅ Setup complete → system aapki business ke shape mein taiyaar.

---

# PHASE B — DAILY SALES FLOW (step-by-step)

### B1. Lead andar aati hai
3 tareeke (Sales & CRM → **Leads**):
1. ⚙️ **Integration se auto** (Facebook/Google/FXArtha) → lead auto-create + auto-assign RM ko.
2. 🔵 **CSV upload** → "Import template" download → bharo → upload → ⚙️ system validate + duplicate (phone/email) skip + lead codes generate.
3. 🔵 **Manual** → New → naam, email, phone, **country (dropdown → phone code auto aata hai)**, source.

### B2. Leads distribute
- 🔵 Leads → **Distribute** → mode:
  - **Round-robin** (barabar), **Performance** (top RMs ko zyada), **Manual**.
- ⚙️ System sabse kam load wale RM ko ya top performers ko assign karta hai + notification bhejta hai.

### B3. RM lead pe kaam karta hai (Lead Detail)
- 🔵 Lead pe click → **Lead Detail** → upar naam, **status funnel**, **AI score**.
- 🔵 **Engage buttons:**
  - **Call** → ⚙️ activity log + status `contacted` + Twilio (creds ho to live, warna "logged").
  - **WhatsApp / Email** → message modal → send → ⚙️ Communication log + timeline.
  - **Send Proposal** → ProposalBuilder khulta hai.
- ⚙️ **Auto status advance:** call/whatsapp/email → contacted; meeting/proposal → qualified.
- ⚙️ **Activity counters bump:** RM ke calls/notes counters HR activity mein badhte hain.

### B4. Opportunity (deal tracker)
- Ek lead ke **kai opportunities** (alag products).
- Stages: `Active → Proposal → Negotiation → Won / Lost`.
- 🔵 **Negotiation** manually set karo jab proposal ke baad price/terms pe baat chal rahi ho.

### B5. Proposal banao & bhejo
- 🔵 ProposalBuilder → business choose → ⚙️ **products load** → item select → ⚙️ **unit price auto-fill** → qty/discount/tax.
- ⚙️ Subtotal, discount, tax, total real-time calculate.
- 🔵 Buttons: **Save Draft** · **WhatsApp** · **Email** · **Save & Send**.
- ⚙️ Send pe: status `sent` + timeline pe log + Communication record.

### B6. Deal close (proposal Accept)
- 🔵 Proposals → **Accept**.
- ⚙️ System **automatic chain chalata hai:**
  1. Lead → **converted**.
  2. Naya **Customer** ban jaata hai (lead se linked).
  3. **Opportunity → Won**.
  4. **Revenue book** hoti hai (gross/commission/net).
  5. Customer ke saath products attach.
  6. Timeline pe accountability note.

### B7. Customer 360
- 🔵 Sales & CRM → **Customers** → open.
- ⚙️ Ek jagah: **KPIs** (lifetime revenue, products, open tickets), **tabs** (Products, Revenue, Tickets, Communications, Documents, Timeline).
- 🔵 Quick actions: Add Revenue / Communication / Ticket / Upload doc / Create proposal.

### B8. Support
- 🔵 Support → **Support Desk** → ticket → Assign → In Progress → Resolved → Closed.
- ⚙️ **SLA tracking** (urgent 4h, high 24h…) + RM apne client ke tickets dekh sakta.
- ⚙️ Ticket update pe HR activity counter (tickets_updated) badhta.

---

# PHASE C — TARGETS & TEAM MANAGEMENT

### C1. Target assign karo (CTC-based)
- 🔵 Sales & CRM → **Targets → Assign Target** tab:
  1. **Scope** choose: Individual / Team / Business.
  2. Entity choose (employee / team / business head).
  3. ⚙️ **CTC apne aap calculate** hoke dikhta hai:
     - Individual → us bande ka CTC.
     - Team → poori team ka total CTC.
     - Business → us head ke neeche poori subtree ka CTC.
  4. 🔵 **Multiplier** daalo → ⚙️ **Suggested Target = CTC × multiplier**.
  5. 🔵 **Assign** → ⚙️ Target + assignment ban jaata + sabko notification.
- ⚙️ **Delegation (kaun kisko):**
  - **Admin** → kisi ko bhi (dusri business bhi).
  - **Business Head / Sales Director** → sirf apni subtree.
  - **Sales Manager** → assign **nahi** kar sakta (403).

### C2. Target Board (progress)
- 🔵 Targets → **Target Board** tab → month/year.
- ⚙️ Tree: har person/team/business ka **target vs achieved vs progress%**, roll-up.
  (RM own target; manager = poori team ke targets ka sum.)

### C3. Team banao (approval ke saath)
- 🔵 Sales & CRM → **Team Requests**:
  - Sales Manager apni team khud nahi chunta → **request daalta** (person + team + reason).
  - ⚙️ Upar wale (Sales Director/Business Head/Admin) ko notification.
  - 🔵 Higher authority **Approve/Reject** → ⚙️ approve pe person team mein add + requester ko notification.
  - ⚙️ SM apni request **khud approve nahi** kar sakta.

---

# PHASE D — KPI & PERFORMANCE (mostly automatic)

Sales & CRM → **KPI & Performance** (ek section, tabs):

### D1. KPI Board
- ⚙️ Har KPI, har person/team ka value, hierarchy roll-up (sum/count/avg/latest ke hisaab se).

### D2. Auto Performance (automatic detection)
- ⚙️ **Derived metrics** (Calls, Meetings, Leads Converted) CRM activity se **apne aap detect**.
- 🔵 **Filter:** Year / Month / Metric / Employee.
- ⚙️ Har row pe **Source** dikhta: `auto` (derived) ya `manual`.

### D3. KPI Entries (manual form)
- 🔵 Jo KPI system auto nahi padh sakta (Lots, Nodes) → **form** se enter.
- ⚙️ **Auto-fetch:** agar derived metric + employee choose karo → value apne aap aa jaata (us mahine ka count).

### D4. Performance (scorecard)
- ⚙️ Har employee ke 3 scorecards (Revenue/Growth/Activity) **weighted** (Performance Weights se) → final score + leaderboard.

---

# PHASE E — HR (attendance, leave, salary, incentive)

### E1. Attendance
- 🔵 **My Attendance** → Check In / Check Out.
- ⚙️ Working hours + active/idle time (heartbeat se) track.

### E2. Activity Tracking
- ⚙️ Login/active/idle minutes + calls/notes/tickets counters (real actions se auto-bump).

### E3. Leaves
- 🔵 **My Leaves** → Apply (type + dates + reason).
- 🔵 HR & People → Attendance & Leave → **Leaves** → Approve/Reject.
- ⚙️ **Unpaid leave** approve → payroll deduction mein auto-count.

### E4. Payroll (auto-calc)
- 🔵 HR & People → Payroll & Incentives → **Payroll** → New → employee select.
- ⚙️ **Auto-fill:** basic salary (employee se), incentive (us mahine ka), deduction (unpaid leave se).
- ⚙️ `Net Pay = Basic + Incentive + Bonus − Deduction`.

### E5. Incentives (automatic engine)
- 🔵 **Incentives → Recalculate** (ya Formula Payouts → Run).
- ⚙️ System: Revenue → Customer → Lead → RM → Employee attribute karke:
  - **Slabs** (target achievement %) + **Activity incentives** (KPI × rate) + **Formula rules** apply.
  - Result Payroll ke incentive mein flow.

---

# PHASE F — FINANCE & PROFIT

Sidebar → **Finance**:

### F1. Revenue / Expenses / Commissions
- ⚙️ Revenue deals se auto book (ya manual). Gross − commission = Net.
- 🔵 Expenses (department kharche) + Commissions (partner payout) manually.

### F2. P&L Statement
- 🔵 Month/year choose.
- ⚙️ Har level ka **profit = revenue − CTC cost**, roll-up (RM→TL→SM→BH), margin%.

### F3. AUM Board (Forex)
- ⚙️ Deposits − Withdrawals = **Net New AUM**, org tree roll-up.
- 🔗 Data FXArtha integration se ya AUM Entries se.

### F4. Contribution
- ⚙️ Net client value = `Σ(component × weight)` (brokerage/insurance/staking − trading loss).
- 🔵 Formula weights **Contribution Formula** page se editable.

---

# PHASE G — INTEGRATIONS (data auto-flow)
- 🔵 **Integrations** → platform (FX Artha / Meta / Google / WhatsApp…) → Connect (API key/config) → Sync.
- ⚙️ **FXArtha connector** pull karta hai:
  - `/leads` → Leads · `/customers` → Customers + **Revenue** (brokerage/commission) + **AUM** (deposit/withdrawal).
  - Sab **idempotent** (dubara sync pe duplicate nahi).
- 🔵 **Send Test Lead** se pipeline test.

---

# PHASE H — OWNER / REPORTS
- ⚙️ **Dashboards** — role-wise (leads, revenue, tickets, team performance) + AI insights.
- ⚙️ **Reports** — leads by status/source, revenue by business, P&L, AUM, contribution.
- 🔵 Export PDF / CSV.

---

# BEHIND-THE-SCENES — AUTOMATIC DATA CHAIN
```
Lead (integration/CSV/manual)
   → assigned to RM (auto)
   → activities logged → status auto-advances → activity counters bump (HR)
   → Proposal accepted
        → Customer created (auto)
        → Revenue booked (auto)
        → Opportunity Won (auto)
   → Revenue drives:
        → Incentives (slabs + activity + formula) → Payroll (auto)
        → P&L per level (revenue − CTC)
        → KPI/Performance (derived auto-detected)
   → CTC (salary + costs) drives:
        → Targets (CTC × multiplier, roll-up)
        → P&L cost
   → FX data (deposits/withdrawals) → AUM Board (Net New AUM)
   → everything visible on Dashboards + Reports
```

**Ek line:** *Aap sirf leads aur deals handle karo — DAGOS baaki (customer, revenue, target, incentive, payroll, P&L, AUM) apne aap chain kar deta hai.*
