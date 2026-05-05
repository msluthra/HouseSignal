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
    <main className="container grid" style={{ gap: 18 }}>
      <section className="card">
        <h1>ProphetAI</h1>
        <p className="subtitle">Friendly California real estate investment analysis with quick guidance for non-experts.</p>
      </section>

      <section className="card">
        <div className="label">Quick scenario buttons</div>
        <div className="row">
          {Object.entries(PRESETS).map(([name, payload]) => (
            <button key={name} className="btn" onClick={() => setForm(payload)}>
              {name}
            </button>
          ))}
        </div>
      </section>

      <section className="grid two">
        <form className="card grid" onSubmit={runAnalysis} style={{ gap: 12 }}>
          <h3 style={{ margin: 0 }}>Property Inputs</h3>
          <div>
            <div className="label">Address</div>
            <input className="input" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </div>
          <div className="grid" style={{ gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
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
          </div>
          <div className="grid" style={{ gridTemplateColumns: "repeat(2, 1fr)", gap: 10 }}>
            <div>
              <div className="label">Sqft</div>
              <input className="input" type="number" value={form.sqft} onChange={(e) => setForm({ ...form, sqft: Number(e.target.value) })} />
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
          </div>
          <button className="btn primary" type="submit" disabled={loading}>
            {loading ? "Running..." : "Run Analysis"}
          </button>
          {error ? <div style={{ color: "#b91c1c" }}>{error}</div> : null}
        </form>

        <aside className="card grid" style={{ gap: 10 }}>
          <h3 style={{ margin: 0 }}>Friendly Filters</h3>
          <div>
            <div className="label">Risk profile</div>
            <select className="input" value={riskProfile} onChange={(e) => setRiskProfile(e.target.value)}>
              <option>Conservative</option>
              <option>Balanced</option>
              <option>Aggressive</option>
            </select>
          </div>
          <p className="subtitle" style={{ margin: 0 }}>
            Selected profile: <b>{riskProfile}</b>
          </p>
          <p className="subtitle" style={{ margin: 0 }}>
            Tip: Ask questions below if terms like cap rate, yield, or downside risk are unclear.
          </p>
        </aside>
      </section>

      {result ? (
        <>
          <section className="card">
            <div className="label">Recommendation</div>
            <div className="metric" style={{ color: labelColor }}>
              {result.recommendation_label.toUpperCase()}
            </div>
          </section>

          <section className="grid four">
            <div className="card">
              <div className="label">Fair Value</div>
              <div className="metric">${result.fair_value.toLocaleString()}</div>
            </div>
            <div className="card">
              <div className="label">Expected Monthly Rent</div>
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

          <section className="grid" style={{ gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
            <div className="card">
              <div className="label">3 Month Appreciation</div>
              <div className="metric">{(result.appreciation_3m * 100).toFixed(2)}%</div>
            </div>
            <div className="card">
              <div className="label">6 Month Appreciation</div>
              <div className="metric">{(result.appreciation_6m * 100).toFixed(2)}%</div>
            </div>
            <div className="card">
              <div className="label">12 Month Appreciation</div>
              <div className="metric">{(result.appreciation_12m * 100).toFixed(2)}%</div>
            </div>
          </section>

          <section className="card grid" style={{ gap: 10 }}>
            <h3 style={{ margin: 0 }}>AI Copilot (No API Key Needed)</h3>
            <div className="row">
              <button className="btn" onClick={() => askPreset("Why this recommendation?")}>Why this recommendation?</button>
              <button className="btn" onClick={() => askPreset("What are the biggest risks?")}>What are the biggest risks?</button>
              <button className="btn" onClick={() => askPreset("Is this overpriced or discounted?")}>Is this overpriced or discounted?</button>
            </div>
            <div className="chat">
              {chat.length === 0 ? <div className="subtitle">Ask a question and I’ll explain the analysis in plain language.</div> : null}
              {chat.map((msg, idx) => (
                <div key={idx} className={`msg ${msg.role}`}>
                  <b>{msg.role === "user" ? "You" : "ProphetAI Copilot"}:</b> {msg.content}
                </div>
              ))}
            </div>
            <div className="row">
              <input className="input" style={{ flex: 1 }} value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Ask about any term or recommendation..." />
              <button className="btn primary" onClick={askCustomQuestion}>Ask</button>
            </div>
          </section>
        </>
      ) : null}
    </main>
  );
}
