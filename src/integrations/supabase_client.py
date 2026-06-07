"""Supabase client factory helpers.

The service-role client is backend-only. Do not import this module in browser
code or expose service credentials through `NEXT_PUBLIC_*` variables.
"""

from __future__ import annotations

from typing import Any

from config.settings import settings
from src.security.secrets import require_secret


def create_supabase_user_client() -> Any:
    """Create a Supabase client using the publishable/anon key."""
    from supabase import create_client

    url = require_secret(settings.supabase_url, "SUPABASE_URL")
    anon_key = require_secret(settings.supabase_anon_key, "SUPABASE_ANON_KEY")
    return create_client(url, anon_key)


def create_supabase_service_client() -> Any:
    """Create a backend-only Supabase service client."""
    from supabase import create_client

    url = require_secret(settings.supabase_url, "SUPABASE_URL")
    service_key = require_secret(settings.supabase_service_role_key, "SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, service_key)
