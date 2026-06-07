"""Security guardrail tests for HouseSignal AI."""

from __future__ import annotations

from pathlib import Path

from src.utils.security import BACKEND_ONLY_SECRET_NAMES, contains_secret_value, missing_required_keys, public_service_status

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".next",
    "__pycache__",
    "data",
}
EXCLUDED_SUFFIXES = {".pyc", ".db", ".sqlite3", ".parquet", ".joblib", ".png", ".jpg", ".jpeg", ".pdf"}
SCANNED_SUFFIXES = {".py", ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".sql", ".tsx", ".ts", ".css", ".example"}
UI_PATH_PARTS = {"app", "frontend"}


def iter_repo_text_files() -> list[Path]:
    """Return source/config files that are safe and useful to scan."""
    files: list[Path] = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = set(path.relative_to(PROJECT_ROOT).parts)
        if relative_parts & EXCLUDED_DIRS:
            continue
        if path.name == ".env":
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        if path.name == ".env.example" or path.suffix in SCANNED_SUFFIXES or path.name in {"Dockerfile", ".gitignore"}:
            files.append(path)
    return files


def test_no_secret_looking_values_are_hardcoded() -> None:
    """Prevent accidental commits of real-looking API keys/JWTs."""
    offenders: list[str] = []
    for path in iter_repo_text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if contains_secret_value(text):
            offenders.append(str(path.relative_to(PROJECT_ROOT)))
    assert offenders == []


def test_env_example_uses_placeholders_only() -> None:
    """Ensure env docs contain placeholders, not real secret-looking values."""
    env_example = PROJECT_ROOT / ".env.example"
    text = env_example.read_text(encoding="utf-8")
    assert "RENTCAST_API_KEY=replace-with-rentcast-key" in text
    assert "OPENAI_API_KEY=replace-with-openai-key" in text
    assert "SUPABASE_SERVICE_ROLE_KEY=replace-with-service-role-key-backend-only" in text
    assert not contains_secret_value(text)


def test_backend_only_secret_names_are_not_in_ui_or_frontend_code() -> None:
    """Backend-only env var names should not appear in Streamlit UI or browser code."""
    offenders: list[str] = []
    for base in [PROJECT_ROOT / "app", PROJECT_ROOT / "frontend"]:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".tsx", ".ts", ".css", ".md"}:
                continue
            if set(path.relative_to(PROJECT_ROOT).parts) & EXCLUDED_DIRS:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for secret_name in BACKEND_ONLY_SECRET_NAMES:
                if secret_name in text:
                    offenders.append(f"{path.relative_to(PROJECT_ROOT)} contains {secret_name}")
    assert offenders == []


def test_security_helpers_do_not_return_secret_values() -> None:
    """Validation helpers return names/statuses, never provided secret values."""
    env = {
        "OPENAI_API_KEY": "configured-openai-placeholder",
        "RENTCAST_API_KEY": "configured-rentcast-placeholder",
    }
    assert missing_required_keys(env, ["OPENAI_API_KEY", "SUPABASE_SERVICE_ROLE_KEY"]) == ["SUPABASE_SERVICE_ROLE_KEY"]
    statuses = public_service_status(env)
    serialized = " ".join(f"{item.label}:{item.configured}" for item in statuses)
    assert "configured-openai-placeholder" not in serialized
    assert "configured-rentcast-placeholder" not in serialized
    assert "OPENAI_API_KEY" not in serialized
    assert "RENTCAST_API_KEY" not in serialized
    assert "SUPABASE_SERVICE_ROLE_KEY" not in serialized
