import { useEffect, useRef } from "react";

// Run `fn` once on mount and then every `intervalMs` while the tab is visible.
// Pages use this for live auto-refresh — data updates without a manual reload.
// The latest `fn` is always used (kept in a ref) so closures stay fresh without
// resetting the timer each render.
export default function usePolling(fn, intervalMs = 2000, deps = []) {
  const saved = useRef(fn);
  saved.current = fn;

  useEffect(() => {
    let alive = true;
    const tick = () => { if (alive && !document.hidden) saved.current(); };
    tick();                                   // immediate fetch (mount / deps change)
    const id = setInterval(tick, intervalMs);
    return () => { alive = false; clearInterval(id); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, ...deps]);
}
