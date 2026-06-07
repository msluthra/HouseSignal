"""API usage and cache dashboard."""

from __future__ import annotations

import streamlit as st

from config.settings import settings
from src.services.usage_reporting import load_api_usage_frame

try:
    from st_aggrid import AgGrid
except ImportError:  # pragma: no cover - optional UI dependency fallback.
    AgGrid = None

st.set_page_config(page_title="API Usage", layout="wide")
st.title("API Usage + Cache")
st.caption("Protects free-tier API usage by showing cache hits, misses, blocked calls, and daily limits.")

st.metric("RentCast Daily Limit", settings.rentcast_daily_limit)
st.metric("RentCast Cache TTL Hours", settings.rentcast_cache_ttl_hours)

usage = load_api_usage_frame()
if usage.empty:
    st.info("No API usage logged yet.")
else:
    if AgGrid:
        AgGrid(usage, fit_columns_on_grid_load=True)
    else:
        st.dataframe(usage, use_container_width=True)
    summary = usage.groupby(["provider", "cache_status"]).size().reset_index(name="count")
    st.bar_chart(summary, x="cache_status", y="count", color="provider")
