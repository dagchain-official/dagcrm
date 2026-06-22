"""Heuristic lead-scoring + insight engine.

Deliberately rule-based so the service runs with zero external API keys.
Swap `score_lead` / `assistant_reply` internals for an LLM call later
(e.g. Anthropic Claude) without changing the API surface.
"""
from .schemas import Insight, LeadIn

HOT_SOURCES = {"referral", "website", "whatsapp"}
WARM_SOURCES = {"meta ads", "google ads", "telegram"}


def score_lead(lead: LeadIn) -> dict:
    score = 30
    reasons: list[str] = []

    src = (lead.source or "").lower()
    if src in HOT_SOURCES:
        score += 25
        reasons.append(f"High-intent source ({lead.source})")
    elif src in WARM_SOURCES:
        score += 12
        reasons.append(f"Paid/medium source ({lead.source})")

    if lead.email:
        score += 8
        reasons.append("Email captured")
    if lead.phone:
        score += 10
        reasons.append("Phone captured")

    if lead.activity_count >= 3:
        score += 20
        reasons.append("Strong engagement (3+ activities)")
    elif lead.activity_count >= 1:
        score += 10
        reasons.append("Some engagement")

    status_boost = {"qualified": 15, "contacted": 8, "converted": 25, "lost": -25}
    if lead.status in status_boost:
        score += status_boost[lead.status]
        reasons.append(f"Status: {lead.status}")

    score = max(0, min(100, score))

    if score >= 75:
        grade, action = "A", "Call now — high conversion probability"
    elif score >= 50:
        grade, action = "B", "Follow up within 24h with tailored offer"
    elif score >= 30:
        grade, action = "C", "Nurture via WhatsApp/email sequence"
    else:
        grade, action = "D", "Low priority — automate or recycle"

    return {"score": score, "grade": grade, "reasons": reasons or ["Baseline score"],
            "recommended_action": action}


def build_insights(d) -> list[Insight]:
    out: list[Insight] = []
    conv = (d.converted_leads / d.total_leads * 100) if d.total_leads else 0
    if d.total_leads:
        sev = "good" if conv >= 20 else "warning" if conv < 10 else "info"
        out.append(Insight(title="Lead Conversion Rate",
                           detail=f"{conv:.1f}% of {d.total_leads} leads converted.",
                           severity=sev))
    if d.pipeline_value:
        out.append(Insight(title="Open Pipeline",
                           detail=f"{d.open_opportunities} open opportunities worth ${d.pipeline_value:,.0f}.",
                           severity="info"))
    if d.gross_revenue:
        margin = (d.net_revenue / d.gross_revenue * 100) if d.gross_revenue else 0
        out.append(Insight(title="Net Margin",
                           detail=f"Net margin at {margin:.1f}% (${d.net_revenue:,.0f} net of ${d.gross_revenue:,.0f}).",
                           severity="good" if margin >= 80 else "warning"))
    if d.open_tickets > 10:
        out.append(Insight(title="Support Load",
                           detail=f"{d.open_tickets} unresolved tickets — consider re-balancing the support queue.",
                           severity="warning"))
    if not out:
        out.append(Insight(title="Getting Started",
                           detail="Not enough data yet. Add leads and revenue to unlock insights.",
                           severity="info"))
    return out


def assistant_reply(message: str, context: dict | None) -> str:
    m = message.lower()
    ctx = context or {}
    if "lead" in m:
        return (f"You currently have {ctx.get('total_leads', 'some')} leads. "
                "Focus on grade A/B leads first — I can score any lead from the Leads page.")
    if "revenue" in m or "sales" in m:
        return (f"Net revenue is ${ctx.get('net_revenue', 0):,.0f}. "
                "Check Revenue by Business in Reports to see top performers.")
    if "ticket" in m or "support" in m:
        return (f"There are {ctx.get('open_tickets', 0)} open tickets. "
                "Prioritise 'urgent' and 'high' priority first.")
    return ("I'm your DAGOS assistant. Ask me about leads, revenue, pipeline, "
            "tickets, or open any module to act on the data.")
