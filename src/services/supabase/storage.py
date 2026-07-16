"""Storage helpers for deal document uploads."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from config.settings import settings
from src.integrations.supabase_client import create_supabase_service_client
from src.services.supabase.auth import AuthUser
from src.services.supabase.config import SupabaseMode, get_supabase_runtime_config


@dataclass(frozen=True)
class StoredObject:
    """Metadata for a stored document object."""

    bucket: str
    path: str
    size_bytes: int
    content_sha256: str
    is_mock: bool


class DocumentStorage(Protocol):
    """Storage service interface."""

    def upload_document(self, user: AuthUser, file_name: str, content: bytes) -> StoredObject:
        """Persist document bytes and return storage metadata."""


class MockDocumentStorage:
    """Local filesystem storage for mock mode."""

    def __init__(self, root: str | Path = "data/uploads/mock") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def upload_document(self, user: AuthUser, file_name: str, content: bytes) -> StoredObject:
        """Store bytes under an ignored local uploads directory."""
        digest = hashlib.sha256(content).hexdigest()
        safe_name = Path(file_name).name.replace("/", "_")
        path = self.root / user.id / f"{digest[:12]}-{safe_name}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return StoredObject(
            bucket="mock-local",
            path=str(path),
            size_bytes=len(content),
            content_sha256=digest,
            is_mock=True,
        )


class SupabaseDocumentStorage:
    """Supabase Storage implementation for backend-only uploads."""

    def upload_document(self, user: AuthUser, file_name: str, content: bytes) -> StoredObject:
        """Upload document bytes to a private Supabase bucket."""
        digest = hashlib.sha256(content).hexdigest()
        safe_name = Path(file_name).name.replace("/", "_")
        storage_path = f"{user.id}/{digest[:12]}-{safe_name}"
        client = create_supabase_service_client()
        bucket = settings.supabase_storage_bucket
        client.storage.from_(bucket).upload(storage_path, content, {"upsert": "false"})
        return StoredObject(bucket=bucket, path=storage_path, size_bytes=len(content), content_sha256=digest, is_mock=False)


def get_document_storage() -> DocumentStorage:
    """Return live storage when configured; otherwise local mock storage."""
    runtime = get_supabase_runtime_config()
    if runtime.mode == SupabaseMode.LIVE:
        return SupabaseDocumentStorage()
    return MockDocumentStorage()
