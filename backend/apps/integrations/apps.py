import os
import sys
import threading
import time

from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.integrations"
    _autosync_started = False

    def ready(self):
        # Auto-sync only inside the running server (not during migrate/shell/etc.),
        # and only when enabled. Disable with AUTO_SYNC=0.
        if os.environ.get("AUTO_SYNC", "1") != "1":
            return
        if "runserver" not in sys.argv and not os.environ.get("FORCE_AUTOSYNC"):
            return
        if IntegrationsConfig._autosync_started:
            return
        IntegrationsConfig._autosync_started = True
        threading.Thread(target=_autosync_loop, daemon=True).start()


def _autosync_loop():
    """Every AUTO_SYNC_INTERVAL seconds, pull connected FXArtha connections so
    deposits/withdrawals, revenue, AUM and contribution update on their own."""
    interval = int(os.environ.get("AUTO_SYNC_INTERVAL", "600"))  # default 10 min
    time.sleep(20)  # let the server finish booting
    while True:
        try:
            _run_sync_once()
        except Exception:  # noqa: BLE001 — never let the loop die
            pass
        time.sleep(interval)


def _run_sync_once():
    from django.db import close_old_connections
    close_old_connections()
    from .models import IntegrationConnection
    from .services_fxartha import sync_fxartha
    for conn in IntegrationConnection.objects.filter(platform="fxartha", status="connected"):
        sync_fxartha(conn)
    close_old_connections()
