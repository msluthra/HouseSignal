"""Market map page using pydeck and mock listings."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from app.ui import apply_theme, hero
from src.agents.base import AgentContext
from src.agents.market_data_agent import MarketDataAgent
from src.mock.sample_data import MARKET_SNAPSHOTS, MOCK_LISTINGS, SAMPLE_DEAL

try:
    import plotly.express as px
except ImportError:  # pragma: no cover - optional chart dependency fallback.
    px = None

try:
    import pydeck as pdk
except ImportError:  # pragma: no cover - optional map dependency fallback.
    pdk = None

st.set_page_config(page_title="HouseSignal AI | Market Map", layout="wide")
apply_theme()
hero(
    "Market Map",
    "Explore mock pilot markets and listing-style deal points before live RentCast and Supabase-backed listings are connected.",
    pills=["San Jose", "Sacramento", "Elk Grove", "Mock listings"],
)

market_df = pd.DataFrame(MARKET_SNAPSHOTS)
listing_df = pd.DataFrame(MOCK_LISTINGS)

with st.sidebar:
    st.header("Filters")
    selected_cities = st.multiselect("Markets", sorted(market_df["city"].unique()), default=sorted(market_df["city"].unique()))
    max_risk = st.slider("Max Listing Risk", 0, 100, 45)

filtered_listings = listing_df[listing_df["city"].isin(selected_cities) & (listing_df["risk"] <= max_risk)]
filtered_markets = market_df[market_df["city"].isin(selected_cities)]

st.subheader("Pilot Market Snapshot")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Markets", len(filtered_markets))
k2.metric("Mock Listings", len(filtered_listings))
k3.metric("Avg Signal", f"{filtered_markets['market_signal'].mean():.1f}" if not filtered_markets.empty else "N/A")
k4.metric("Avg Risk", f"{filtered_markets['risk'].mean():.1f}" if not filtered_markets.empty else "N/A")

if pdk:
    map_layers = [
        pdk.Layer(
            "ScatterplotLayer",
            data=filtered_markets,
            get_position="[lon, lat]",
            get_radius="market_signal * 150",
            get_fill_color="[15, 118, 110, 155]",
            pickable=True,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data=filtered_listings,
            get_position="[lon, lat]",
            get_radius="units * 120",
            get_fill_color="[196, 123, 45, 210]",
            pickable=True,
        ),
    ]

    view_state = pdk.ViewState(latitude=37.9, longitude=-121.7, zoom=6, pitch=0)
    st.pydeck_chart(
        pdk.Deck(
            layers=map_layers,
            initial_view_state=view_state,
            tooltip={"text": "{city}\n{name}\nSignal: {market_signal}\nRisk: {risk}\nUnits: {units}"},
        )
    )
else:
    st.map(filtered_listings.rename(columns={"lat": "latitude", "lon": "longitude"}))

left, right = st.columns([1.1, 1])
with left:
    st.markdown("### Market Signal vs Risk")
    if px:
        fig = px.scatter(
            market_df,
            x="risk",
            y="market_signal",
            size="market_signal",
            color="city",
            hover_data=["inventory_trend", "takeaway", "latest_record_date"],
            color_discrete_sequence=["#0f766e", "#b45309", "#2563eb"],
        )
        fig.update_layout(height=360, margin=dict(l=20, r=20, t=35, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.scatter_chart(market_df, x="risk", y="market_signal", color="#0f766e")

with right:
    st.markdown("### Market Agent Readout")
    selected_market = st.selectbox("Analyze Market", list(filtered_markets["city"]) if not filtered_markets.empty else [SAMPLE_DEAL.city])
    snapshot = next((item for item in MARKET_SNAPSHOTS if item["city"] == selected_market), MARKET_SNAPSHOTS[0])
    result = MarketDataAgent().run(AgentContext(property_profile=SAMPLE_DEAL.to_agent_profile(), market_snapshot=snapshot))
    st.write(result.summary)
    for finding in result.findings:
        st.write(f"- {finding}")
    for risk in result.risks:
        st.warning(risk)

st.markdown("### Mock Listing Feed")
st.dataframe(
    filtered_listings.style.format({"price": "${:,.0f}", "cap_rate": "{:.2%}", "risk": "{:.0f}"}),
    use_container_width=True,
)
st.caption("Listings are fake demo rows. Live listing/property calls should go through the backend RentCast cache and daily limiter.")
