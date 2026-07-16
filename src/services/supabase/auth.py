"""Auth-aware helpers for HouseSignal AI Supabase workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.integrations.supabase_client import create_supabase_user_client
from src.services.supabase.config import SupabaseMode, get_supabase_runtime_config


@dataclass(frozen=True)
class AuthUser:
    """Authenticated user context used by persistence/storage services."""

    id: str
    email: str
    role: str = "analyst"
    is_mock: bool = True


class AuthService(Protocol):
    """Auth service interface."""

    def current_user(self, access_token: str | None = None) -> AuthUser:
        """Return the current authenticated user context."""


class MockAuthService:
    """Mock auth for local MVP work when Supabase is not configured."""

    def current_user(self, access_token: str | None = None) -> AuthUser:
        """Return a deterministic mock user."""
        return AuthUser(id="00000000-0000-4000-8000-000000000001", email="demo@housesignal.ai", is_mock=True)


class SupabaseAuthService:
    """Supabase-backed auth helper.

    The service accepts an optional access token from a trusted backend context.
    Streamlit mock mode does not require one.
    """

    def current_user(self, access_token: str | None = None) -> AuthUser:
        """Fetch the current user from Supabase auth when possible."""
        if not access_token:
            raise RuntimeError("Supabase access token is required in live auth mode")
        client = create_supabase_user_client()
        user_response = client.auth.get_user(access_token)
        user = user_response.user
        return AuthUser(id=str(user.id), email=user.email or "", is_mock=False)


def get_auth_service() -> AuthService:
    """Return live auth only when Supabase is configured; otherwise mock."""
    runtime = get_supabase_runtime_config()
    if runtime.mode == SupabaseMode.LIVE:
        return SupabaseAuthService()
    return MockAuthService()
