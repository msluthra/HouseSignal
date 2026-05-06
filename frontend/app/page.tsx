"use client";

import { FormEvent, useMemo, useState } from "react";
import { quickExplain } from "../lib/copilot";
import { ChatMessage, PredictionResult, PropertyPayload } from "../lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const PRESETS: Record<string, PropertyPayload> = {
  "Starter Home": {
    address: "450 Park Ave, San Jose, CA",
    list_price: 780000,
    beds: 3,
    baths: 2,
    sqft: 1350,
    neighborhood_price_per_sqft: 560,
  },
  "Value Play": {
    address: "112 Cedar St, Sacramento, CA",
    list_price: 540000,
    beds: 3,
    baths: 2,
    sqft: 1700,
    neighborhood_price_per_sqft: 360,
  },
  "Premium Coastal": {
    address: "89 Ocean View Dr, San Diego, CA",
    list_price: 1450000,
    beds: 4,
    baths: 3,
    sqft: 2400,
    neighborhood_price_per_sqft: 720,
  },
};

export default function Page() {
  const [form, setForm] = useState<PropertyPayload>({
    address: "123 Main St, San Jose, CA",
    list_price: 850000,
    beds: 3,
    baths: 2,
    sqft: 1500,
    neighborhood_price_per_sqft: 550,
  });
  const [riskProfile, setRiskProfile] = useState("Balanced");
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [chat, setChat] = useState<ChatMessage[]>([]);

  const labelColor = useMemo(() => {
    if (!result) return "#334155";
    const label = result.recommendation_label;
    if (label === "strong buy") return "#15803d";
    if (label === "buy with caution") return "#ca8a04";
    if (label === "hold/monitor") return "#0ea5a4";
    return "#b91c1c";
  }, [result]);

  async function runAnalysis(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!response.ok) {
        throw new Error(`API error ${response.status}`);
      }
      const data = (await response.json()) as PredictionResult;
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run analysis");
    } finally {
      setLoading(false);
    }
  }

  function askPreset(question: string) {
    if (!result) return;
    const assistant = quickExplain(result, question);
    setChat((prev) => [...prev, { role: "user", content: question }, { role: "assistant", content: assistant }]);
  }

  function askCustomQuestion() {
    if (!result || !chatInput.trim()) return;
    const q = chatInput.trim();
    const assistant = quickExplain(result, q);
    setChat((prev) => [...prev, { role: "user", content: q }, { role: "assistant", content: assistant }]);
    setChatInput("");
  }

  return (
    <main className="dashboard-shell">
      <section className="main-pane">
        <header className="card hero-card">
          <h1>HouseSignal</h1>
          <p className="subtitle">Full-page California real estate investment workspace with built-in AI guidance.</p>
        </header>

        <section className="card">
          <div className="label">Quick Scenarios</div>
          <div className="row">
            {Object.entries(PRESETS).map(([name, payload]) => (
              <button key={name} className="btn" onClick={() => setForm(payload)}>
                {name}
              </button>
            ))}
          </div>
        </section>

        <section className="card">
          <form className="grid" onSubmit={runAnalysis} style={{ gap: 12 }}>
            <div className="grid two-equal">
              <div>
                <div className="label">Address</div>
                <input className="input" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
              </div>
              <div>
                <div className="label">Risk Profile</div>
                <select className="input" value={riskProfile} onChange={(e) => setRiskProfile(e.target.value)}>
                  <option>Conservative</option>
                  <option>Balanced</option>
                  <option>Aggressive</option>
                </select>
              </div>
            </div>

            <div className="grid four">
              <div>
                <div className="label">List Price ($)</div>
                <input className="input" type="number" value={form.list_price} onChange={(e) => setForm({ ...form, list_price: Number(e.target.value) })} />
              </div>
              <div>
                <div className="label">Beds</div>
                <input className="input" type="number" value={form.beds} onChange={(e) => setForm({ ...form, beds: Number(e.target.value) })} />
              </div>
              <div>
                <div className="label">Baths</div>
                <input className="input" type="number" value={form.baths} onChange={(e) => setForm({ ...form, baths: Number(e.target.value) })} />
              </div>
              <div>
                <div className="label">Sqft</div>
                <input className="input" type="number" value={form.sqft} onChange={(e) => setForm({ ...form, sqft: Number(e.target.value) })} />
              </div>
            </div>

            <div>
              <div className="label">Neighborhood Price/Sqft ($)</div>
              <input
                className="input"
                type="number"
                value={form.neighborhood_price_per_sqft}
                onChange={(e) => setForm({ ...form, neighborhood_price_per_sqft: Number(e.target.value) })}
              />
            </div>

            <button className="btn primary" type="submit" disabled={loading}>
              {loading ? "Running Analysis..." : "Run Analysis"}
            </button>
            {error ? <div className="error-text">{error}</div> : null}
          </form>
        </section>

        {result ? (
          <>
            <section className="card">
              <div className="label">Recommendation</div>
              <div className="metric" style={{ color: labelColor }}>
                {result.recommendation_label.toUpperCase()}
              </div>
              <p className="subtitle">Risk profile: {riskProfile}</p>
            </section>

            <section className="grid four">
              <div className="card">
                <div className="label">Fair Value</div>
                <div className="metric">${result.fair_value.toLocaleString()}</div>
              </div>
              <div className="card">
                <div className="label">Expected Rent</div>
                <div className="metric">${result.expected_monthly_rent.toLocaleString()}</div>
              </div>
              <div className="card">
                <div className="label">Investment Score</div>
                <div className="metric">{result.investment_score.toFixed(1)}</div>
              </div>
              <div className="card">
                <div className="label">Downside Risk</div>
                <div className="metric">{(result.downside_risk * 100).toFixed(1)}%</div>
              </div>
            </section>

            <section className="grid three">
              <div className="card">
                <div className="label">3M Appreciation</div>
                <div className="metric">{(result.appreciation_3m * 100).toFixed(2)}%</div>
              </div>
              <div className="card">
                <div className="label">6M Appreciation</div>
                <div className="metric">{(result.appreciation_6m * 100).toFixed(2)}%</div>
              </div>
              <div className="card">
                <div className="label">12M Appreciation</div>
                <div className="metric">{(result.appreciation_12m * 100).toFixed(2)}%</div>
              </div>
            </section>
          </>
        ) : (
          <section className="card">
            <p className="subtitle" style={{ margin: 0 }}>
              Run analysis to unlock full metrics and assistant explanations.
            </p>
          </section>
        )}
      </section>

      <aside className="assistant-pane">
        <div className="card assistant-card">
          <h3 style={{ margin: 0 }}>AI Assistant</h3>
          <p className="subtitle" style={{ marginBottom: 8 }}>
            Ask any real-estate term or recommendation question.
          </p>

          <div className="row" style={{ marginBottom: 8 }}>
            <button className="btn small" onClick={() => askPreset("Why this recommendation?")}>Why this rec?</button>
            <button className="btn small" onClick={() => askPreset("What are the biggest risks?")}>Top risks</button>
            <button className="btn small" onClick={() => askPreset("Is this overpriced or discounted?")}>Overpriced?</button>
          </div>

          <div className="chat">
            {chat.length === 0 ? <div className="subtitle">No messages yet. Start with a quick prompt.</div> : null}
            {chat.map((msg, idx) => (
              <div key={idx} className={`msg ${msg.role}`}>
                <b>{msg.role === "user" ? "You" : "Assistant"}:</b> {msg.content}
              </div>
            ))}
          </div>

          <div className="row" style={{ marginTop: 10 }}>
            <input
              className="input"
              style={{ flex: 1 }}
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask about score, risk, terms..."
            />
            <button className="btn primary" onClick={askCustomQuestion}>Ask</button>
          </div>
        </div>
      </aside>
    </main>
  );
}
