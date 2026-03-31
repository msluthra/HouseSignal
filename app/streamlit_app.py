"""Streamlit frontend for California investment recommendations."""

from __future__ import annotations

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="ProphetAI", layout="wide")
st.title("ProphetAI")
st.caption("Estimate fair value, appreciation, rent, risk, and investment recommendation.")

with st.form("property_form"):
    address = st.text_input("Address", value="123 Main St, San Jose, CA")
    col1, col2, col3 = st.columns(3)
    with col1:
        list_price = st.number_input("List Price ($)", min_value=50000.0, value=850000.0, step=5000.0)
    with col2:
        beds = st.number_input("Beds", min_value=1.0, value=3.0, step=1.0)
    with col3:
        baths = st.number_input("Baths", min_value=1.0, value=2.0, step=0.5)

    sqft = st.number_input("Sqft", min_value=400.0, value=1500.0, step=50.0)
    neighborhood_price_per_sqft = st.number_input(
        "Neighborhood Price/Sqft ($)",
        min_value=100.0,
        value=550.0,
        step=10.0,
    )
    submit = st.form_submit_button("Get Recommendation")

if submit:
    payload = {
        "address": address,
        "list_price": list_price,
        "beds": beds,
        "baths": baths,
        "sqft": sqft,
        "neighborhood_price_per_sqft": neighborhood_price_per_sqft,
    }
    try:
        response = requests.post(f"{API_BASE_URL}/recommend", json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()

        st.subheader("Recommendation")
        st.metric("Label", result["recommendation_label"].upper())

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Fair Value", f"${result['fair_value']:,.0f}")
        c2.metric("Expected Monthly Rent", f"${result['expected_monthly_rent']:,.0f}")
        c3.metric("Investment Score", f"{result['investment_score']:.1f}")
        c4.metric("Downside Risk", f"{result['downside_risk'] * 100:.1f}%")

        st.subheader("Appreciation Forecast")
        st.write(
            {
                "3M": f"{result['appreciation_3m'] * 100:.2f}%",
                "6M": f"{result['appreciation_6m'] * 100:.2f}%",
                "12M": f"{result['appreciation_12m'] * 100:.2f}%",
            }
        )
    except requests.RequestException as exc:
        st.error(f"Failed to call API at {API_BASE_URL}: {exc}")
