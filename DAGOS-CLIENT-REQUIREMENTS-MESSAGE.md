# Requirements From Client — To Proceed With DAGOS Development

Hi,

To proceed with development and start connecting your businesses into DAGOS, we'll need the following from your end. I've broken each point down so it's clear exactly what to share. You can send items as they become ready — we'll start with whatever comes first.

---

## 1. Business APIs & Credentials (data connections)

For **each** business, please share: the **platform/software name**, **API base URL + documentation**, the **access credentials** (API key or login), whether it supports **webhooks** (auto push of events to us), and a **technical contact person**. Credentials should be shared securely (we'll provide a safe link — please don't send over normal email/WhatsApp).

### ✅ FX Artha (Forex) — highest priority
- Platform name (e.g. MT4 / MT5 / broker back-office)
- **Deposit / Withdrawal API** (to track client deposits & withdrawals)
- **Transaction / Slab Webhook** (to receive live events for brokerage, lots, slab triggers)
- API key or login credentials + the API documentation
- Data we need access to: deposits, withdrawals, lots traded, brokerage earned, AUM per client

### ✅ DAGChain
- Sales API or webhook for **Developer Nodes, Storage Nodes, DGCC coin sales, renewals**
- API key / credentials + documentation
- If sales are on-chain: wallet/contract addresses + network details

### ✅ DAGGPT
- Subscription / billing API + webhook (the system that charges customers)
- Usage API (API calls, active users)
- API key / credentials + documentation

### ✅ DAGDB
- Usage + billing API (storage usage, contracts, accounts)
- API key / credentials + documentation

### ✅ Energy DAO
- Participation / investment API or webhook (participation amounts, investments, yield payouts)
- API key / credentials + documentation

### ✅ DAG Army
- Course platform API + **enrollment webhook** (course sales, students, certifications)
- Platform name (Teachable / Thinkific / custom) + payment gateway details
- API key / credentials + documentation

> If any business currently has **no API/software** (runs on spreadsheets), just let us know — we'll configure DAGOS for direct manual entry for that one.

---

## 2. Lead Source Credentials (Facebook + Google)

To pull leads automatically from ad campaigns:

- **Facebook / Meta:** App ID, App Secret, **Page ID**, Page Access Token (and admin access to the Lead Ads forms)
- **Google:** Google Ads Developer Token, OAuth Client ID + Secret, and the Ads Account (Customer) ID
- Confirmation of which Facebook Pages / Google accounts feed which business

---

## 3. Document Templates & Branding

- **Document formats/templates** with sample copies and the fields each should contain:
  - Proposal
  - Quotation
  - Invoice
  - Finance / Receipt documents
- **Logo files** — for each business + the main DAGOS brand, in high resolution (transparent PNG and/or SVG preferred)
- Any brand colors / letterhead style to apply on generated PDFs

---

## 4. Email Access

- The **email address** the system should send from (e.g. no-reply@dagos.com) and its **SMTP credentials** (host, port, username, password)
- OR confirmation of the sending domain so we can set up email delivery

---

## 5. Product List With Pricing

- Full **product catalogue per business** with current pricing and the **revenue type** (one-time / recurring / per-unit / token), for example:
  - FX Artha: Trading Account, VIP, Funded, VPS, Copy Trading
  - DAGChain: Developer Node ($3,000), Storage Node ($/GB), DGCC, Validator
  - DAGGPT: Subscription, Enterprise, API Access, White Label
  - DAGDB, Energy DAO, DAG Army (courses ~$149): same detail

---

## 6. Formulas & Business Condition Logic

Since DAGOS is fully configurable, we need your current rules in writing so we set them up correctly the first time:

- **Targets** (e.g. Target = Employee Cost × Multiplier)
- **Cost to Company (CTC)** — which cost categories to include
- **Performance weightage** (Revenue % / Growth % / Activity %)
- **FX-specific formulas:** Net New AUM, and client Business Contribution

---

## 7. Slab Incentive Logic — detailed specification (important)

For the **Slab Incentive Logic**, please provide a clear documentation/specification that includes:

- **All products** covered
- The **slab structure** (the ranges/tiers)
- **Incentive percentages / amounts** per slab
- **All conditional rules and edge cases**
- Any **exceptions or special scenarios**

This will let us implement the complete slab logic accurately, with no ambiguity.

> **Let's also schedule one dedicated discussion only for the Slab Logic**, so we can walk through every condition once before implementation. That ensures everything is built exactly as expected.

---

Once we have these, we'll begin connecting the businesses one at a time, starting with the one you most want live first. Happy to jump on a quick call to walk through any of the above.

Thanks!
