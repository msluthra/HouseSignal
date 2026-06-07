"""Offering memorandum agent."""

from src.agents.document_agents.base_document_agent import BaseDocumentAgent


class OfferingMemorandumAgent(BaseDocumentAgent):
    """Analyze offering memorandums for broker assumptions and deal narrative."""

    name = "offering_memorandum_agent"
    focus_terms = ("noi", "cap rate", "pro forma", "assumption", "occupancy", "rent growth", "market", "upside")
