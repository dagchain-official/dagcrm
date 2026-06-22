import { useEffect, useRef } from "react";
import api from "../api/client";

// Sends a heartbeat every minute while the app is open. The backend
// accumulates active vs idle minutes for today's EmployeeActivity.
// "active" = the page is visible AND the user interacted in the last minute.
export default function useActivityTracker(enabled) {
  const activeRef = useRef(false);

  useEffect(() => {
    if (!enabled) return;

    const markActive = () => (activeRef.current = true);
    const events = ["mousemove", "mousedown", "keydown", "scroll", "touchstart"];
    events.forEach((e) => window.addEventListener(e, markActive, { passive: true }));

    const tick = () => {
      const active = activeRef.current && document.visibilityState === "visible";
      activeRef.current = false;
      api.post("/activity/heartbeat/", { active }).catch(() => {});
    };
    const id = setInterval(tick, 60000); // every 60s

    return () => {
      clearInterval(id);
      events.forEach((e) => window.removeEventListener(e, markActive));
    };
  }, [enabled]);
}
