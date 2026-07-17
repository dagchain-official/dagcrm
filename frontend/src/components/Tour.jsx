import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Joyride, { ACTIONS, EVENTS, STATUS } from "react-joyride";
import { HelpCircle, X } from "lucide-react";
import { TOUR } from "../config/tourSteps";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

// Only walk through modules whose sidebar item is actually rendered (i.e. this
// user has permission to see it).
const availableEntries = () =>
  TOUR.filter((t) => document.querySelector(`[data-tour="${t.route}"]`));

// Flatten entries into Joyride steps. Each module contributes one sidebar step
// plus any in-page steps. In-page steps carry `_route` so the tour can navigate
// into that module's page before showing them.
const buildSteps = (entries) => {
  const out = [];
  entries.forEach((e) => {
    out.push({
      target: `[data-tour="${e.route}"]`, title: e.label, content: e.content,
      placement: "right", disableBeacon: true, _route: null,
    });
    (e.inPage || []).forEach((s) => {
      out.push({
        target: s.selector, title: s.title, content: s.content,
        placement: "auto", disableBeacon: true, _route: e.route,
      });
    });
  });
  return out;
};

// Poll for an element (a page may still be loading its data), then continue.
const waitForEl = (selector, cb, tries = 0) => {
  if (document.querySelector(selector) || tries > 50) return cb();
  setTimeout(() => waitForEl(selector, cb, tries + 1), 100);
};

export default function Tour() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const loc = useLocation();
  const [run, setRun] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [steps, setSteps] = useState([]);
  const [picker, setPicker] = useState(null); // { mode: "first" | "guide", entries, selected:Set }
  const started = useRef(false);

  const isAdmin = user?.dashboard === "admin";

  const persist = useCallback((routes) => {
    api.post("/auth/onboarding/", { onboarded: true, modules: routes }).catch(() => {});
    refreshUser?.();
  }, [refreshUser]);

  const finish = useCallback(() => {
    setRun(false);
    setStepIndex(0);
    if (!user?.onboarded) persist(steps.filter((s) => !s._route).map((s) => s.target));
  }, [user, steps, persist]);

  const startTour = useCallback((entries) => {
    const list = entries.length ? entries : availableEntries();
    setSteps(buildSteps(list));
    setStepIndex(0);
    setRun(true);
  }, []);

  // First-run: once per user. Admin picks modules first; everyone else auto-runs.
  useEffect(() => {
    if (!user || user.onboarded || started.current) return;
    started.current = true;
    const t = setTimeout(() => {
      const entries = availableEntries();
      if (!entries.length) return;
      if (isAdmin) setPicker({ mode: "first", entries, selected: new Set(entries.map((e) => e.route)) });
      else startTour(entries);
    }, 900);
    return () => clearTimeout(t);
  }, [user, isAdmin, startTour]);

  // Manual re-trigger from the "Guide" button (top bar).
  useEffect(() => {
    const open = () => {
      const entries = availableEntries();
      setPicker({ mode: "guide", entries, selected: new Set(entries.map((e) => e.route)) });
    };
    window.addEventListener("dagos:open-guide", open);
    return () => window.removeEventListener("dagos:open-guide", open);
  }, []);

  const onJoyride = useCallback((data) => {
    const { action, index, type, step, status } = data;

    if ([STATUS.FINISHED, STATUS.SKIPPED].includes(status) || action === ACTIONS.CLOSE) {
      finish();
      return;
    }

    // Bring the current target into view (the sidebar scrolls independently).
    if (type === EVENTS.STEP_BEFORE && step?.target) {
      const el = document.querySelector(step.target);
      if (el) el.scrollIntoView({ block: "center", behavior: "smooth" });
    }

    // Advance / go back — navigate into the page first if the next step lives there.
    if (type === EVENTS.STEP_AFTER || type === EVENTS.TARGET_NOT_FOUND) {
      const nextIndex = index + (action === ACTIONS.PREV ? -1 : 1);
      const next = steps[nextIndex];
      if (!next) { finish(); return; }
      if (next._route && loc.pathname !== next._route) {
        setRun(false);
        navigate(next._route);
        waitForEl(next.target, () => { setStepIndex(nextIndex); setRun(true); });
      } else {
        setStepIndex(nextIndex);
      }
    }
  }, [steps, loc.pathname, navigate, finish]);

  const confirmPicker = () => {
    const chosen = picker.entries.filter((e) => picker.selected.has(e.route));
    const wasFirst = picker.mode === "first";
    setPicker(null);
    if (chosen.length) startTour(chosen);
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
      <Joyride
        steps={steps}
        run={run}
        stepIndex={stepIndex}
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

// Top-bar button that re-opens the guide any time.
export function GuideButton() {
  return (
    <button
      className="btn-ghost p-2"
      title="Guided tour"
      onClick={() => window.dispatchEvent(new CustomEvent("dagos:open-guide"))}
    >
      <HelpCircle size={19} />
    </button>
  );
}
