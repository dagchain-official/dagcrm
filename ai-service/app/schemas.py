from typing import List, Optional

from pydantic import BaseModel


class LeadIn(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    country: str = ""
    source: str = ""
    activity_count: int = 0
    status: str = "new"


class LeadScoreOut(BaseModel):
    score: int
    grade: str
    reasons: List[str]
    recommended_action: str


class InsightIn(BaseModel):
    total_leads: int = 0
    converted_leads: int = 0
    open_opportunities: int = 0
    pipeline_value: float = 0
    gross_revenue: float = 0
    net_revenue: float = 0
    open_tickets: int = 0


class Insight(BaseModel):
    title: str
    detail: str
    severity: str  # info | good | warning


class InsightOut(BaseModel):
    insights: List[Insight]


class ChatIn(BaseModel):
    message: str
    context: Optional[dict] = None


class ChatOut(BaseModel):
    reply: str
