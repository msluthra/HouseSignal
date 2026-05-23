"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { quickExplain } from "../lib/copilot";
import {
  ChatMessage,
  DataCoverage,
  DataFreshness,
  MarketAnalytics,
  ModelEvaluation,
  PredictionAudit,
  PredictionResult,
  PropertyPayload,
} from "../lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type GoalMode = "Buy" | "Rent" | "Sell";

type WatchlistItem = {
  address: string;
  score: number;
  marketSignal: number;
  label: string;
};

const MARKET_PROFILES = [
  {
    market: "San Jose",
    type: "High-price tech core",
    signal: 64,
    rentYield: 3.4,
    risk: 28,
    takeaway: "Stronger appreciation story, tougher yield math.",
  },
  {
    market: "Elk Grove",
    type: "Middle-market suburb",
    signal: 58,
    rentYield: 5.1,
    risk: 22,
    takeaway: "Cleaner family-housing value and better income balance.",
  },
];

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
  const [previousResult, setPreviousResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [goalMode, setGoalMode] = useState<GoalMode>("Buy");
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [downPaymentPct, setDownPaymentPct] = useState(20);
  const [interestRate, setInterestRate] = useState(6.75);
  const [loanYears, setLoanYears] = useState(30);
  const [modelEvaluation, setModelEvaluation] = useState<ModelEvaluation | null>(null);
  const [dataCoverage, setDataCoverage] = useState<DataCoverage | null>(null);
  const [marketAnalytics, setMarketAnalytics] = useState<MarketAnalytics | null>(null);
  const [predictionAudit, setPredictionAudit] = useState<PredictionAudit | null>(null);
  const [freshness, setFreshness] = useState<DataFreshness>({
    status: "not_loaded",
    label: "Data freshness: demo estimates, no ingested market files yet",
    last_refresh_at: null,
    latest_record_dates: {},
    retention_policy: "append-only",
  });

  useEffect(() => {
    const saved = window.localStorage.getItem("housesignal-watchlist");
    if (saved) {
      setWatchlist(JSON.parse(saved) as WatchlistItem[]);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("housesignal-watchlist", JSON.stringify(watchlist));
  }, [watchlist]);

  useEffect(() => {
    async function loadDashboards() {
      try {
        const [freshnessResponse, evaluationResponse, coverageResponse, analyticsResponse, auditResponse] = await Promise.all([
          fetch(`${API_BASE}/data/freshness`),
          fetch(`${API_BASE}/models/evaluation`),
          fetch(`${API_BASE}/data/coverage`),
          fetch(`${API_BASE}/analytics/market`),
          fetch(`${API_BASE}/predictions/audit`),
        ]);

        if (freshnessResponse.ok) setFreshness((await freshnessResponse.json()) as DataFreshness);
        if (evaluationResponse.ok) setModelEvaluation((await evaluationResponse.json()) as ModelEvaluation);
        if (coverageResponse.ok) setDataCoverage((await coverageResponse.json()) as DataCoverage);
        if (analyticsResponse.ok) setMarketAnalytics((await analyticsResponse.json()) as MarketAnalytics);
        if (auditResponse.ok) setPredictionAudit((await auditResponse.json()) as PredictionAudit);
      } catch {
        setFreshness((current) => ({
          ...current,
          label: "Data freshness: backend unavailable",
        }));
      }
    }

    loadDashboards();
  }, []);

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
      setPreviousResult(result);
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

  function saveToWatchlist() {
    if (!result) return;
    const item = {
      address: result.address,
      score: result.investment_score,
      marketSignal: result.market_signal_score,
      label: result.recommendation_label,
    };
    setWatchlist((prev) => [item, ...prev.filter((saved) => saved.address !== item.address)].slice(0, 6));
  }

  function getGoalDecision() {
    if (!result) return "Run analysis";
    if (goalMode === "Buy") return result.buy_decision;
    if (goalMode === "Rent") return result.rent_decision;
    return result.sell_decision;
  }

  const monthlyPayment = useMemo(() => {
    const principal = form.list_price * (1 - downPaymentPct / 100);
    const monthlyRate = interestRate / 100 / 12;
    const months = loanYears * 12;
    if (monthlyRate === 0) return principal / months;
    return (principal * monthlyRate * (1 + monthlyRate) ** months) / ((1 + monthlyRate) ** months - 1);
  }, [downPaymentPct, form.list_price, interestRate, loanYears]);

  const rentCoverage = result ? (result.expected_monthly_rent / monthlyPayment) * 100 : 0;

  const signalTimeline = useMemo(() => {
    const current = result?.market_signal_score ?? 55;
    return [
      { label: "3mo ago", value: Math.max(0, current - 7) },
      { label: "2mo ago", value: Math.max(0, current - 4) },
      { label: "1mo ago", value: Math.max(0, current - 2) },
      { label: "Today", value: current },
    ];
  }, [result]);

  const changeSummary = useMemo(() => {
    if (!result || !previousResult) return ["Run another analysis to compare changes."];
    const deltas = [
      `Score ${result.investment_score >= previousResult.investment_score ? "rose" : "fell"} by ${Math.abs(result.investment_score - previousResult.investment_score).toFixed(1)} points.`,
      `Market signal ${result.market_signal_score >= previousResult.market_signal_score ? "improved" : "weakened"} by ${Math.abs(result.market_signal_score - previousResult.market_signal_score).toFixed(1)} points.`,
      `Downside risk changed by ${Math.abs((result.downside_risk - previousResult.downside_risk) * 100).toFixed(1)} percentage points.`,
    ];
    return deltas;
  }, [previousResult, result]);

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
                <div className="label">Goal Mode</div>
                <div className="segmented">
                  {(["Buy", "Rent", "Sell"] as GoalMode[]).map((mode) => (
                    <button
                      className={goalMode === mode ? "segment active" : "segment"}
                      key={mode}
                      onClick={() => setGoalMode(mode)}
                      type="button"
                    >
                      {mode}
                    </button>
                  ))}
                </div>
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

            <div>
              <div className="label">Risk Profile</div>
              <select className="input" value={riskProfile} onChange={(e) => setRiskProfile(e.target.value)}>
                <option>Conservative</option>
                <option>Balanced</option>
                <option>Aggressive</option>
              </select>
            </div>

            <button className="btn primary" type="submit" disabled={loading}>
              {loading ? "Running Analysis..." : "Run Analysis"}
            </button>
            {error ? <div className="error-text">{error}</div> : null}
          </form>
        </section>

        <section className="card product-dashboard">
          <div className="section-heading">
            <div>
              <div className="label">ML Readiness</div>
              <h2>Model Evaluation Dashboard</h2>
            </div>
            <span className="status-pill">{modelEvaluation?.status.replace("_", " ") ?? "loading"}</span>
          </div>
          <p className="subtitle">
            {modelEvaluation?.notes ?? "Loading model evaluation structure..."}
          </p>
          <div className="grid three">
            {(modelEvaluation?.metrics ?? []).map((metric) => (
              <div className="insight-tile" key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
                <p>{metric.helper}</p>
              </div>
            ))}
          </div>
          <div className="grid two-equal">
            <div className="mini-panel">
              <div className="label">Target + Split</div>
              <p><strong>{modelEvaluation?.target ?? "Pending"}</strong></p>
              <p>Train: {modelEvaluation?.training_window ?? "Pending"}</p>
              <p>Test: {modelEvaluation?.test_window ?? "Pending"}</p>
            </div>
            <div className="mini-panel">
              <div className="label">Baseline Comparison</div>
              {(modelEvaluation?.baseline ?? []).map((item) => (
                <p key={item.label}><strong>{item.label}:</strong> {item.value} - {item.helper}</p>
              ))}
            </div>
          </div>
        </section>

        <section className="grid two-equal">
          <div className="card">
            <div className="label">Feature Importance</div>
            <h2>What The Model Will Learn From</h2>
            <div className="importance-list">
              {(modelEvaluation?.feature_importance ?? []).map((feature) => (
                <div className="importance-row" key={feature.feature}>
                  <span>{feature.feature}</span>
                  <div className="importance-track">
                    <div className="importance-fill" style={{ width: `${feature.importance * 100}%` }} />
                  </div>
                  <strong>{Math.round(feature.importance * 100)}%</strong>
                </div>
              ))}
            </div>
          </div>
          <div className="card">
            <div className="label">Data Coverage</div>
            <h2>City Readiness</h2>
            <div className="coverage-list">
              {(dataCoverage?.cities ?? []).map((city) => (
                <div className="coverage-row" key={city.city}>
                  <div>
                    <strong>{city.city}</strong>
                    <p>{city.status}</p>
                  </div>
                  <span>{city.market_rows.toLocaleString()} rows</span>
                  <span>{city.metrics_loaded} metrics</span>
                  <span>{city.latest_record_date ?? "pending"}</span>
                </div>
              ))}
            </div>
            <p className="subtitle">Next data needed: {(dataCoverage?.missing_next ?? []).join(", ") || "loading..."}</p>
          </div>
        </section>

        <section className="grid two-equal">
          <div className="card">
            <div className="label">Market Analytics</div>
            <h2>Signal Board</h2>
            <div className="grid compact-grid">
              {(marketAnalytics?.cities ?? []).map((city) => (
                <div className="signal-card" key={city.city}>
                  <div>
                    <strong>{city.city}</strong>
                    <p>{city.takeaway}</p>
                  </div>
                  <div className="signal-score">{city.signal ? city.signal.toFixed(0) : "--"}</div>
                  <span>{city.price_momentum}</span>
                  <span>{city.buyer_leverage}</span>
                  <span>Risk: {city.risk_level}</span>
                </div>
              ))}
            </div>
            <p className="subtitle">{marketAnalytics?.methodology}</p>
          </div>
          <div className="card">
            <div className="label">Prediction Audit</div>
            <h2>How A Recommendation Is Built</h2>
            <div className="audit-list">
              {(predictionAudit?.stages ?? []).map((stage) => (
                <div className="audit-row" key={stage.step}>
                  <strong>{stage.step}</strong>
                  <p>{stage.signal}</p>
                </div>
              ))}
            </div>
            <p className="subtitle">{predictionAudit?.caveat}</p>
          </div>
        </section>

        {result ? (
          <>
            <section className="card">
              <div className="label">Recommendation</div>
              <div className="metric" style={{ color: labelColor }}>
                {result.recommendation_label.toUpperCase()}
              </div>
              <p className="subtitle">Focused decision: {goalMode} - {getGoalDecision()}</p>
              <button className="btn" onClick={saveToWatchlist}>Save To Watchlist</button>
            </section>

            <section className="grid four">
              <div className="card">
                <div className="label">Market Signal</div>
                <div className="metric">{result.market_signal_score.toFixed(1)}</div>
              </div>
              <div className="card">
                <div className="label">Buy Decision</div>
                <div className="metric decision-text">{result.buy_decision}</div>
              </div>
              <div className="card">
                <div className="label">Rent Decision</div>
                <div className="metric decision-text">{result.rent_decision}</div>
              </div>
              <div className="card">
                <div className="label">Sell Decision</div>
                <div className="metric decision-text">{result.sell_decision}</div>
              </div>
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

            <section className="grid two-equal">
              <div className="card">
                <div className="label">Rent Recommendation</div>
                <div className="metric decision-text">{result.rent_decision}</div>
                <p className="subtitle">
                  Estimated rent covers {rentCoverage.toFixed(0)}% of the modeled principal and interest payment.
                </p>
              </div>
              <div className="card">
                <div className="label">Affordability Calculator</div>
                <div className="grid three compact-grid">
                  <div>
                    <div className="label">Down %</div>
                    <input className="input" type="number" value={downPaymentPct} onChange={(e) => setDownPaymentPct(Number(e.target.value))} />
                  </div>
                  <div>
                    <div className="label">Rate %</div>
                    <input className="input" type="number" value={interestRate} onChange={(e) => setInterestRate(Number(e.target.value))} />
                  </div>
                  <div>
                    <div className="label">Years</div>
                    <input className="input" type="number" value={loanYears} onChange={(e) => setLoanYears(Number(e.target.value))} />
                  </div>
                </div>
                <p className="subtitle">Payment estimate: ${monthlyPayment.toLocaleString(undefined, { maximumFractionDigits: 0 })}/mo</p>
              </div>
            </section>

            <section className="grid two-equal">
              <div className="card">
                <div className="label">Market Signal Timeline</div>
                <div className="timeline">
                  {signalTimeline.map((point) => (
                    <div className="timeline-row" key={point.label}>
                      <span>{point.label}</span>
                      <div className="timeline-track">
                        <div className="timeline-fill" style={{ width: `${point.value}%` }} />
                      </div>
                      <strong>{point.value.toFixed(1)}</strong>
                    </div>
                  ))}
                </div>
              </div>
              <div className="card">
                <div className="label">What Changed?</div>
                {changeSummary.map((line) => (
                  <p className="subtitle" key={line}>{line}</p>
                ))}
              </div>
            </section>

            <section className="card">
              <div className="label">Market Compare</div>
              <div className="grid three">
                {MARKET_PROFILES.map((market) => (
                  <div className="compare-tile" key={market.market}>
                    <strong>{market.market}</strong>
                    <span>{market.type}</span>
                    <span>Signal: {market.signal}/100</span>
                    <span>Yield: {market.rentYield}%</span>
                    <span>Risk: {market.risk}%</span>
                    <p>{market.takeaway}</p>
                  </div>
                ))}
                <div className="compare-tile highlight">
                  <strong>This Property</strong>
                  <span>{result.address}</span>
                  <span>Signal: {result.market_signal_score.toFixed(1)}/100</span>
                  <span>Yield: {(result.rental_yield * 100).toFixed(2)}%</span>
                  <span>Risk: {(result.downside_risk * 100).toFixed(1)}%</span>
                  <p>{result.recommendation_label}</p>
                </div>
              </div>
            </section>

            <section className="card">
              <div className="label">Deal Watchlist</div>
              {watchlist.length === 0 ? (
                <p className="subtitle">No saved deals yet.</p>
              ) : (
                <div className="watchlist">
                  {watchlist.map((item) => (
                    <div className="watch-row" key={item.address}>
                      <span>{item.address}</span>
                      <strong>{item.score.toFixed(1)}</strong>
                      <span>{item.marketSignal.toFixed(1)}</span>
                      <span>{item.label}</span>
                    </div>
                  ))}
                </div>
              )}
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

      <div className="freshness-badge" aria-label="Data freshness">
        <strong>{freshness.status === "loaded" ? "Live Data" : "MVP Data"}</strong>
        <span>{freshness.label}</span>
        <em>Refresh policy: {freshness.retention_policy}</em>
      </div>
    </main>
  );
}
