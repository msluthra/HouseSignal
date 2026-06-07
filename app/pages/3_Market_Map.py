"""Market map page using pydeck."""

from __future__ import annotations

import pandas as pd
import pydeck as pdk
import streamlit as st

st.set_page_config(page_title="Market Map", layout="wide")
st.title("Market Map")
st.caption("Pilot market view for San Jose and Sacramento. Listing-level feeds will plug into this page after RentCast/Supabase caching is configured.")

data = pd.DataFrame(
    [
        {"city": "San Jose", "lat": 37.3382, "lon": -121.8863, "market_signal": 64, "risk": 28},
        {"city": "Sacramento", "lat": 38.5816, "lon": -121.4944, "market_signal": 57, "risk": 33},
    ]
)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=data,
    get_position="[lon, lat]",
    get_radius="market_signal * 120",
    get_fill_color="[15, 118, 110, 170]",
    pickable=True,
)

view_state = pdk.ViewState(latitude=37.9, longitude=-121.7, zoom=6, pitch=0)
st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{city}\nSignal: {market_signal}\nRisk: {risk}"}))
st.dataframe(data, use_container_width=True)
