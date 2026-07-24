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
    """Every AUTO_SYNC_INTERVAL seconds, pull the connected poll connectors
    (FXArtha AND DAGChain) so revenue, deposits, nodes, staking, AUM and
    contribution update on their own — no manual "Sync" click needed."""
    interval = int(os.environ.get("AUTO_SYNC_INTERVAL", "300"))  # default 5 min
    time.sleep(20)  # let the server finish booting
    while True:
        try:
            _run_sync_once()
        except Exception:  # noqa: BLE001 — never let the loop die
            pass
        time.sleep(interval)


# a fixed key so every worker contends for the SAME Postgres advisory lock
_SYNC_LOCK_KEY = 918273645


def _run_sync_once():
    """One sync pass, guarded by a Postgres advisory lock so that with several
    gunicorn workers only ONE actually syncs each tick (the others skip). The
    lock is released the moment this pass ends, so if the holder dies another
    worker simply picks up the next tick."""
    from django.db import close_old_connections, connection

    close_old_connections()
    with connection.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s)", [_SYNC_LOCK_KEY])
        if not cur.fetchone()[0]:
            return                       # another worker is syncing this tick
    try:
        from .models import IntegrationConnection
        from .services_dagchain import sync_dagchain
        from .services_fxartha import sync_fxartha
        syncers = {"fxartha": sync_fxartha, "dagchain": sync_dagchain}
        for conn in IntegrationConnection.objects.filter(
                platform__in=syncers, status="connected"):
            try:
                syncers[conn.platform](conn)
            except Exception:  # noqa: BLE001 — one bad connection can't stop the rest
                pass
    finally:
        with connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_unlock(%s)", [_SYNC_LOCK_KEY])
        close_old_connections()
