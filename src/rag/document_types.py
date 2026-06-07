"""Supported document types for HouseSignal AI RAG."""

from __future__ import annotations

from enum import Enum


class DocumentType(str, Enum):
    """Commercial real estate document types supported by specialized agents."""

    LEASE_AGREEMENT = "lease_agreement"
    RENT_ROLL = "rent_roll"
    OFFERING_MEMORANDUM = "offering_memorandum"
    T12_FINANCIAL_STATEMENT = "t12_financial_statement"
    PROPERTY_CONDITION_REPORT = "property_condition_report"


DOCUMENT_TYPE_LABELS = {
    DocumentType.LEASE_AGREEMENT: "Lease Agreement",
    DocumentType.RENT_ROLL: "Rent Roll",
    DocumentType.OFFERING_MEMORANDUM: "Offering Memorandum",
    DocumentType.T12_FINANCIAL_STATEMENT: "T12 Financial Statement",
    DocumentType.PROPERTY_CONDITION_REPORT: "Property Condition Report",
}
