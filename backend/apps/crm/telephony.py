"""Twilio click-to-call + WhatsApp. Works in 'manual' mode without credentials
(activity still logged); flips to LIVE the moment Twilio env vars are set."""
from django.conf import settings


def _client():
    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    if not sid or not token:
        return None
    try:
        from twilio.rest import Client
        return Client(sid, token)
    except Exception:
        return None


def make_call(lead_phone, agent_phone=None):
    """Click-to-call: ring the agent, then dial the lead."""
    client = _client()
    if not client or not settings.TWILIO_FROM_NUMBER:
        return {"live": False, "note": "Logged (configure Twilio for live calling)"}
    try:
        target = agent_phone or lead_phone
        call = client.calls.create(
            to=target, from_=settings.TWILIO_FROM_NUMBER,
            twiml=f"<Response><Dial>{lead_phone}</Dial></Response>",
        )
        return {"live": True, "sid": call.sid}
    except Exception as e:
        return {"live": False, "error": str(e)[:120]}


def send_whatsapp(lead_phone, body):
    client = _client()
    if not client or not settings.TWILIO_WHATSAPP_FROM:
        return {"live": False, "note": "Logged (configure Twilio WhatsApp to send live)"}
    try:
        msg = client.messages.create(
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
            to=f"whatsapp:{lead_phone}", body=body,
        )
        return {"live": True, "sid": msg.sid}
    except Exception as e:
        return {"live": False, "error": str(e)[:120]}
