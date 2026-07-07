# DAGOS — Role-by-Role Flow, Hierarchy & Responsibilities

Har role: kaun kiske upar/neeche hai, kya responsibility hai, aur kahan-kahan jaana hai (click flow).

---

## 🏢 HIERARCHY (kaun kiske upar)
```
                 SUPER ADMIN            (sabse upar — poora system)
                     │
                BUSINESS HEAD           (ek business ka malik — uska saara data)
                     │
                SALES DIRECTOR          (business ka sales head)
                     │
                SALES MANAGER           (teams manage karta)
                     │
                 TEAM LEADER            (ek team lead karta)
                     │
             SALES EXECUTIVE / RM       (ground level — leads pe kaam)

     Side roles (sabke saath):   SUPPORT   ·   HR   ·   FINANCE
```

---

## 1️⃣ SUPER ADMIN
- **Upar:** koi nahi (top) · **Neeche:** sab
- **Responsibility:** Poora system — setup, saari businesses, users, permissions, integrations, config. Har cheez dekh/kar sakta hai.
- **Flow:**
  1. **Administration → Users / Roles** → team + roles banao
  2. **Administration → Permission Matrix** → kaun kya dekhe/kare set karo
  3. **Administration → Configuration** → Businesses, Products, KPI Definitions, Lead Sources
  4. **Administration → Integration Hub** → FX Artha + baaki businesses connect
  5. **Targets → Assign Target** → **kisi ko bhi** (any business) target do
  6. Sab dashboards, P&L, reports dekho
- **Restriction:** koi nahi.

## 2️⃣ BUSINESS HEAD
- **Upar:** Super Admin · **Neeche:** Sales Director → poora business
- **Responsibility:** Apne business ka poora control — sales, revenue, targets, team, P&L.
- **Flow:**
  1. **Dashboard** → business ka overview
  2. **Targets → Assign Target** → apni business/team ko target (CTC auto-calc)
  3. **Team Requests** → Sales Managers ki requests **approve/reject**
  4. **KPI & Performance / Target Board** → poore business ki performance
  5. **Finance → P&L / AUM / Contribution** → profit dekho
- **Restriction:** sirf **apne business/subtree** tak (dusri business nahi — woh Admin karta).

## 3️⃣ SALES DIRECTOR
- **Upar:** Business Head · **Neeche:** Sales Manager
- **Responsibility:** Business ke **sales org** ko chalana — managers ko target dena, team structure approve karna.
- **Flow:**
  1. **Dashboard** → sales org overview
  2. **Targets → Assign Target** → Sales Managers / unki teams ko target (apni subtree)
  3. **Team Requests** → SM ki team-member requests **approve/reject**
  4. **KPI & Performance / Target Board** → managers ki performance monitor
  5. **Leads → Distribute** (zaroorat pe)
- **Restriction:** sirf **apni subtree** tak.

## 4️⃣ SALES MANAGER
- **Upar:** Sales Director · **Neeche:** Team Leaders → RMs
- **Responsibility:** Teams manage karna — leads baantna, kaam monitor karna, performance nikaalna.
- **Flow:**
  1. **Dashboard** → team overview
  2. **Leads → Distribute** → RMs ko baanto (round-robin/performance/manual)
  3. **Activities / Opportunities / Proposals** → team ke kaam pe nazar
  4. **KPI & Performance / Target Board** → performance monitor
  5. **Team Requests** → naya member chahiye → **request daalo**
  6. **Leaves** → team ke leave approve
- **Restriction:** ❌ target **assign nahi** kar sakta · ❌ apni team **khud pick nahi** (request se).

## 5️⃣ TEAM LEADER
- **Upar:** Sales Manager · **Neeche:** Sales Executives (RMs)
- **Responsibility:** Apni team ko lead karna — leads pe kaam karwana, follow-ups ensure karna.
- **Flow:**
  1. **Dashboard** → team ki daily activity
  2. **Leads** → team ke leads dekho, distribute karo
  3. **Activities / Opportunities / Proposals** → team ke deals aage badhao
  4. **KPI & Performance** → team ki performance
  5. **Leaves** → team ke leave approve
- **Restriction:** target sirf **view** (assign nahi).

## 6️⃣ SALES EXECUTIVE / RM (ground level)
- **Upar:** Team Leader · **Neeche:** koi nahi
- **Responsibility:** **Leads ko customer banana** — call/WhatsApp/email, follow-up, proposal, close.
- **Flow (rozana ka core):**
  1. **Dashboard** → aaj ke leads + follow-ups
  2. **Leads** → apni assigned leads (sirf apni dikhengi)
  3. Lead kholo → **Call / WhatsApp / Email** → remarks + **next follow-up** save
  4. **Send Proposal** → product select (price auto) → WhatsApp/Email se bhejo
  5. Client "haan" → **Accept** → ⚙️ auto Customer + Revenue
  6. **My Attendance** (check in/out) + **My Leaves** (apply)
- **Restriction:** sirf **apni leads** dikhti hain · leads kisi aur ko assign nahi kar sakta.

---

## 🎯 SIDE ROLES

## SUPPORT
- **Responsibility:** Customer tickets handle karna.
- **Flow:** **Support → Support Desk** → ticket kholo → Assign → In Progress → **Resolved** → Closed. Comments + SLA track.
- **Restriction:** sirf tickets + customers (view).

## HR
- **Responsibility:** People, attendance, leaves, payroll, incentives, CTC.
- **Flow:**
  1. **HR → People** → employees/departments/levels
  2. **HR → Cost & CTC** → cost categories + employee costs (CTC)
  3. **HR → Attendance & Leave** → attendance + leaves approve
  4. **HR → Payroll & Incentives** → Incentives **Recalculate** → Payroll (auto-fill) → Net Pay
- **Restriction:** sales/finance data nahi (apne HR modules).

## FINANCE
- **Responsibility:** Paisa — revenue, expenses, commissions, payroll, P&L, AUM, contribution.
- **Flow:**
  1. **Finance → Finance (P&L)** → Expenses/Commissions + P&L Statement
  2. **Finance → AUM** → Net New AUM (Forex)
  3. **Finance → Contribution** → net client value
  4. Payroll/incentives verify
- **Restriction:** apne finance modules (sales edit nahi).

---

## 🔄 POORA ECOSYSTEM — ek picture
```
Super Admin  →  sab set karta (users, permissions, config, integrations)
     │
Business Head → apni business ka target + approvals + P&L
     │
Sales Director → managers ko target + team approvals
     │
Sales Manager → leads baantta + team request + monitor
     │
Team Leader → team se kaam karwata
     │
RM → leads → call/proposal → CUSTOMER + REVENUE  ← yahan asli paisa banta hai
     │
     ├─ Support → us customer ke tickets
     ├─ HR → us RM ki attendance/salary/incentive
     └─ Finance → revenue → P&L → profit
```

**Ek line mein:**
> Upar wale (Admin → BH → Director) **target dete + approve karte** hain, beech wale (Manager → TL) **baantte + monitor karte** hain, aur **RM asli kaam karke paisa banata** hai — Support, HR, Finance side se sambhaalte hain.

---

## KAUN KYA "EXTRA" KAR SAKTA (quick table)
| Role | Target assign | Team banao/approve | Sabka data | Sirf apna |
|---|---|---|---|---|
| Super Admin | ✅ kisi ko bhi | ✅ | ✅ sab | — |
| Business Head | ✅ apni subtree | ✅ approve | ✅ apni business | — |
| Sales Director | ✅ apni subtree | ✅ approve | subtree | — |
| Sales Manager | ❌ (view) | 🔸 request only | team | — |
| Team Leader | ❌ (view) | ❌ | team | — |
| Sales Executive/RM | ❌ | ❌ | — | ✅ apni leads |
| Support / HR / Finance | ❌ | ❌ | apne module | — |
