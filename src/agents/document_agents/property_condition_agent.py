"""Property condition report agent."""

from src.agents.document_agents.base_document_agent import BaseDocumentAgent


class PropertyConditionReportAgent(BaseDocumentAgent):
    """Analyze property condition reports for capex and physical risk."""

    name = "property_condition_report_agent"
    focus_terms = ("repair", "deferred", "roof", "hvac", "plumbing", "electrical", "foundation", "life safety", "capex")
