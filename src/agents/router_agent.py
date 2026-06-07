"""Router agent for dispatching tasks to specialized agents."""

from __future__ import annotations

from src.agents.base import Agent, AgentContext, AgentResult
from src.agents.document_agents import (
    LeaseAgreementAgent,
    OfferingMemorandumAgent,
    PropertyConditionReportAgent,
    RentRollAgent,
    T12FinancialStatementAgent,
)
from src.agents.financial_analysis_agent import FinancialAnalysisAgent
from src.agents.market_data_agent import MarketDataAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.risk_analysis_agent import RiskAnalysisAgent
from src.rag.document_types import DocumentType


class RouterAgent:
    """Route requests to the correct HouseSignal AI agent."""

    name = "router_agent"

    def __init__(self) -> None:
        self.agents: dict[str, Agent] = {
            DocumentType.LEASE_AGREEMENT.value: LeaseAgreementAgent(),
            DocumentType.RENT_ROLL.value: RentRollAgent(),
            DocumentType.OFFERING_MEMORANDUM.value: OfferingMemorandumAgent(),
            DocumentType.T12_FINANCIAL_STATEMENT.value: T12FinancialStatementAgent(),
            DocumentType.PROPERTY_CONDITION_REPORT.value: PropertyConditionReportAgent(),
            "financial": FinancialAnalysisAgent(),
            "risk": RiskAnalysisAgent(),
            "market": MarketDataAgent(),
            "recommendation": RecommendationAgent(),
        }

    def route(self, task: str) -> Agent:
        """Select an agent based on a document type or task keyword."""
        normalized = task.lower().strip().replace(" ", "_")
        if normalized in self.agents:
            return self.agents[normalized]
        if "risk" in normalized:
            return self.agents["risk"]
        if "market" in normalized:
            return self.agents["market"]
        if "recommend" in normalized:
            return self.agents["recommendation"]
        if "financial" in normalized or "underwriting" in normalized:
            return self.agents["financial"]
        return self.agents["recommendation"]

    def run(self, task: str, context: AgentContext) -> AgentResult:
        """Dispatch to a specialized agent."""
        return self.route(task).run(context)
