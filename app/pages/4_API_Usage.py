"""API usage and cache dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from app.ui import apply_theme, hero, status_step
from config.settings import settings
from src.mock.sample_data import MOCK_API_USAGE
from src.services.usage_reporting import load_api_usage_frame

try:
    import plotly.express as px
except ImportError:  # pragma: no cover - optional chart dependency fallback.
    px = None

try:
    from st_aggrid import AgGrid
except ImportError:  # pragma: no cover - optional UI dependency fallback.
    AgGrid = None

st.set_page_config(page_title="HouseSignal AI | API Usage", layout="wide")
apply_theme()
hero(
    "API Usage + Cache",
    "Monitor the cache-first API workflow that protects free-tier RentCast usage. This page uses mock rows when no local API calls have been logged yet.",
    pills=["Backend-only keys", "Cache-first", "Daily limits", "No secrets shown"],
)

usage = load_api_usage_frame()
using_mock = usage.empty
if using_mock:
    usage = pd.DataFrame(MOCK_API_USAGE)
else:
    usage = usage.assign(count=1)

misses_today = int(usage[(usage["provider"] == "rentcast") & (usage["cache_status"] == "miss")]["count"].sum())
hits = int(usage[usage["cache_status"] == "hit"]["count"].sum())
blocked = int(usage[usage["cache_status"] == "blocked"]["count"].sum())
remaining = max(settings.rentcast_daily_limit - misses_today, 0)

k1, k2, k3, k4 = st.columns(4)
k1.metric("RentCast Daily Limit", settings.rentcast_daily_limit)
k2.metric("Estimated Calls Used", misses_today)
k3.metric("Estimated Remaining", remaining)
k4.metric("Cache Hits", hits)

if using_mock:
    st.info("Showing mock API usage because no local API usage logs exist yet.")
else:
    st.success("Showing local API usage logs from the backend cache database.")

left, right = st.columns([1.15, 1])
with left:
    st.subheader("Usage by Cache Status")
    summary = usage.groupby(["provider", "cache_status"], as_index=False)["count"].sum()
    if px:
        fig = px.bar(
            summary,
            x="cache_status",
            y="count",
            color="provider",
            text="count",
            color_discrete_sequence=["#0f766e", "#b45309", "#2563eb"],
        )
        fig.update_layout(height=360, margin=dict(l=20, r=20, t=35, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(summary.pivot_table(index="cache_status", columns="provider", values="count", fill_value=0))

with right:
    st.subheader("Governance Flow")
    status_step("1. Normalize request", "Required", "Address, endpoint, and params become a stable non-secret cache key.")
    status_step("2. Check cache", "Required", "Cached responses are returned before any external request is attempted.")
    status_step("3. Enforce daily cap", "Required", "Misses are blocked once the configured daily RentCast limit is reached.")
    status_step("4. Log metadata", "Required", "Only provider, endpoint, cache status, and dates are logged. API keys are never logged.")

st.subheader("Usage Rows")
if AgGrid:
    AgGrid(usage, fit_columns_on_grid_load=True)
else:
    st.dataframe(usage, use_container_width=True)

st.caption("This dashboard intentionally never renders RentCast, OpenAI, or Supabase service-role key names or values.")
