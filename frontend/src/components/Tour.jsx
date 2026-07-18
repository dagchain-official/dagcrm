import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import Joyride, { ACTIONS, EVENTS, STATUS } from "react-joyride";
import { HelpCircle, X } from "lucide-react";
import { TOUR, pageTour } from "../config/tourSteps";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

// The sidebar overview: only walk through modules whose sidebar item is
// actually rendered (i.e. this user has permission to see it).
const availableEntries = () =>
  TOUR.filter((t) => document.querySelector(`[data-tour="${t.route}"]`));

const sidebarSteps = (entries) =>
  entries.map((t) => ({
    target: `[data-tour="${t.route}"]`, title: t.label, content: t.content,
    placement: "right", disableBeacon: true,
  }));

// A page's own feature tour: its in-page steps + a "what's next" pointer.
const pageSteps = (pt) => {
  const steps = pt.steps.map((s) => ({
    target: s.selector, title: s.title, content: s.content,
    placement: "auto", disableBeacon: true,
  }));
  if (pt.next) {
    steps.push({
      target: "body", placement: "center", disableBeacon: true,
      title: "What's next?",
      content: `You're all set on this page. Next, head to ${pt.next.label} — open it from the sidebar.`,
    });
  }
  return steps;
};

export default function Tour() {
  const { user, refreshUser } = useAuth();
  const loc = useLocation();
  const [run, setRun] = useState(false);
  const [steps, setSteps] = useState([]);
  const [picker, setPicker] = useState(null); // { mode, entries, selected:Set }
  const firstRun = useRef(false);             // is the active tour the one-time onboarding?
  const started = useRef(false);

  const isAdmin = user?.dashboard === "admin";

  const persist = useCallback((routes) => {
    api.post("/auth/onboarding/", { onboarded: true, modules: routes }).catch(() => {});
    refreshUser?.();
  }, [refreshUser]);

  const startOverview = useCallback((entries, isFirst = false) => {
    const list = entries.length ? entries : availableEntries();
    firstRun.current = isFirst;
    setSteps(sidebarSteps(list));
    setRun(true);
  }, []);

  const startPage = useCallback((pt) => {
    firstRun.current = false;
    setSteps(pageSteps(pt));
    setRun(true);
  }, []);

  // First-run onboarding: once per user. Admins pick modules first.
  useEffect(() => {
    if (!user || user.onboarded || started.current) return;
    started.current = true;
    const t = setTimeout(() => {
      const entries = availableEntries();
      if (!entries.length) return;
      if (isAdmin) setPicker({ mode: "first", entries, selected: new Set(entries.map((e) => e.route)) });
      else startOverview(entries, true);
    }, 900);
    return () => clearTimeout(t);
  }, [user, isAdmin, startOverview]);

  // "?" Help button: tour the CURRENT page if it has one, else the overview.
  useEffect(() => {
    const open = () => {
      const pt = pageTour(loc.pathname);
      if (pt) startPage(pt);
      else setPicker({ mode: "guide", entries: availableEntries(), selected: new Set(availableEntries().map((e) => e.route)) });
    };
    window.addEventListener("dagos:open-guide", open);
    return () => window.removeEventListener("dagos:open-guide", open);
  }, [loc.pathname, startPage]);

  const onJoyride = useCallback((data) => {
    const { action, type, step, status } = data;
    if ([STATUS.FINISHED, STATUS.SKIPPED].includes(status) || action === ACTIONS.CLOSE) {
      setRun(false);
      if (firstRun.current && !user?.onboarded) persist(steps.map((s) => s.target));
      firstRun.current = false;
      return;
    }
    // Bring the target into view (the sidebar scrolls independently).
    if (type === EVENTS.STEP_BEFORE && step?.target && step.target !== "body") {
      const el = document.querySelector(step.target);
      if (el) el.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }, [user, steps, persist]);

  const confirmPicker = () => {
    const chosen = picker.entries.filter((e) => picker.selected.has(e.route));
    const wasFirst = picker.mode === "first";
    setPicker(null);
    if (chosen.length) startOverview(chosen, wasFirst);
    else if (wasFirst) persist([]);
  };

  const skipAll = () => {
    const wasFirst = picker?.mode === "first";
    setPicker(null);
    if (wasFirst) persist([]);
  };

  const toggle = (route) =>
    setPicker((p) => {
      const s = new Set(p.selected);
      s.has(route) ? s.delete(route) : s.add(route);
      return { ...p, selected: s };
    });

  return (
    <>
      {run && steps.length > 0 && (
      <Joyride
        steps={steps}
        run={run}
        continuous
        showProgress
        showSkipButton
        scrollToFirstStep
        disableScrollParentFix
        spotlightPadding={6}
        callback={onJoyride}
        locale={{ back: "Back", close: "Close", last: "Finish", next: "Next", skip: "Skip Tour" }}
        styles={{
          options: { primaryColor: "#6366f1", zIndex: 10000, arrowColor: "#fff", width: 340 },
          tooltipTitle: { fontWeight: 800, fontSize: 16 },
          tooltipContent: { textAlign: "left", fontSize: 14, color: "#475569" },
        }}
      />
      )}

      {picker && (
        <div className="fixed inset-0 z-[9999] grid place-items-center bg-black/40 p-4">
          <div className="card w-full max-w-lg p-6 max-h-[85vh] flex flex-col">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-extrabold text-ink-900">
                  {picker.mode === "first" ? "Welcome! 👋 Let's take a quick tour" : "Guided Tour"}
                </h2>
                <p className="text-sm text-ink-400 mt-0.5">
                  Choose the modules you'd like a walkthrough of, then start the tour.
                </p>
              </div>
              <button className="btn-ghost p-1.5" onClick={skipAll}><X size={18} /></button>
            </div>

            <div className="mt-4 grid sm:grid-cols-2 gap-2 overflow-y-auto">
              {picker.entries.map((e) => {
                const on = picker.selected.has(e.route);
                return (
                  <label key={e.route}
                    className={`flex items-start gap-2.5 p-3 rounded-xl border cursor-pointer transition
                      ${on ? "border-brand-300 bg-brand-50" : "border-ink-200 hover:border-ink-300"}`}>
                    <input type="checkbox" className="mt-0.5" checked={on} onChange={() => toggle(e.route)} />
                    <span className="text-sm font-semibold text-ink-800">{e.label}</span>
                  </label>
                );
              })}
            </div>

            <div className="flex items-center justify-between gap-3 mt-5">
              <button className="text-sm font-semibold text-ink-400 hover:text-ink-600" onClick={skipAll}>
                Skip for now
              </button>
              <button className="btn-primary" onClick={confirmPicker} disabled={picker.selected.size === 0}>
                Start Tour ({picker.selected.size})
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Top-bar Help button — tours the current page (or opens the overview).
export function GuideButton() {
  return (
    <button
      className="btn-ghost p-2"
      title="Help & tour this page"
      onClick={() => window.dispatchEvent(new CustomEvent("dagos:open-guide"))}
    >
      <HelpCircle size={19} />
    </button>
  );
}
