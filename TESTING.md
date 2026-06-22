# DAGOS CRM — Testing Guide (Step by Step)

Is document me har module ko test karne ka complete flow hai — kya click karna hai,
kya data daalna hai, aur kya result aana chahiye.

---

## 0. Services chalu hain ya nahi (Pre-check)

App use karne se pehle 3 cheezein chalni chahiye:

| Service | URL | Test |
|---|---|---|
| Frontend | http://localhost:5173 | Browser me khulna chahiye |
| Backend API | http://localhost:8010/api/docs/ | Swagger page khule |
| AI Service | http://localhost:8101/docs | FastAPI docs khule |

Agar koi band hai to in commands se chalu karo (3 alag terminal me):

```bash
# Terminal 1 - Backend
cd "e:/crm doc/backend" && ./.venv/Scripts/python.exe manage.py runserver 8010

# Terminal 2 - AI Service
cd "e:/crm doc/ai-service" && ./.venv/Scripts/python.exe -m uvicorn app.main:app --port 8101

# Terminal 3 - Frontend
cd "e:/crm doc/frontend" && npm run dev
```

---

## 1. LOGIN / AUTHENTICATION

| # | Step | Expected Result |
|---|------|-----------------|
| 1.1 | Browser me kholo `http://localhost:5173` | Login page — left side dark branding, right side form |
| 1.2 | Email/password pehle se bhare hain (`admin@dagos.com` / `admin123`). **Sign in** dabao | Dashboard khul jaye |
| 1.3 | Logout karo (top-right corner ka logout icon) | Wapas login page |
| 1.4 | Galat password daalo (e.g. `wrong123`) → Sign in | Red error: "Invalid email or password" |
| 1.5 | Sahi credentials se dobara login | Dashboard |

✅ **Pass:** Login/logout aur galat password handling theek.

---

## 2. DASHBOARD

| # | Step | Expected Result |
|---|------|-----------------|
| 2.1 | Login ke baad Dashboard pe ho | 8 KPI cards: Total Leads, Open Pipeline, Net Revenue, Open Tickets, Customers, Converted, Gross Revenue, Open Opps |
| 2.2 | Numbers dekho | Total Leads = 120, Customers = 29 (demo data) |
| 2.3 | "Net Revenue Trend" chart | Area chart with months |
| 2.4 | "Leads by Source" pie chart | Colors + legend (Meta Ads, Google Ads, etc.) |
| 2.5 | "Opportunities by Stage" bar chart | Bars: proposal, negotiation, won, lost, active |
| 2.6 | Right side **AI Insights** panel | 2-4 insight cards (Conversion Rate, Pipeline, Net Margin…) |

✅ **Pass:** Saare charts + AI insights data ke saath load.

---

## 3. LEADS (sabse important module)

| # | Step | Expected Result |
|---|------|-----------------|
| 3.1 | Sidebar → **Sales & CRM → Leads** | Table with ~100 leads, columns: Code, Name, Phone, Country, Source, Owner, Score, Status |
| 3.2 | **Score** column dekho | Colored progress bar (green/amber/red) + number |
| 3.3 | Top-right search box me type karo (e.g. `LD0001`) | List filter ho jaye |
| 3.4 | **+ New** button dabao | Modal form khule |
| 3.5 | Form bharo: Lead code `LD9999`, Name `Test Lead`, Phone `+919999999999`, Source select, Assign to select, Status = `new` | — |
| 3.6 | **Save** dabao | Modal band, naya lead list me top pe aaye |
| 3.7 | Us lead ki row pe **pencil (edit)** icon | Form pre-filled khule |
| 3.8 | Status `new` → `qualified` karo → Save | Status badge update ho jaye |
| 3.9 | **trash (delete)** icon → Confirm | Row gayab |

✅ **Pass:** Create, Read, Search, Update, Delete sab chalein.

---

## 4. LEAD ACTIVITIES

| # | Step | Expected Result |
|---|------|-----------------|
| 4.1 | Sidebar → **Lead Activities** | Table: Lead#, Type, Remarks, Follow-up, By |
| 4.2 | **+ New** → Lead select karo, Type = `call`, Remarks = `Interested`, Follow-up date set karo → Save | Naya activity add ho |
| 4.3 | Type badge dekho | Color badge (call/whatsapp/email…) |

---

## 5. OPPORTUNITIES

| # | Step | Expected Result |
|---|------|-----------------|
| 5.1 | Sidebar → **Opportunities** | Table: Lead, Product, Owner, Stage, Expected (₹), Status |
| 5.2 | **+ New** → Lead select, Product select, Stage = `negotiation`, Expected revenue = `25000`, Status = `open` → Save | Naya opportunity, Expected = $25,000 dikhe |
| 5.3 | Edit karke Stage = `won` karo | Badge green ho jaye |

---

## 6. CUSTOMERS

| # | Step | Expected Result |
|---|------|-----------------|
| 6.1 | Sidebar → **Customers** | ~29 customers table |
| 6.2 | Search me naam type karo | Filter ho |
| 6.3 | **+ New** → Name, Email, Phone, Country → Save | Naya customer |

---

## 7. COMMUNICATIONS

| # | Step | Expected Result |
|---|------|-----------------|
| 7.1 | Sidebar → **Communications** | Channel, Direction, Message, When |
| 7.2 | **+ New** → Channel = `whatsapp`, Direction = `outbound`, Customer select, Message type karo → Save | Naya record |

---

## 8. TARGETS & REVENUE

| # | Step | Expected Result |
|---|------|-----------------|
| 8.1 | **Targets** → table dikhe (har business ka Q-Target) | — |
| 8.2 | **Revenue** → Gross, Commission, Net columns | Net = Gross − Commission (auto) |
| 8.3 | Revenue **+ New** → Customer select, Gross = `10000`, Commission = `1500` → Save | Net column me `$8,500` aaye (backend auto-calc) |

✅ **Key test:** Net revenue khud calculate hota hai.

---

## 9. SETUP (Business / Products / Lead Sources)

| # | Step | Expected Result |
|---|------|-----------------|
| 9.1 | **Businesses** → 6 businesses (FX Artha, DAGChain…) | Products count dikhe |
| 9.2 | **Products** → business ke saath products | — |
| 9.3 | **+ New** Product → Name, Business select, Status → Save | Naya product |

---

## 10. SUPPORT DESK

| # | Step | Expected Result |
|---|------|-----------------|
| 10.1 | Sidebar → **Support → Support Desk** | ~40 tickets: Ticket#, Customer, Category, Priority, Agent, Status |
| 10.2 | Priority badges dekho | urgent=red, high=amber, etc. |
| 10.3 | **+ New** → Ticket no `TK9999`, Customer, Priority = `high`, Status = `open` → Save | Naya ticket |
| 10.4 | Edit → Status `open` → `resolved` | Badge green |

---

## 11. HR & PEOPLE

| # | Step | Expected Result |
|---|------|-----------------|
| 11.1 | **Employees** → 15 employees, Salary column | — |
| 11.2 | **Departments** → Sales, Support, HR, Finance, Tech | — |
| 11.3 | **Attendance** → date-wise, Hours, Status badges | — |
| 11.4 | **Activity Tracking** → Active min, Calls, Tickets | — |
| 11.5 | **Leaves** → From/To, Reason, Status (pending/approved) | — |
| 11.6 | **Payroll** → **Net Pay** auto-calc test ↓ | |
| 11.7 | Payroll **+ New** → Employee select, Basic = `50000`, Incentive = `5000`, Bonus = `2000`, Deduction = `1000`, Month = `6`, Year = `2026` → Save | **Net Pay = $56,000** (50000+5000+2000−1000) |
| 11.8 | **Incentives** / **Incentive Rules** → tables load | — |

✅ **Key test:** Payroll final salary formula auto chale.

---

## 12. FINANCE

| # | Step | Expected Result |
|---|------|-----------------|
| 12.1 | **Expenses** → Type, Department, Amount, Date | — |
| 12.2 | **Commissions** → Partner, Business, Amount | — |
| 12.3 | Dono me **+ New** se record add karke check karo | Save ho jaye |

---

## 13. ADMINISTRATION

| # | Step | Expected Result |
|---|------|-----------------|
| 13.1 | **Users** → 15 users, Role, Status | — |
| 13.2 | **+ New** User → Name, Email, Role select, Password set → Save | Naya user (ye user login bhi kar sakta hai) |
| 13.3 | **Roles** → 8 roles (Super Admin, RM, HR…) | — |
| 13.4 | **Teams** → Team A/B/C with leaders | — |

---

## 14. REPORTS

| # | Step | Expected Result |
|---|------|-----------------|
| 14.1 | Sidebar → **Reports** | 2 charts: Leads by Status (bar), Revenue by Business (horizontal bar) |
| 14.2 | Neeche Revenue table | Business-wise Gross/Net breakdown |

---

## 15. AI ASSISTANT (sabse interesting)

| # | Step | Expected Result |
|---|------|-----------------|
| 15.1 | Sidebar → **Overview → AI Assistant** | Left: chat box, Right: Lead Scorer |
| 15.2 | Chat me type karo: `how many leads do I have?` → Send | AI reply with lead count |
| 15.3 | Chat: `what is my revenue?` | AI reply with net revenue figure |
| 15.4 | Right panel **Lead Scorer**: Source = `Referral`, Status = `qualified`, Activity count = `4` → **Score Lead** | Bada number (e.g. 100), **Grade A**, reasons list, recommended action |
| 15.5 | Source = `CSV`, Status = `lost`, Activity = `0` → Score Lead | Low score, **Grade D** |

✅ **Pass:** Chat reply aaye aur scoring grade badle.

---

## 16. RESPONSIVE / UI

| # | Step | Expected Result |
|---|------|-----------------|
| 16.1 | Browser window chhota karo (mobile size) | Sidebar hide ho, hamburger menu (☰) aaye |
| 16.2 | ☰ dabao | Sidebar slide-in ho |
| 16.3 | Kisi bhi page pe refresh (F5) karo | Logged-in raho (token persist) |

---

## Common Issues (agar kuch na chale)

| Problem | Reason | Fix |
|---|---|---|
| Login pe "Network Error" | Backend (8010) band hai | Backend terminal chalu karo |
| Dashboard pe AI Insights khaali | AI service (8101) band hai | AI terminal chalu karo |
| Page blank / 404 on refresh | — | URL `http://localhost:5173` se start karo |
| Save fail (red alert) | Required field khaali | `*` wale fields bharo |
| Port conflict error | 8000/8010 busy | Doosra port use karo + `.env.local` update |

---

## Quick Smoke Test (2 minute me sab check)

1. Login → Dashboard charts dikhe ✅
2. Leads → New lead banao ✅
3. Revenue → Gross 10000, Commission 1500 → Net 8500 auto ✅
4. Payroll → New → Net Pay auto-calc ✅
5. AI Assistant → Lead score karo (Grade aaye) ✅
6. Logout ✅

Agar ye 6 chal gaye, **pura system theek hai.** 🎉
