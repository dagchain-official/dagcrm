import { Component } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("Render error:", error, info);
  }

  // reset when navigating to a different page
  componentDidUpdate(prev) {
    if (prev.routeKey !== this.props.routeKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  render() {
    if (this.state.error) {
      // Non-essential UI (e.g. the product tour) can fail without taking the
      // whole app down — render nothing instead of a big error card.
      if (this.props.silent) return this.props.fallback ?? null;
      return (
        <div className="grid place-items-center min-h-[60vh] text-center p-6">
          <div className="card p-8 max-w-md">
            <div className="grid place-items-center w-14 h-14 rounded-2xl bg-rose-50 text-rose-500 mx-auto">
              <AlertTriangle size={26} />
            </div>
            <h2 className="text-xl font-extrabold text-ink-900 mt-4">Something went wrong</h2>
            <p className="text-sm text-ink-500 mt-1">
              Something went wrong on this page. Please reload and try again.
            </p>
            {this.state.error?.message && (
              <p className="text-[11px] text-rose-500 mt-3 font-mono break-words bg-rose-50 rounded-lg p-2">
                {String(this.state.error.message).slice(0, 300)}
              </p>
            )}
            <button className="btn-primary mt-5 mx-auto" onClick={() => window.location.reload()}>
              <RefreshCw size={16} /> Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
