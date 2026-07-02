# DAGOS — Build Status, Implementation Plan & Integration Requirements

> Working document mapping the two client PRDs (Vision PRD + "Product/Revenue/Target/Incentive Logic v3.0") against the current codebase.
> Three sections: **A.** What's done vs left · **B.** Next implementation plan · **C.** What to collect from the client per business.

---

## A. STATUS — DONE vs LEFT

Legend: ✅ Done · ⚠️ Partial · ❌ Not started

### Phase 1 — Core CRM
| Capability | Status | Detail |
|---|---|---|
| JWT Auth, password reset | ✅ | Email login, 12h access / 7d refresh |
| Roles & 3-layer permissions | ✅ | Role→module CRUD, business scoping, owner scoping; editable in UI |
| Business/Product access matrix (per RM/Team) | ✅ | `UserPermission` per user×business×product |
| Lead management + 360 profile + timeline | ✅ | |
| Lead distribution — round-robin / performance / manual | ✅ | |
| Lead distribution — **team-based (TL re-distributes)** | ❌ | Named in PRD §7 |
| **Mandatory call control** (lock next lead until update) | ❌ | PRD §9 — hard requirement, not implemented |
| Opportunities (multiple per lead) | ⚠️ | Model supports; UI is flat, not grouped per lead |
| Customer 360 (cross-business) | ✅ | |
| Revenue (gross / commission / net stored separately) | ✅ | |
| Target management | ⚠️ | Static values only; **CTC×multiplier missing** (Logic §5) |
| Support desk (tickets + SLA) | ✅ | |
| Reporting / dashboards | ✅ | Role dashboards + P&L + charts |

### Phase 2 — HR / Incentive / Payroll
| Capability | Status | Detail |
|---|---|---|
| Attendance + active/idle activity tracking | ✅ | Heartbeat + counters |
| Employee profile / HR | ✅ | |
| Leave apply→approve | ⚠️ | Single-step; **Manager→HR two-step missing** (PRD §22) |
| **CTC engine** (cost categories, per-employee cost) | ✅ | Matches Logic §3 |
| **P&L per hierarchy level** (RM→TL→SM→BH rollup) | ✅ | Matches Logic §4 |
| Payroll (salary+incentive+bonus−deduction) | ✅ | |
| Incentive engine | ⚠️ | Only percentage/fixed/slab on **revenue**; multi-condition missing |

### The strategic gaps (mostly Logic Doc v3.0)
| Capability | Status | What's missing |
|---|---|---|
| **Admin Formula Builder** (Logic §16) | ❌ | No rule engine; incentive rule is a fixed enum |
| **3 weighted scorecards** Revenue/Growth/Activity (§13) | ❌ | No scorecard or weightage model |
| **CTC-based targets w/ multipliers** (§5) | ❌ | Targets are static numbers |
| **Per-product metrics & revenue types** (§6–10) | ❌ | Products generic; no nodes-sold, storage-GB, DGCC value, lots, deposits, enrollments |
| **FX AUM logic** — New/Existing/Withdrawals/Net New AUM (§11) | ❌ | No deposit/withdrawal/AUM model |
| **Client loss / business contribution** (§12) | ❌ | Configurable contribution formula not modeled |
| **Meeting KPI & meeting incentives** (§9, §15) | ❌ | "Meeting" is only an activity type |
| **Dynamic unlimited hierarchy** (rename/reorder, no code) (§2) | ⚠️ | `HierarchyLevel` configurable, but reporting rides single `manager` FK |
| **Integration Hub / data sync** (PRD §27–28) | ⚠️ | Only inbound lead webhooks; no Forex/Chain/GPT CRM sync |
| **Internal employee ticketing** (PRD §17) | ⚠️ | Tickets are customer-bound only |
| **Communication center** (WA/Email/SMS/Telegram logging) (§18) | ⚠️ | Model + Twilio WA/call exist; SMS/Telegram/Email-thread not wired |
| **Executive Command Center / Founder view** (§29) | ⚠️ | Admin dashboard exists; not full ecosystem rollup |
| **AI Layer** (§30) | ⚠️ | Heuristic stubs; designed to swap to real LLM |

---

## B. NEXT IMPLEMENTATION PLAN (sequenced)

> Ordered so each block unblocks the next. The "configuration/rules layer" is the spine of DAGOS and should come before product-specific work.

**Sprint 0 — Close Phase-1 gaps (quick wins)**
- Mandatory call control: lock next lead until outcome/remarks/follow-up/next-action saved (PRD §9).
- Team-based lead distribution (TL receives, re-assigns to members).
- Two-step leave approval (Manager → HR).

**Sprint 1–2 — Configuration & Rules Engine (the spine)**
- Generic **metric registry**: define KPIs/metrics per business & product without code (nodes sold, storage GB, lots, deposits, enrollments, DGCC value…).
- **Admin Formula Builder**: condition→action rules (`Revenue > Cost×2 → 10%`, `Meetings > 10 → $200`). Safe expression evaluator + rule storage + audit.
- **CTC-based targets**: `Target = CTC × Multiplier` with admin-configurable multipliers.

**Sprint 3 — Incentive & Performance**
- **Multi-condition incentives** built on the formula engine: revenue/deposit/AUM/user-acquisition/retention/meeting/lot/node/course/hybrid.
- Target-achievement **slab model** (0–100% none, 100–200% 10%, …).
- **3 weighted scorecards** (Revenue/Growth/Activity) with admin weightage → feeds performance ranking & leaderboard.

**Sprint 4 — FX / domain revenue modeling**
- AUM model: Existing / New / Withdrawals / **Net New AUM**, surfaced for RM→BH.
- Revenue sources split (brokerage/spread/swap/insurance/staking).
- Client loss / **business contribution** with admin formula.

**Sprint 5 — Integration Hub framework**
- Connector abstraction: REST pull, webhook push, scheduled sync jobs, per-source field mapping, sync logs, idempotency/dedup.
- Reuse existing webhook ingestion; generalize to deposits/lots/nodes/subscriptions/enrollments — see Section C.

**Sprint 6 — Per-business connectors** (depends on client deliverables in Section C)
- One connector per business as credentials/APIs arrive.

**Sprint 7 — Command Center & Communication**
- Founder ecosystem dashboard; complete WhatsApp/Email/SMS/Telegram logging.

**Phase 4 — AI Layer**
- Swap heuristic AI service for real LLM (call summary, scoring, forecasting, ticket classification).

---

## C. WHAT TO COLLECT FROM THE CLIENT — PER BUSINESS

> For **every** business we need the same baseline before any connector can be built. Then each business has specifics.

### Baseline (ask for ALL six businesses)
1. **Source system name & vendor** — what platform currently runs this business (CRM/trading server/billing/LMS) and is it SaaS or self-hosted.
2. **API access** — base URL, API docs, auth method (API key / OAuth client id+secret / token), and a **sandbox/test environment**.
3. **Credentials** — issued to us in a secure vault (no plaintext email).
4. **Webhook capability** — can the system push events to us? If yes, what events; we supply the endpoint + secret.
5. **Data dictionary** — field names/types for the entities we need + sample payloads.
6. **Sync direction & frequency** — real-time webhook vs scheduled pull; how often.
7. **Identity mapping** — how a customer/lead in their system maps to ours (email/phone/external id).
8. **Rate limits & SLAs**, and a **technical point of contact** per business.
9. **Compliance** — any KYC/PII handling constraints, data residency.

### 1. FX Artha (Forex)
- **Likely source:** MetaTrader **MT4/MT5** (Manager/Server API) and/or broker back-office CRM.
- **Need:** MT4/5 **Manager API** credentials (server IP, manager login/password) or back-office REST API + key.
- **Data to sync:** deposits, withdrawals, **lots traded**, brokerage/spread/swap/insurance/staking revenue, open AUM per client, IB/partner commission structure, active traders.
- **Specifics:** definition of **Net New AUM** and the **business-contribution** formula (deposit − trading loss + brokerage + insurance…) so admin can model it.

### 2. DAGChain (blockchain)
- **Likely source:** custom commerce/checkout + on-chain data.
- **Need:** API/webhook for **node sales** (Developer Node $3,000, Storage Node $/GB, Validator), **renewals**, and **DGCC** token-sale dollar value.
- **On-chain:** contract addresses, network/RPC endpoint or explorer API key (for token sales / wallet attribution), treasury/sales wallet addresses.
- **Data to sync:** node units sold, storage GB sold, DGCC $ value sold, new/active/retained users.

### 3. DAGGPT (AI SaaS)
- **Likely source:** billing provider (e.g. Stripe) + the product's own usage metering.
- **Need:** billing API key + webhook secret; product **subscription/API-usage** API.
- **Data to sync:** subscription revenue, API revenue, enterprise/white-label revenue, active users, retention/churn, plan tier per customer.

### 4. DAGDB (data infrastructure)
- **Likely source:** metering/usage system + billing.
- **Need:** usage-metering API + billing API.
- **Data to sync:** storage usage, contract value, enterprise deals, active accounts.

### 5. DAG Energy DAO
- **Likely source:** investment/participation platform (possibly on-chain).
- **Need:** participation/investment API or webhook; if on-chain, contract addresses + RPC/explorer access.
- **Data to sync:** participation amounts, infrastructure investments, yield-program payouts, participant identity.

### 6. DAG Army (LMS / education)
- **Likely source:** LMS (Teachable / Thinkific / LearnDash / custom) + payment gateway.
- **Need:** LMS API key + **enrollment/sale webhooks**; payment-gateway credentials.
- **Data to sync:** course sales (current price ~$149), enrollments, student count, active students, certifications, retention.

---

### Consolidated "ask list" to send the client
For each of the 6 businesses, request a single sheet with:
- Platform/vendor name + admin contact
- API base URL + documentation link
- Auth type + credentials (via secure vault) + sandbox access
- Webhook support (yes/no) + event list
- Required-entity field mapping + sample payloads
- Sync frequency expectation
- The **business-specific formula definitions** (FX Net New AUM & contribution; incentive slabs; meeting/lot/node/course reward amounts) — needed for the Formula Builder.

> Note: the original PRD lists **six** businesses (FX Artha, DAGChain, DAGGPT, DAGDB, DAG Energy DAO, DAG Army). All six are covered above.
