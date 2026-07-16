"""Tests for Supabase mock/live service boundaries."""

from __future__ import annotations

from pathlib import Path

from src.services.supabase.auth import MockAuthService
from src.services.supabase.config import SupabaseMode, get_supabase_runtime_config
from src.services.supabase.persistence import MockPersistenceService
from src.services.supabase.storage import MockDocumentStorage


SUPABASE_ENV_KEYS = [
    "SUPABASE_MODE",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
]


def clear_supabase_env(monkeypatch) -> None:
    """Clear Supabase env vars for deterministic mock-mode tests."""
    for key in SUPABASE_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_defaults_to_mock_when_credentials_are_missing(monkeypatch) -> None:
    """Missing credentials should never break local development."""
    clear_supabase_env(monkeypatch)
    runtime = get_supabase_runtime_config()
    assert runtime.mode == SupabaseMode.MOCK
    assert not runtime.live_ready


def test_placeholders_do_not_activate_live_mode(monkeypatch) -> None:
    """Placeholder env values from .env.example must not count as configured secrets."""
    monkeypatch.setenv("SUPABASE_MODE", "live")
    monkeypatch.setenv("SUPABASE_URL", "https://your-project-ref.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "your-publishable-or-anon-key")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "replace-with-service-role-key-backend-only")
    runtime = get_supabase_runtime_config()
    assert runtime.mode == SupabaseMode.MOCK
    assert not runtime.live_ready


def test_live_mode_requires_all_backend_credentials(monkeypatch) -> None:
    """Live mode should activate only when all required backend values are present."""
    monkeypatch.setenv("SUPABASE_MODE", "live")
    monkeypatch.setenv("SUPABASE_URL", "https://abc123.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key-for-tests")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "backend-key-for-tests")
    runtime = get_supabase_runtime_config()
    assert runtime.mode == SupabaseMode.LIVE
    assert runtime.live_ready


def test_mock_storage_writes_to_local_uploads(tmp_path: Path) -> None:
    """Mock storage should persist bytes locally without Supabase credentials."""
    user = MockAuthService().current_user()
    storage = MockDocumentStorage(root=tmp_path)
    stored = storage.upload_document(user, "rent_roll.csv", b"unit,rent\n101,1800")
    assert stored.is_mock
    assert stored.size_bytes > 0
    assert stored.content_sha256
    assert Path(stored.path).exists()


def test_mock_persistence_saves_core_records() -> None:
    """Mock persistence should cover deals, documents, agent runs, and recommendations."""
    user = MockAuthService().current_user()
    persistence = MockPersistenceService()
    storage = MockDocumentStorage(root=Path("/tmp/housesignal-test-uploads"))
    stored = storage.upload_document(user, "lease.txt", b"base rent default renewal")

    deal = persistence.save_deal(
        user,
        {
            "name": "Mock Deal",
            "address": "123 Demo St",
            "city": "Sacramento",
            "asset_type": "Multifamily",
            "units": 12,
            "purchase_price": 2_000_000,
        },
    )
    document = persistence.save_document_metadata(user, stored, "lease_agreement", "lease.txt", property_id=deal.id)
    agent_run = persistence.save_agent_run(
        user,
        {
            "property_id": deal.id,
            "agent_name": "lease_agreement_agent",
            "input_summary": {"question": "risks"},
            "output_summary": {"findings": ["base rent found"]},
        },
    )
    recommendation = persistence.save_recommendation(
        user,
        {
            "property_id": deal.id,
            "recommendation_label": "buy with caution",
            "investment_score": 66.5,
            "risk_score": 32.0,
        },
    )

    assert deal.owner_id == user.id
    assert document.property_id == deal.id
    assert agent_run.agent_name == "lease_agreement_agent"
    assert recommendation.investment_score == 66.5
    assert persistence.list_deals(user) == [deal]
