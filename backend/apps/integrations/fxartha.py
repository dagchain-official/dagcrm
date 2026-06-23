"""FX Artha external CRM API connector (read-only proxy).

Keeps the API key server-side. Works in 'not configured' mode (clear message)
until FXARTHA_API_URL + FXARTHA_API_KEY env vars are set.
"""
from django.conf import settings


def is_configured():
    return bool(settings.FXARTHA_API_URL and settings.FXARTHA_API_KEY)


def fx_get(path, params=None):
    """Call an FX Artha endpoint. Returns (data, http_status)."""
    if not is_configured():
        return ({"error": "not_configured",
                 "detail": "FX Artha API not configured. Set FXARTHA_API_URL + FXARTHA_API_KEY."}, 503)
    import requests
    base = settings.FXARTHA_API_URL.rstrip("/")
    try:
        r = requests.get(f"{base}{path}",
                         headers={"X-API-Key": settings.FXARTHA_API_KEY},
                         params={k: v for k, v in (params or {}).items() if v not in (None, "")},
                         timeout=20)
        try:
            data = r.json()
        except ValueError:
            data = {"raw": r.text[:1000]}
        return data, r.status_code
    except requests.RequestException as e:
        return ({"error": "request_failed", "detail": str(e)[:200]}, 502)
