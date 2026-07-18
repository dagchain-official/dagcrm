import { useEffect, useRef, useState } from "react";
import { Sparkles, Send, Gauge } from "lucide-react";
import api, { ai } from "../api/client";

export default function AIAssistant() {
  const [messages, setMessages] = useState([
    { role: "ai", text: "Hi! I'm your DAGOS assistant — ask me anything about your data: leads, revenue, pipeline, proposals, tickets, employees, expenses… Try \"summary\" for a quick snapshot." },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const endRef = useRef(null);

  // lead scorer
  const [lead, setLead] = useState({ source: "Referral", status: "new", activity_count: 2, email: "x@y.com", phone: "123" });
  const [score, setScore] = useState(null);

  // NOTE: must be a block body — an implicit arrow return would hand React the
  // scrollIntoView() result as the effect's "cleanup", and React calls that on
  // unmount → "c2 is not a function" crash when leaving this page.
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async (preset) => {
    const text = (preset ?? input).trim();
    if (!text) return;
    setMessages((m) => [...m, { role: "me", text }]);
    setInput("");
    setSending(true);
    try {
      // hits the live CRM database (role-scoped) for a real, grounded answer
      const { data } = await api.post("/ai/ask/", { message: text });
      setMessages((m) => [...m, { role: "ai", text: data.reply }]);
    } catch {
      setMessages((m) => [...m, { role: "ai", text: "Couldn't reach the server. Please try again." }]);
    } finally {
      setSending(false);
    }
  };

  const runScore = async () => {
    const { data } = await ai.post("/score/lead", { ...lead, activity_count: Number(lead.activity_count) });
    setScore(data);
  };

  const gradeColor = { A: "text-emerald-600", B: "text-brand-600", C: "text-amber-600", D: "text-rose-600" };

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <Sparkles className="text-brand-600" />
        <h1 className="text-2xl font-extrabold text-ink-900">AI Assistant</h1>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* chat */}
        <div className="card flex flex-col lg:col-span-2 h-[70vh]">
          <div className="flex-1 overflow-y-auto p-5 space-y-3">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "me" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm whitespace-pre-line ${
                  m.role === "me" ? "bg-brand-600 text-white rounded-br-sm" : "bg-ink-100 text-ink-800 rounded-bl-sm"
                }`}>
                  {m.text}
                </div>
              </div>
            ))}
            <div ref={endRef} />
          </div>
          <div className="px-3 pt-2 flex flex-wrap gap-2">
            {["summary", "Lead conversion rate", "Revenue by business", "Open tickets by priority", "Proposals sent vs accepted"].map((s) => (
              <button key={s} onClick={() => send(s)} disabled={sending}
                className="text-xs px-2.5 py-1 rounded-full bg-ink-100 text-ink-600 hover:bg-brand-50 hover:text-brand-700">
                {s}
              </button>
            ))}
          </div>
          <div className="p-3 border-t border-ink-200 flex gap-2">
            <input
              className="input"
              placeholder="Ask anything about your data…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
            />
            <button className="btn-primary" onClick={() => send()} disabled={sending}>
              <Send size={16} />
            </button>
          </div>
        </div>

        {/* lead scorer */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Gauge size={18} className="text-brand-600" />
            <h3 className="font-bold text-ink-900">Lead Scorer</h3>
          </div>
          <div className="space-y-3">
            <div>
              <label className="label">Source</label>
              <select className="input" value={lead.source} onChange={(e) => setLead({ ...lead, source: e.target.value })}>
                {["Referral", "Website", "WhatsApp", "Meta Ads", "Google Ads", "Telegram", "CSV"].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Status</label>
              <select className="input" value={lead.status} onChange={(e) => setLead({ ...lead, status: e.target.value })}>
                {["new", "contacted", "qualified", "converted", "lost"].map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Activity count</label>
              <input className="input" type="number" value={lead.activity_count}
                onChange={(e) => setLead({ ...lead, activity_count: e.target.value })} />
            </div>
            <button className="btn-primary w-full" onClick={runScore}>Score Lead</button>
          </div>

          {score && (
            <div className="mt-5 p-4 rounded-xl bg-ink-50 border border-ink-100 text-center">
              <p className="text-4xl font-extrabold text-ink-900 tabular-nums">{score.score}</p>
              <p className={`font-bold ${gradeColor[score.grade]}`}>Grade {score.grade}</p>
              <p className="text-xs text-ink-500 mt-2">{score.recommended_action}</p>
              <ul className="text-left text-xs text-ink-500 mt-3 space-y-1">
                {score.reasons.map((r, i) => <li key={i}>• {r}</li>)}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
