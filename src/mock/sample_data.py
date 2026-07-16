"""Mock/sample data for the HouseSignal AI Streamlit demo.

This module intentionally contains no real customer data and no API keys. It is
used to make the product workflow testable before live RentCast, Supabase, and
user-uploaded documents are connected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SampleDeal:
    """One sample commercial real estate deal used across demo pages."""

    name: str
    address: str
    city: str
    state: str
    asset_type: str
    units: int
    year_built: int
    purchase_price: float
    annual_gross_income: float
    annual_operating_expenses: float
    annual_debt_service: float
    equity_invested: float
    vacancy_rate: float
    capex_reserve: float
    market_signal_score: float
    lat: float
    lon: float

    def to_agent_profile(self) -> dict[str, Any]:
        """Return fields expected by the underwriting agents."""
        return {
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "asset_type": self.asset_type,
            "units": self.units,
            "purchase_price": self.purchase_price,
            "annual_gross_income": self.annual_gross_income,
            "annual_operating_expenses": self.annual_operating_expenses,
            "annual_debt_service": self.annual_debt_service,
            "equity_invested": self.equity_invested,
            "vacancy_rate": self.vacancy_rate,
            "capex_reserve": self.capex_reserve,
            "market_signal_score": self.market_signal_score,
        }


SAMPLE_DEAL = SampleDeal(
    name="Riverbend Commons",
    address="4100 Mockingbird Ave",
    city="Sacramento",
    state="CA",
    asset_type="Garden-style multifamily",
    units=42,
    year_built=1988,
    purchase_price=7_850_000,
    annual_gross_income=982_000,
    annual_operating_expenses=412_000,
    annual_debt_service=386_000,
    equity_invested=2_355_000,
    vacancy_rate=0.064,
    capex_reserve=310_000,
    market_signal_score=61,
    lat=38.5816,
    lon=-121.4944,
)

MARKET_SNAPSHOTS: list[dict[str, Any]] = [
    {
        "city": "San Jose",
        "state": "CA",
        "lat": 37.3382,
        "lon": -121.8863,
        "market_signal": 68,
        "risk": 34,
        "zhvi_yoy": 0.047,
        "rent_yoy": 0.032,
        "latest_record_date": "2026-04-30",
        "inventory_trend": "Tight but improving",
        "takeaway": "Stronger appreciation profile, harder income yield math.",
    },
    {
        "city": "Sacramento",
        "state": "CA",
        "lat": 38.5816,
        "lon": -121.4944,
        "market_signal": 61,
        "risk": 31,
        "zhvi_yoy": 0.029,
        "rent_yoy": 0.041,
        "latest_record_date": "2026-04-30",
        "inventory_trend": "Balanced supply",
        "takeaway": "Better rent-to-price balance with moderate appreciation.",
    },
    {
        "city": "Elk Grove",
        "state": "CA",
        "lat": 38.4088,
        "lon": -121.3716,
        "market_signal": 58,
        "risk": 29,
        "zhvi_yoy": 0.025,
        "rent_yoy": 0.036,
        "latest_record_date": "Mock sample",
        "inventory_trend": "Suburban family demand",
        "takeaway": "Useful middle-market comparison for Sacramento suburbs.",
    },
]

MOCK_LISTINGS: list[dict[str, Any]] = [
    {"name": "Riverbend Commons", "city": "Sacramento", "lat": 38.5816, "lon": -121.4944, "price": 7_850_000, "units": 42, "cap_rate": 0.073, "risk": 31},
    {"name": "Almaden Eight", "city": "San Jose", "lat": 37.2431, "lon": -121.8777, "price": 6_400_000, "units": 8, "cap_rate": 0.046, "risk": 38},
    {"name": "Midtown Walkup", "city": "Sacramento", "lat": 38.5722, "lon": -121.4761, "price": 3_250_000, "units": 18, "cap_rate": 0.066, "risk": 34},
    {"name": "Elk Grove Court", "city": "Elk Grove", "lat": 38.4210, "lon": -121.3970, "price": 4_120_000, "units": 24, "cap_rate": 0.064, "risk": 29},
]

MOCK_DOCUMENTS: dict[str, str] = {
    "lease_agreement": """
Lease Agreement - Riverbend Commons
Tenant shall pay base rent of $1,875 per month. Lease term is 12 months with renewal options at market rent.
Late payment default occurs after 5 days. Assignment and sublet require landlord approval.
Tenant pays utilities directly. Landlord handles roof, structural, plumbing, and major HVAC repairs.
""".strip(),
    "rent_roll": """
Rent Roll - Riverbend Commons
Unit 101 | Tenant: Carter | Rent: $1,825 | Lease Expiration: 2027-03-31 | Status: Occupied
Unit 102 | Tenant: Nguyen | Rent: $1,910 | Lease Expiration: 2026-11-30 | Status: Occupied
Unit 103 | Tenant: Vacant | Rent: $0 | Lease Expiration: N/A | Status: Vacant
Unit 104 | Tenant: Patel | Rent: $1,795 | Lease Expiration: 2026-09-30 | Status: Occupied
Three units are below market by roughly $125 per month based on mock comp assumptions.
""".strip(),
    "offering_memorandum": """
Offering Memorandum - Riverbend Commons
Broker pro forma assumes 5.0% rent growth, 95% stabilized occupancy, and $610,000 year-three NOI.
Current in-place NOI is represented as $570,000. Asking price is $7,850,000.
Upside thesis depends on light unit renovations and Sacramento rent demand.
Buyer should verify capex assumptions, tax reassessment, insurance, and payroll expenses.
""".strip(),
    "t12_financial_statement": """
T12 Financial Statement - Riverbend Commons
Rental Income: $934,000
Other Income: $48,000
Repairs and Maintenance: $96,000
Taxes: $118,000
Insurance: $52,000
Utilities: $64,000
Management: $39,000
Net Operating Income: $570,000
One-time plumbing repair of $28,000 occurred in March.
""".strip(),
    "property_condition_report": """
Property Condition Report - Riverbend Commons
Roof has approximately 4-6 years of remaining useful life. HVAC units are mixed age with 11 units over 15 years old.
Immediate repairs include exterior stair resurfacing, parking lot sealing, and selective plumbing replacement.
Estimated near-term capex reserve: $310,000. No major foundation issues observed in mock inspection.
Life safety items are minor but should be completed before closing.
""".strip(),
}

MOCK_API_USAGE: list[dict[str, Any]] = [
    {"provider": "rentcast", "endpoint": "properties", "cache_status": "hit", "request_date": "2026-07-14", "count": 9},
    {"provider": "rentcast", "endpoint": "avm/rent/long-term", "cache_status": "hit", "request_date": "2026-07-14", "count": 6},
    {"provider": "rentcast", "endpoint": "listings/sale", "cache_status": "miss", "request_date": "2026-07-14", "count": 2},
    {"provider": "rentcast", "endpoint": "listings/sale", "cache_status": "blocked", "request_date": "2026-07-13", "count": 1},
]

AGENT_PIPELINE = [
    {"step": "Upload", "status": "Mock-ready", "detail": "Documents are uploaded or selected from bundled sample text."},
    {"step": "Classify", "status": "Connected", "detail": "Document type routes to the matching specialized agent."},
    {"step": "Retrieve", "status": "Connected", "detail": "Keyword RAG returns the most relevant chunks for the question."},
    {"step": "Analyze", "status": "Connected", "detail": "Document, financial, risk, market, and recommendation agents generate structured outputs."},
    {"step": "Store", "status": "Planned", "detail": "Supabase schema and RLS are ready for real persistence."},
]
