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
  recommendation_label: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};
