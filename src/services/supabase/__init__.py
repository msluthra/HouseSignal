"""Supabase mock/live service layer for HouseSignal AI."""

from src.services.supabase.auth import AuthUser, get_auth_service
from src.services.supabase.config import SupabaseMode, SupabaseRuntimeConfig, get_supabase_runtime_config
from src.services.supabase.persistence import get_persistence_service
from src.services.supabase.storage import StoredObject, get_document_storage

__all__ = [
    "AuthUser",
    "StoredObject",
    "SupabaseMode",
    "SupabaseRuntimeConfig",
    "get_auth_service",
    "get_document_storage",
    "get_persistence_service",
    "get_supabase_runtime_config",
]
