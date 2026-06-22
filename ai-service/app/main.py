from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    ChatIn, ChatOut, InsightIn, InsightOut, LeadIn, LeadScoreOut,
)
from .scoring import assistant_reply, build_insights, score_lead

app = FastAPI(title="DAGOS AI Service", version="1.0.0",
              description="AI layer: lead scoring, insights & assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "dagos-ai"}


@app.post("/score/lead", response_model=LeadScoreOut)
def score(lead: LeadIn):
    return score_lead(lead)


@app.post("/insights/summary", response_model=InsightOut)
def insights(data: InsightIn):
    return {"insights": build_insights(data)}


@app.post("/assistant/chat", response_model=ChatOut)
def chat(payload: ChatIn):
    return {"reply": assistant_reply(payload.message, payload.context)}
