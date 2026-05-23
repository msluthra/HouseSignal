export type PropertyPayload = {
  address: string;
  list_price: number;
  beds: number;
  baths: number;
  sqft: number;
  neighborhood_price_per_sqft: number;
};

export type PredictionResult = {
  address: string;
  fair_value: number;
  appreciation_3m: number;
  appreciation_6m: number;
  appreciation_12m: number;
  expected_monthly_rent: number;
  rental_yield: number;
  downside_risk: number;
  investment_score: number;
  market_signal_score: number;
  recommendation_label: string;
  buy_decision: string;
  rent_decision: string;
  sell_decision: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type DataFreshness = {
  status: string;
  label: string;
  last_refresh_at: string | null;
  latest_record_dates: Record<string, string | null>;
  retention_policy: string;
};

export type ModelEvaluation = {
  status: string;
  target: string;
  model_name: string;
  training_window: string;
  test_window: string;
  last_trained_at: string | null;
  metrics: { label: string; value: string; helper: string }[];
  baseline: { label: string; value: string; helper: string }[];
  feature_importance: { feature: string; importance: number }[];
  notes: string;
};

export type DataCoverage = {
  retention_policy: string;
  cities: {
    city: string;
    market_rows: number;
    metrics_loaded: number;
    latest_record_date: string | null;
    status: string;
  }[];
  missing_next: string[];
};

export type MarketAnalytics = {
  cities: {
    city: string;
    signal: number;
    price_momentum: string;
    buyer_leverage: string;
    risk_level: string;
    takeaway: string;
  }[];
  methodology: string;
};

export type PredictionAudit = {
  stages: { step: string; signal: string }[];
  caveat: string;
};
