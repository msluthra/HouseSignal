"""Utilities for normalizing geographic identifiers."""

from __future__ import annotations

import pandas as pd


def normalize_california_geo(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize city/state/zip formatting for downstream joins."""
    normalized = df.copy()
    for col in ("city", "state", "zip_code"):
        if col not in normalized.columns:
            normalized[col] = ""
    normalized["city"] = normalized["city"].astype(str).str.strip().str.title()
    normalized["state"] = normalized["state"].astype(str).str.strip().str.upper().replace("", "CA")
    normalized["zip_code"] = normalized["zip_code"].astype(str).str.extract(r"(\d{5})", expand=False).fillna("00000")
    return normalized
