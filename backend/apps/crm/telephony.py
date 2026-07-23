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


def _e164(num):
    """Twilio needs E.164 (+123456789) — strip spaces, dashes and brackets."""
    if not num:
        return None
    s = "".join(ch for ch in str(num) if ch.isdigit() or ch == "+")
    return s or None


def make_call(lead_phone, agent_phone=None):
    """Click-to-call: ring the agent, then dial the lead."""
    client = _client()
    if not client or not settings.TWILIO_FROM_NUMBER:
        return {"live": False, "note": "Logged (configure Twilio for live calling)"}
    lead = _e164(lead_phone)
    agent = _e164(agent_phone)
    if not lead:
        return {"live": False, "error": "Lead has no phone number"}
    if not agent:
        # without the agent's number we can't bridge the call — don't ring the
        # lead with a call that just dials themselves.
        return {"live": False, "note": "Logged — set the agent's phone number to place live calls"}
    try:
        call = client.calls.create(
            to=agent, from_=settings.TWILIO_FROM_NUMBER,
            twiml=f"<Response><Dial>{lead}</Dial></Response>",
        )
        return {"live": True, "sid": call.sid}
    except Exception as e:
        return {"live": False, "error": str(e)[:160]}


def send_whatsapp(lead_phone, body):
    client = _client()
    if not client or not settings.TWILIO_WHATSAPP_FROM:
        return {"live": False, "note": "Logged (configure Twilio WhatsApp to send live)"}
    lead = _e164(lead_phone)
    if not lead:
        return {"live": False, "error": "Lead has no phone number"}
    try:
        msg = client.messages.create(
            from_=f"whatsapp:{_e164(settings.TWILIO_WHATSAPP_FROM)}",
            to=f"whatsapp:{lead}", body=body,
        )
        return {"live": True, "sid": msg.sid}
    except Exception as e:
        return {"live": False, "error": str(e)[:120]}
