"""Market data agent for HouseSignal AI."""

from __future__ import annotations

from src.agents.base import AgentContext, AgentResult


class MarketDataAgent:
    """Summarize market data snapshots for a target city/submarket."""

    name = "market_data_agent"

    def run(self, context: AgentContext) -> AgentResult:
        """Return market findings from supplied snapshot data."""
        market = context.market_snapshot
        city = str(market.get("city", context.property_profile.get("city", "target market")))
        latest_date = str(market.get("latest_record_date", "unknown"))
        zhvi_yoy = market.get("zhvi_yoy")
        rent_yoy = market.get("rent_yoy")

        findings = [f"Market reviewed: {city}", f"Latest market data date: {latest_date}"]
        if zhvi_yoy is not None:
            findings.append(f"Home value YoY trend: {float(zhvi_yoy) * 100:.2f}%")
        if rent_yoy is not None:
            findings.append(f"Rent YoY trend: {float(rent_yoy) * 100:.2f}%")

        risks = []
        if zhvi_yoy is not None and float(zhvi_yoy) < 0:
            risks.append("Home value trend is negative in the supplied market snapshot.")
        if rent_yoy is not None and float(rent_yoy) < 0:
            risks.append("Rent trend is negative in the supplied market snapshot.")

        return AgentResult(
            agent_name=self.name,
            summary="Summarized available market snapshot data.",
            findings=findings,
            risks=risks,
            confidence=0.65 if len(market) > 1 else 0.35,
        )
