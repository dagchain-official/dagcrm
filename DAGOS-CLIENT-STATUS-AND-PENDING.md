# DAGOS — Simple Flow + What's Still Left to Configure

For explaining to the client: how the system works (easy words) + what we still need
from your side / what's left to set up.

---

# PART 1 — HOW IT WORKS (simple flow)

**One line:** A lead comes in → your team turns it into a deal → the deal makes money →
the system tracks everything (sales, support, HR, salary, targets, profit) on its own.

### The everyday flow
1. **Lead aati hai** — from ads, a file upload, or by hand → system auto-gives it to a salesperson.
2. **Salesperson kaam karta hai** — calls / WhatsApp / email, saves notes + next follow-up.
3. **Proposal bhejta hai** — picks product (price auto), sends by WhatsApp/Email.
4. **Deal close** — on "yes", the lead **automatically** becomes a Customer + Revenue is booked.
5. **Customer 360** — one screen shows that customer's products, money, tickets, chats.
6. **Support** — customer's problems become tickets (open → resolved).

### Runs by itself (behind the scenes)
- **Targets** = each person's cost × a multiplier (rolls up team → business).
- **Incentives & Payroll** calculate automatically from revenue.
- **P&L** (profit) shows at every level.
- **FX Artha data** (deposits, withdrawals, brokerage, lots) flows in **automatically every minute**.

> Full step-by-step is in **DAGOS-DETAILED-FLOW.md** and **DAGOS-CRM-COMPLETE-FLOW.md**.

---

# PART 2 — WHAT'S ALREADY DONE ✅

- Full CRM: leads → proposals → customers → revenue → support
- Roles, permissions, reporting hierarchy (Business Head → Sales Director → Sales Manager → Team Leader → RM)
- Targets (CTC-based) + team assignment + approval workflow
- KPI & Performance (auto-detected) + scorecards
- HR: attendance, leaves, payroll (auto), incentives (auto), CTC
- Finance: revenue, expenses, P&L, AUM board, Contribution board
- **FX Artha integration** — LIVE, auto-syncing every 1 minute (leads, customers, revenue, AUM, contribution, lots)

---

# PART 3 — WHAT'S STILL LEFT TO CONFIGURE ⏳

These need **your input / credentials / decisions** before they can go live.

## A. Connect the other 5 businesses (only FX Artha is connected)
For each we need the **API access / credentials** (like we got for FX Artha):
- ⏳ **DAGChain** — node/coin sales API
- ⏳ **DAGGPT** — subscription/billing API
- ⏳ **DAGDB** — usage/billing API
- ⏳ **Energy DAO** — participation/investment API
- ⏳ **DAG Army** — course platform (LMS) API + enrollment webhook

## B. Lead sources (ad leads)
- ⏳ **Facebook/Meta:** App ID, App Secret, Page ID (to auto-pull Lead Ads)
- ⏳ **Google Ads:** developer token + account access

## C. Business rules — you must define the actual values
The engine is built; we need your **real numbers/rules in writing**:
- ⏳ **Slab incentive spec** — exact slabs, %/amounts, all conditions & edge cases (needs a dedicated call)
- ⏳ **Target multipliers** — e.g. 1.5× / 2× / 3× per level or person
- ⏳ **Contribution formula** — confirm the weights (brokerage, insurance, staking, trading loss…)
- ⏳ **Product list + real prices** for every business

## D. Communication channels
- ⏳ **Twilio** (SID + token + numbers) — for LIVE calls & WhatsApp (right now it only "logs")
- ⏳ **Email / SMTP** — to actually send proposals & alerts (right now dev/console mode)
- ⏳ **SMS / Telegram** — to be wired if needed

## E. Branding & documents
- ⏳ **Logo files** (each business + main)
- ⏳ **Document templates** — Proposal, Quotation, Invoice, Finance/Receipt

## F. Go-live (hosting)
- ⏳ **Deploy to a server** with a public web address + HTTPS (right now it runs on a local machine only).
  Needed for: everyone to access it online, ad-lead webhooks, and real-time FX webhooks.

## G. Optional upgrades
- ⏳ **Real-time FX webhook** — instant (vs the current 1-minute auto-sync); needs FX Artha to support webhooks + the system hosted online.
- ⏳ **AI Layer (Phase 2)** — smart call summaries, AI forecasting, ticket auto-classification (currently a basic version).

---

# QUICK CHECKLIST TO GIVE THE CLIENT
```
[ ] API access for: DAGChain, DAGGPT, DAGDB, Energy DAO, DAG Army
[ ] Facebook (App ID/Secret/Page ID) + Google Ads access
[ ] Slab incentive document + target multipliers + contribution weights
[ ] Product list with real prices (per business)
[ ] Twilio credentials (calls/WhatsApp) + Email/SMTP
[ ] Logo files + document templates (proposal/quotation/invoice/finance)
[ ] Decision: where to host it online (server + domain + HTTPS)
```

---

**Summary line for the client:**
> "The full system is built and working — FX Artha is already live and syncing on its own.
> To finish, we mainly need **the other 5 businesses' API access, your rules/prices, the
> ad-platform & communication credentials, logos/templates, and a server to host it online.**"
