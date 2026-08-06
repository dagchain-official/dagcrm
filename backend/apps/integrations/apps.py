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
        threading.Thread(target=_reassign_loop, daemon=True).start()
        threading.Thread(target=_payroll_loop, daemon=True).start()


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


def _reassign_loop():
    """Every 60s, reassign any lead an agent has left un-actioned past the SLA
    (default 5 min) to the next clocked-in agent, and hand out unassigned leads.
    Independent of the sync loop so the 5-minute SLA is measured tightly."""
    interval = int(os.environ.get("LEAD_REASSIGN_INTERVAL", "60"))
    time.sleep(30)
    while True:
        try:
            _run_reassign_once()
        except Exception:  # noqa: BLE001 — never let the loop die
            pass
        time.sleep(interval)


_PAYROLL_LOCK_KEY = 918273647         # payroll generation lock


def _payroll_loop():
    """On the 1st of each month, auto-generate the just-ended month's payroll
    (a payslip for every active employee) so HR never has to create them by hand.
    Checks a few times a day; generation is idempotent so re-checks are harmless."""
    interval = int(os.environ.get("PAYROLL_CHECK_INTERVAL", "21600"))  # 6h
    time.sleep(60)
    while True:
        try:
            from django.db import close_old_connections, connection
            from django.utils import timezone
            today = timezone.localdate()
            if today.day == 1:               # month just rolled over
                close_old_connections()
                with connection.cursor() as cur:
                    cur.execute("SELECT pg_try_advisory_lock(%s)", [_PAYROLL_LOCK_KEY])
                    got = cur.fetchone()[0]
                if got:
                    try:
                        from apps.hr.services import generate_payroll
                        pm = today.month - 1 or 12                       # the completed month
                        py = today.year if today.month > 1 else today.year - 1
                        generate_payroll(pm, py)
                    finally:
                        with connection.cursor() as cur:
                            cur.execute("SELECT pg_advisory_unlock(%s)", [_PAYROLL_LOCK_KEY])
                        close_old_connections()
        except Exception:  # noqa: BLE001 — never let the loop die
            pass
        time.sleep(interval)


_REASSIGN_LOCK_KEY = 918273646        # its own advisory lock, distinct from sync


def _run_reassign_once():
    """One reassignment pass, advisory-locked so only ONE gunicorn worker runs it."""
    from django.db import close_old_connections, connection

    close_old_connections()
    with connection.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s)", [_REASSIGN_LOCK_KEY])
        if not cur.fetchone()[0]:
            return
    try:
        from apps.crm.assignment import reassign_stale_leads
        reassign_stale_leads()
    finally:
        with connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_unlock(%s)", [_REASSIGN_LOCK_KEY])
        close_old_connections()


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
        # fresh platform accounts just synced — link any converted customer who
        # opened an FX Artha / DAGChain account after they converted.
        try:
            from apps.crm.linking import link_pending_conversions, sync_postsales_from_platform
            link_pending_conversions()
            sync_postsales_from_platform()   # fill sale Collected/Commission from platform
        except Exception:  # noqa: BLE001
            pass
    finally:
        with connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_unlock(%s)", [_SYNC_LOCK_KEY])
        close_old_connections()
