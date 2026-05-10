import { PredictionResult } from "./types";

const GLOSSARY: Record<string, string> = {
  "cap rate": "Cap rate is annual net operating income divided by property value. Higher can mean better cash return, often with more risk.",
  "fair value": "Fair value estimates what the property should be worth today based on local market signals.",
  appreciation: "Appreciation is expected price growth over time.",
  yield: "Rental yield is annual rent divided by purchase price.",
  "downside risk": "Downside risk is the chance this investment underperforms your expectations.",
  "strong buy": "Strong buy means the model sees strong return potential relative to risk.",
  "buy with caution": "Buy with caution means there is upside, but risk is meaningful.",
  "hold/monitor": "Hold/monitor means wait for better pricing or improved market conditions.",
  avoid: "Avoid means risk-adjusted return currently looks weak.",
};

export function quickExplain(result: PredictionResult, question: string): string {
  const q = question.toLowerCase();

  for (const [term, explanation] of Object.entries(GLOSSARY)) {
    if (q.includes(term)) {
      return explanation;
    }
  }

  if (q.includes("why") || q.includes("recommend")) {
    return `This property is labeled ${result.recommendation_label} mainly due to score (${result.investment_score.toFixed(1)}), market signal (${result.market_signal_score.toFixed(1)}), projected 12M appreciation (${(result.appreciation_12m * 100).toFixed(2)}%), and downside risk (${(result.downside_risk * 100).toFixed(1)}%).`;
  }

  if (q.includes("buy")) {
    return `Buy decision: ${result.buy_decision}. This weighs investment score, market signal, projected appreciation, yield, and downside risk.`;
  }

  if (q.includes("rent")) {
    return `Rent decision: ${result.rent_decision}. This leans most on expected rent, rental yield, and risk signals.`;
  }

  if (q.includes("sell")) {
    return `Sell decision: ${result.sell_decision}. Stronger market and investment scores usually argue against selling unless the offer is attractive.`;
  }

  if (q.includes("market signal")) {
    return `Market signal is ${result.market_signal_score.toFixed(1)}/100. It summarizes momentum-style signals such as appreciation, yield strength, valuation discount, and downside risk.`;
  }

  if (q.includes("risk")) {
    return `Downside risk is ${(result.downside_risk * 100).toFixed(1)}%. Consider financing sensitivity, local demand, and vacancy risk before deciding.`;
  }

  if (q.includes("improve") || q.includes("better")) {
    return "Common ways to improve quality are lower purchase price, higher expected rent, or stronger submarket momentum.";
  }

  if (q.includes("overpriced") || q.includes("discount")) {
    return `Estimated fair value is $${result.fair_value.toLocaleString()}. Compare this with your target purchase price to assess discount vs premium.`;
  }

  return "I can explain terms, risks, and what drove this recommendation. Try asking: Why this recommendation?";
}
