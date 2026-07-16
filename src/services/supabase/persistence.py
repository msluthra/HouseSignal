"""Deal/document/agent-run/recommendation persistence services."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from src.integrations.supabase_client import create_supabase_service_client
from src.services.supabase.auth import AuthUser
from src.services.supabase.config import SupabaseMode, get_supabase_runtime_config
from src.services.supabase.storage import StoredObject


@dataclass(frozen=True)
class DealRecord:
    """Persisted commercial real estate deal/property."""

    id: str
    owner_id: str
    name: str
    address: str = ""
    city: str = ""
    state: str = "CA"
    zip_code: str = ""
    asset_type: str = ""
    units: int | None = None
    purchase_price: float | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class DocumentRecord:
    """Persisted document metadata."""

    id: str
    owner_id: str
    property_id: str | None
    document_type: str
    file_name: str
    storage_path: str
    content_sha256: str
    status: str = "uploaded"
    extracted_summary: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class AgentRunRecord:
    """Persisted agent run output."""

    id: str
    owner_id: str
    agent_name: str
    property_id: str | None = None
    input_summary: dict[str, Any] = field(default_factory=dict)
    output_summary: dict[str, Any] = field(default_factory=dict)
    model_name: str | None = None
    status: str = "completed"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class RecommendationRecord:
    """Persisted recommendation snapshot."""

    id: str
    owner_id: str
    recommendation_label: str
    investment_score: float
    property_id: str | None = None
    risk_score: float | None = None
    financial_metrics: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class PersistenceService(Protocol):
    """Persistence service interface for HouseSignal AI."""

    def save_deal(self, user: AuthUser, payload: dict[str, Any]) -> DealRecord:
        """Save a deal/property record."""

    def save_document_metadata(
        self,
        user: AuthUser,
        stored_object: StoredObject,
        document_type: str,
        file_name: str,
        property_id: str | None = None,
        extracted_summary: dict[str, Any] | None = None,
    ) -> DocumentRecord:
        """Save document metadata after upload."""

    def save_agent_run(self, user: AuthUser, payload: dict[str, Any]) -> AgentRunRecord:
        """Save an agent run record."""

    def save_recommendation(self, user: AuthUser, payload: dict[str, Any]) -> RecommendationRecord:
        """Save a recommendation snapshot."""

    def list_deals(self, user: AuthUser) -> list[DealRecord]:
        """List deals owned by the current user."""


class MockPersistenceService:
    """In-memory mock persistence for local MVP development."""

    def __init__(self) -> None:
        self.deals: list[DealRecord] = []
        self.documents: list[DocumentRecord] = []
        self.agent_runs: list[AgentRunRecord] = []
        self.recommendations: list[RecommendationRecord] = []

    def save_deal(self, user: AuthUser, payload: dict[str, Any]) -> DealRecord:
        """Save a mock deal/property record."""
        record = DealRecord(
            id=str(uuid4()),
            owner_id=user.id,
            name=str(payload.get("name", "Untitled Deal")),
            address=str(payload.get("address", "")),
            city=str(payload.get("city", "")),
            state=str(payload.get("state", "CA")),
            zip_code=str(payload.get("zip_code", "")),
            asset_type=str(payload.get("asset_type", "")),
            units=payload.get("units"),
            purchase_price=payload.get("purchase_price"),
        )
        self.deals.append(record)
        return record

    def save_document_metadata(
        self,
        user: AuthUser,
        stored_object: StoredObject,
        document_type: str,
        file_name: str,
        property_id: str | None = None,
        extracted_summary: dict[str, Any] | None = None,
    ) -> DocumentRecord:
        """Save mock document metadata."""
        record = DocumentRecord(
            id=str(uuid4()),
            owner_id=user.id,
            property_id=property_id,
            document_type=document_type,
            file_name=file_name,
            storage_path=stored_object.path,
            content_sha256=stored_object.content_sha256,
            extracted_summary=extracted_summary or {},
        )
        self.documents.append(record)
        return record

    def save_agent_run(self, user: AuthUser, payload: dict[str, Any]) -> AgentRunRecord:
        """Save a mock agent run."""
        record = AgentRunRecord(
            id=str(uuid4()),
            owner_id=user.id,
            property_id=payload.get("property_id"),
            agent_name=str(payload.get("agent_name", "unknown_agent")),
            input_summary=payload.get("input_summary", {}),
            output_summary=payload.get("output_summary", {}),
            model_name=payload.get("model_name"),
            status=str(payload.get("status", "completed")),
        )
        self.agent_runs.append(record)
        return record

    def save_recommendation(self, user: AuthUser, payload: dict[str, Any]) -> RecommendationRecord:
        """Save a mock recommendation."""
        record = RecommendationRecord(
            id=str(uuid4()),
            owner_id=user.id,
            property_id=payload.get("property_id"),
            recommendation_label=str(payload.get("recommendation_label", "hold/monitor")),
            investment_score=float(payload.get("investment_score", 0.0)),
            risk_score=payload.get("risk_score"),
            financial_metrics=payload.get("financial_metrics", {}),
            assumptions=payload.get("assumptions", {}),
            evidence=payload.get("evidence", {}),
        )
        self.recommendations.append(record)
        return record

    def list_deals(self, user: AuthUser) -> list[DealRecord]:
        """List mock deals for the current user."""
        return [deal for deal in self.deals if deal.owner_id == user.id]


class SupabasePersistenceService:
    """Supabase-backed persistence service using backend service-role access."""

    def __init__(self) -> None:
        self.client = create_supabase_service_client()

    @staticmethod
    def _execute_insert(client: Any, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = client.table(table).insert(payload).execute()
        data = getattr(response, "data", None) or []
        if not data:
            raise RuntimeError(f"Supabase insert into {table} returned no data")
        return data[0]

    def save_deal(self, user: AuthUser, payload: dict[str, Any]) -> DealRecord:
        """Save deal to public.cre_properties."""
        insert_payload = {
            "owner_id": user.id,
            "name": payload.get("name", "Untitled Deal"),
            "address": payload.get("address"),
            "city": payload.get("city"),
            "state": payload.get("state", "CA"),
            "zip_code": payload.get("zip_code"),
            "asset_type": payload.get("asset_type"),
            "units": payload.get("units"),
            "purchase_price": payload.get("purchase_price"),
        }
        row = self._execute_insert(self.client, "cre_properties", insert_payload)
        return DealRecord(
            id=str(row["id"]),
            owner_id=str(row["owner_id"]),
            name=str(row["name"]),
            address=str(row.get("address") or ""),
            city=str(row.get("city") or ""),
            state=str(row.get("state") or "CA"),
            zip_code=str(row.get("zip_code") or ""),
            asset_type=str(row.get("asset_type") or ""),
            units=row.get("units"),
            purchase_price=float(row["purchase_price"]) if row.get("purchase_price") is not None else None,
            created_at=str(row.get("created_at") or datetime.now(UTC).isoformat()),
        )

    def save_document_metadata(
        self,
        user: AuthUser,
        stored_object: StoredObject,
        document_type: str,
        file_name: str,
        property_id: str | None = None,
        extracted_summary: dict[str, Any] | None = None,
    ) -> DocumentRecord:
        """Save document metadata to public.deal_documents."""
        insert_payload = {
            "owner_id": user.id,
            "property_id": property_id,
            "document_type": document_type,
            "file_name": file_name,
            "storage_path": stored_object.path,
            "content_sha256": stored_object.content_sha256,
            "extracted_summary": extracted_summary or {},
        }
        row = self._execute_insert(self.client, "deal_documents", insert_payload)
        return DocumentRecord(
            id=str(row["id"]),
            owner_id=str(row["owner_id"]),
            property_id=row.get("property_id"),
            document_type=str(row["document_type"]),
            file_name=str(row["file_name"]),
            storage_path=str(row["storage_path"]),
            content_sha256=str(row.get("content_sha256") or ""),
            status=str(row.get("status") or "uploaded"),
            extracted_summary=row.get("extracted_summary") or {},
            created_at=str(row.get("created_at") or datetime.now(UTC).isoformat()),
        )

    def save_agent_run(self, user: AuthUser, payload: dict[str, Any]) -> AgentRunRecord:
        """Save agent run to public.agent_runs."""
        insert_payload = {
            "owner_id": user.id,
            "property_id": payload.get("property_id"),
            "agent_name": payload.get("agent_name", "unknown_agent"),
            "input_summary": payload.get("input_summary", {}),
            "output_summary": payload.get("output_summary", {}),
            "model_name": payload.get("model_name"),
            "status": payload.get("status", "completed"),
        }
        row = self._execute_insert(self.client, "agent_runs", insert_payload)
        return AgentRunRecord(
            id=str(row["id"]),
            owner_id=str(row["owner_id"]),
            property_id=row.get("property_id"),
            agent_name=str(row["agent_name"]),
            input_summary=row.get("input_summary") or {},
            output_summary=row.get("output_summary") or {},
            model_name=row.get("model_name"),
            status=str(row.get("status") or "completed"),
            created_at=str(row.get("created_at") or datetime.now(UTC).isoformat()),
        )

    def save_recommendation(self, user: AuthUser, payload: dict[str, Any]) -> RecommendationRecord:
        """Save recommendation to public.cre_recommendations."""
        insert_payload = {
            "owner_id": user.id,
            "property_id": payload.get("property_id"),
            "recommendation_label": payload.get("recommendation_label", "hold/monitor"),
            "investment_score": payload.get("investment_score", 0.0),
            "risk_score": payload.get("risk_score"),
            "financial_metrics": payload.get("financial_metrics", {}),
            "assumptions": payload.get("assumptions", {}),
            "evidence": payload.get("evidence", {}),
        }
        row = self._execute_insert(self.client, "cre_recommendations", insert_payload)
        return RecommendationRecord(
            id=str(row["id"]),
            owner_id=str(row["owner_id"]),
            property_id=row.get("property_id"),
            recommendation_label=str(row["recommendation_label"]),
            investment_score=float(row["investment_score"]),
            risk_score=float(row["risk_score"]) if row.get("risk_score") is not None else None,
            financial_metrics=row.get("financial_metrics") or {},
            assumptions=row.get("assumptions") or {},
            evidence=row.get("evidence") or {},
            created_at=str(row.get("created_at") or datetime.now(UTC).isoformat()),
        )

    def list_deals(self, user: AuthUser) -> list[DealRecord]:
        """List deals from public.cre_properties for the current user."""
        response = self.client.table("cre_properties").select("*").eq("owner_id", user.id).execute()
        return [
            DealRecord(
                id=str(row["id"]),
                owner_id=str(row["owner_id"]),
                name=str(row["name"]),
                address=str(row.get("address") or ""),
                city=str(row.get("city") or ""),
                state=str(row.get("state") or "CA"),
                zip_code=str(row.get("zip_code") or ""),
                asset_type=str(row.get("asset_type") or ""),
                units=row.get("units"),
                purchase_price=float(row["purchase_price"]) if row.get("purchase_price") is not None else None,
                created_at=str(row.get("created_at") or datetime.now(UTC).isoformat()),
            )
            for row in (getattr(response, "data", None) or [])
        ]


def get_persistence_service() -> PersistenceService:
    """Return live Supabase persistence when configured; otherwise mock."""
    runtime = get_supabase_runtime_config()
    if runtime.mode == SupabaseMode.LIVE:
        return SupabasePersistenceService()
    return MockPersistenceService()


def record_to_dict(record: Any) -> dict[str, Any]:
    """Convert persistence dataclasses to dictionaries for UI/tests."""
    return asdict(record)
