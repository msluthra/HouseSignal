"""T12 financial statement agent."""

from src.agents.document_agents.base_document_agent import BaseDocumentAgent


class T12FinancialStatementAgent(BaseDocumentAgent):
    """Analyze T12 statements for revenue, expenses, and NOI quality."""

    name = "t12_financial_statement_agent"
    focus_terms = ("income", "revenue", "expense", "noi", "repair", "tax", "insurance", "utility", "management")
