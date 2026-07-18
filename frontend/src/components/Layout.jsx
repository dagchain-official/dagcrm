import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Link } from "react-router-dom";
import {
  Menu, LogOut, Hexagon, Calendar, ChevronDown, SlidersHorizontal,
  Upload, Sun, Moon, Settings,
} from "lucide-react";
import { NAV, moduleOf } from "../config/nav";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import useActivityTracker from "../hooks/useActivityTracker";
import GlobalSearch from "./GlobalSearch";
import NotificationBell from "./NotificationBell";
import ErrorBoundary from "./ErrorBoundary";
import Tour, { GuideButton } from "./Tour";

const today = new Date().toLocaleDateString("en-GB", {
  weekday: "long", day: "numeric", month: "long", year: "numeric",
});

function Sidebar({ open }) {
  const { user, can } = useAuth();
  const isAdmin = user?.dashboard === "admin";
  const isSuper = !!user?.is_superuser;

  const visible = (it) => {
    if (it.hideForSuper && isSuper) return false; // founder doesn't mark own attendance/leave
    const mod = moduleOf(it.to);
    if (mod === null) return true; // dashboard, AI
    if (mod === "__admin__") return isAdmin; // permission matrix / integrations
    return can(mod, "view");
  };
  const groups = NAV
    .map((s) => ({ ...s, items: s.items.filter(visible) }))
    .filter((s) => s.items.length > 0);

  return (
    <aside
      className={`${open ? "w-72 translate-x-0" : "-translate-x-full"} lg:w-72 lg:translate-x-0
        fixed lg:static z-40 h-full bg-ink-0 border-r border-ink-200 transition-all duration-200 flex flex-col`}
    >
      {/* logo */}
      <div className="flex items-center gap-2.5 px-6 h-16 shrink-0">
        <div className="grid place-items-center w-9 h-9 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600">
          <Hexagon size={18} className="text-white" />
        </div>
        <span className="text-lg font-extrabold tracking-tight text-ink-900">DAGOS</span>
      </div>

      {/* nav */}
      <nav className="flex-1 px-4 py-2 space-y-5 overflow-y-auto">
        {groups.map((section) => (
          <div key={section.group}>
            <p className="px-3 mb-1.5 text-[10px] font-bold text-ink-400 uppercase tracking-widest">
              {section.group}
            </p>
            <div className="space-y-0.5">
              {section.items.map((it) => (
                <NavLink
                  key={it.to}
                  to={it.to}
                  data-tour={it.to}
                  end={it.exact}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition
                     ${isActive
                       ? "bg-brand-50 text-brand-700"
                       : "text-ink-500 hover:bg-ink-50 hover:text-ink-800"}`
                  }
                >
                  <it.icon size={17} />
                  {it.label}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* footer card */}
      <div className="p-4 shrink-0 space-y-3">
        <div className="flex items-center gap-3 p-3 rounded-2xl bg-brand-600 text-white">
          <div className="grid place-items-center w-9 h-9 rounded-xl bg-white/20 font-bold text-sm shrink-0">
            {user?.role_name?.[0] || "D"}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold leading-tight truncate">{user?.role_name || "DAGOS"}</p>
            <p className="text-[11px] text-white/60">Workspace</p>
          </div>
          <ChevronDown size={16} className="text-white/70 ml-auto" />
        </div>
        <p className="text-center text-[11px] text-ink-400">© 2026 DAGOS Inc.</p>
      </div>
    </aside>
  );
}

export default function Layout() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const { toggle, isDark } = useTheme();
  const loc = useLocation();
  useActivityTracker(!!user && !user.is_superuser); // not tracked for admin

  return (
    <div className="flex h-screen overflow-hidden">
      <ErrorBoundary silent><Tour /></ErrorBoundary>
      <Sidebar open={open} />
      {open && <div className="fixed inset-0 bg-black/30 z-30 lg:hidden" onClick={() => setOpen(false)} />}

      <div className="flex-1 flex flex-col min-w-0">
        {/* top bar */}
        <header className="h-16 bg-ink-0 border-b border-ink-200 flex items-center gap-3 px-4 lg:px-6 shrink-0">
          <button className="lg:hidden btn-ghost p-2" onClick={() => setOpen(!open)}>
            <Menu size={20} />
          </button>

          <div className="min-w-0">
            <p className="font-bold text-ink-900 leading-tight truncate">
              Welcome {user?.name?.split(" ")[0] || "back"}! <span className="hidden sm:inline">👋</span>
            </p>
            <p className="text-xs text-ink-400 truncate">Today is {today}</p>
          </div>

          <GlobalSearch />
          <div className="flex-1" />

          <GuideButton />
          <button onClick={toggle} className="btn-ghost p-2" title={isDark ? "Light mode" : "Dark mode"}>
            {isDark ? <Sun size={19} /> : <Moon size={19} />}
          </button>
          <NotificationBell />

          <div className="flex items-center gap-2 pl-3 border-l border-ink-200">
            <Link to="/profile" className="flex items-center gap-3 group">
              <div className="grid place-items-center w-9 h-9 rounded-full bg-brand-100 text-brand-700 font-bold">
                {user?.name?.[0]?.toUpperCase() || "U"}
              </div>
              <div className="text-left hidden sm:block">
                <p className="text-sm font-semibold text-ink-800 leading-tight group-hover:text-brand-700">{user?.name}</p>
                <p className="text-xs text-ink-400">{user?.role_name || "User"}</p>
              </div>
            </Link>
            <Link to="/profile" className="btn-ghost p-2 hidden sm:inline-flex" title="Settings">
              <Settings size={18} />
            </Link>
            <button onClick={logout} className="btn-ghost p-2" title="Logout">
              <LogOut size={18} />
            </button>
          </div>
        </header>

        <main key={loc.pathname} className="flex-1 overflow-y-auto p-4 lg:p-6 bg-ink-50">
          <ErrorBoundary routeKey={loc.pathname}>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
