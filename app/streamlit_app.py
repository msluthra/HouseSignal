"""Streamlit frontend for ProphetAI recommendations."""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

REAL_ESTATE_GLOSSARY: dict[str, str] = {
    "cap rate": "Cap rate is annual net operating income divided by property value. Higher usually means better cash return, but often with higher risk.",
    "fair value": "Fair value is an estimate of what a property should be worth today based on comparable and market factors.",
    "appreciation": "Appreciation is expected property value growth over time.",
    "yield": "Rental yield is annual rent divided by purchase price. It helps compare income efficiency across properties.",
    "downside risk": "Downside risk estimates probability of unfavorable outcomes, like value drop or underperformance.",
    "strong buy": "Strong buy suggests high relative attractiveness based on return, valuation, and risk signals.",
    "buy with caution": "Buy with caution suggests potential upside exists, but risks are meaningful and require tighter underwriting.",
    "hold/monitor": "Hold/monitor suggests the property is not a clear buy now; monitor for better pricing or conditions.",
    "avoid": "Avoid suggests risk-adjusted return is weak based on current assumptions.",
}


def ask_quick_question(result: dict[str, Any], question: str) -> str:
    """Return concise, friendly guidance for a quick prompt question."""
    score = float(result.get("investment_score", 0.0))
    label = str(result.get("recommendation_label", "hold/monitor"))
    risk = float(result.get("downside_risk", 0.0))
    appreciation_12m = float(result.get("appreciation_12m", 0.0))
    yield_pct = float(result.get("rental_yield", 0.0)) * 100
    fair_value = float(result.get("fair_value", 0.0))

    if question == "Why this recommendation?":
        return (
            f"This property is rated **{label}** mainly from score ({score:.1f}/100), "
            f"12M appreciation ({appreciation_12m * 100:.2f}%), yield ({yield_pct:.2f}%), "
            f"and downside risk ({risk * 100:.1f}%)."
        )
    if question == "What are the biggest risks?":
        return (
            f"Primary risk signal is downside risk at **{risk * 100:.1f}%**. "
            "Consider local vacancy trends, financing-rate sensitivity, and potential overpricing risk."
        )
    if question == "What could improve this score?":
        return (
            "Levers that usually improve score: lower entry price, higher achievable rent, "
            "or stronger projected appreciation in the target submarket."
        )
    if question == "Is this overpriced or discounted?":
        return (
            f"Estimated fair value is **${fair_value:,.0f}**. Compare this to your planned purchase price to "
            "judge discount or premium."
        )
    return "Ask another quick question to explore this recommendation."


def apply_preset(preset_name: str) -> None:
    """Update session state fields using preset scenario values."""
    presets: dict[str, dict[str, float | str]] = {
        "Starter Home": {
            "address": "450 Park Ave, San Jose, CA",
            "list_price": 780000.0,
            "beds": 3.0,
            "baths": 2.0,
            "sqft": 1350.0,
            "neighborhood_price_per_sqft": 560.0,
        },
        "Value Play": {
            "address": "112 Cedar St, Sacramento, CA",
            "list_price": 540000.0,
            "beds": 3.0,
            "baths": 2.0,
            "sqft": 1700.0,
            "neighborhood_price_per_sqft": 360.0,
        },
        "Premium Coastal": {
            "address": "89 Ocean View Dr, San Diego, CA",
            "list_price": 1450000.0,
            "beds": 4.0,
            "baths": 3.0,
            "sqft": 2400.0,
            "neighborhood_price_per_sqft": 720.0,
        },
    }
    values = presets[preset_name]
    for key, value in values.items():
        st.session_state[key] = value


def get_retrieved_context(question: str, result: dict[str, Any]) -> str:
    """Create lightweight retrieved context from glossary + current analysis."""
    q = question.lower()
    glossary_hits = []
    for term, definition in REAL_ESTATE_GLOSSARY.items():
        if term in q:
            glossary_hits.append(f"- {term}: {definition}")

    analysis_context = (
        "Current property analysis:\n"
        f"- Address: {result.get('address', 'N/A')}\n"
        f"- Recommendation label: {result.get('recommendation_label', 'N/A')}\n"
        f"- Investment score: {result.get('investment_score', 'N/A')}\n"
        f"- Fair value: {result.get('fair_value', 'N/A')}\n"
        f"- Expected monthly rent: {result.get('expected_monthly_rent', 'N/A')}\n"
        f"- Downside risk: {result.get('downside_risk', 'N/A')}\n"
        f"- Appreciation (12m): {result.get('appreciation_12m', 'N/A')}\n"
    )

    glossary_context = "\n".join(glossary_hits) if glossary_hits else "- No exact glossary matches found."
    return analysis_context + "\nGlossary context:\n" + glossary_context


def ask_gemini(question: str, result: dict[str, Any], chat_history: list[dict[str, str]]) -> str:
    """Call Gemini Flash with property context and glossary retrieval."""
    if not GEMINI_API_KEY:
        return (
            "Gemini is not configured yet. Add `GEMINI_API_KEY` to your `.env` file and restart Streamlit."
        )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    recent_history = chat_history[-6:]
    history_lines = []
    for msg in recent_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_lines.append(f"{role}: {content}")

    prompt = (
        "You are ProphetAI Copilot, a friendly real-estate assistant for non-expert users. "
        "Explain terms simply, avoid financial guarantees, and use only provided context.\n\n"
        f"{get_retrieved_context(question, result)}\n\n"
        "Recent chat:\n"
        + "\n".join(history_lines)
        + "\n\n"
        f"User question: {question}\n"
        "Answer in plain language with short actionable bullets when useful."
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 450},
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return "I could not generate a response right now. Please try again."
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return "I could not generate a response right now. Please try again."
        return parts[0].get("text", "I could not generate a response right now. Please try again.")
    except requests.RequestException as exc:
        return f"Gemini request failed: {exc}"


st.set_page_config(page_title="ProphetAI", layout="wide")

if "result" not in st.session_state:
    st.session_state["result"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

st.title("ProphetAI")
st.caption("Friendly AI-powered real estate investment insights for California homes.")

with st.container(border=True):
    st.subheader("1) Pick A Starting Scenario")
    p1, p2, p3 = st.columns(3)
    with p1:
        if st.button("Starter Home", use_container_width=True):
            apply_preset("Starter Home")
    with p2:
        if st.button("Value Play", use_container_width=True):
            apply_preset("Value Play")
    with p3:
        if st.button("Premium Coastal", use_container_width=True):
            apply_preset("Premium Coastal")

with st.container(border=True):
    st.subheader("2) Set Property Inputs")

    c1, c2 = st.columns([2, 1])
    with c1:
        address = st.text_input("Address", key="address", value=st.session_state.get("address", "123 Main St, San Jose, CA"))
        list_price = st.number_input(
            "List Price ($)",
            min_value=50000.0,
            step=5000.0,
            key="list_price",
            value=float(st.session_state.get("list_price", 850000.0)),
        )

        b1, b2, b3 = st.columns(3)
        with b1:
            beds = st.number_input("Beds", min_value=1.0, step=1.0, key="beds", value=float(st.session_state.get("beds", 3.0)))
        with b2:
            baths = st.number_input("Baths", min_value=1.0, step=0.5, key="baths", value=float(st.session_state.get("baths", 2.0)))
        with b3:
            sqft = st.number_input("Sqft", min_value=400.0, step=50.0, key="sqft", value=float(st.session_state.get("sqft", 1500.0)))

        neighborhood_price_per_sqft = st.number_input(
            "Neighborhood Price/Sqft ($)",
            min_value=100.0,
            step=10.0,
            key="neighborhood_price_per_sqft",
            value=float(st.session_state.get("neighborhood_price_per_sqft", 550.0)),
        )

    with c2:
        st.markdown("**Friendly Filters**")
        risk_profile = st.segmented_control(
            "Risk profile",
            options=["Conservative", "Balanced", "Aggressive"],
            default="Balanced",
        )
        show_metrics = st.multiselect(
            "Show sections",
            options=["Recommendation", "Core Metrics", "Appreciation", "Quick Q&A", "AI Chat Copilot"],
            default=["Recommendation", "Core Metrics", "Appreciation", "Quick Q&A", "AI Chat Copilot"],
        )
        st.caption("Tip: Use filters to keep the dashboard clean and focused.")

    run_analysis = st.button("Run Analysis", type="primary", use_container_width=True)

if run_analysis:
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
        st.session_state["result"] = response.json()
    except requests.RequestException as exc:
        st.error(f"Could not reach ProphetAI API at {API_BASE_URL}: {exc}")

result = st.session_state.get("result")
if result:
    if "Recommendation" in show_metrics:
        with st.container(border=True):
            st.subheader("Recommendation")
            st.metric("Label", str(result["recommendation_label"]).upper())
            st.caption(f"Risk profile selected: {risk_profile}")

    if "Core Metrics" in show_metrics:
        with st.container(border=True):
            st.subheader("Core Metrics")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Fair Value", f"${float(result['fair_value']):,.0f}")
            m2.metric("Expected Monthly Rent", f"${float(result['expected_monthly_rent']):,.0f}")
            m3.metric("Investment Score", f"{float(result['investment_score']):.1f}")
            m4.metric("Downside Risk", f"{float(result['downside_risk']) * 100:.1f}%")

    if "Appreciation" in show_metrics:
        with st.container(border=True):
            st.subheader("Appreciation Forecast")
            a1, a2, a3 = st.columns(3)
            a1.metric("3 Months", f"{float(result['appreciation_3m']) * 100:.2f}%")
            a2.metric("6 Months", f"{float(result['appreciation_6m']) * 100:.2f}%")
            a3.metric("12 Months", f"{float(result['appreciation_12m']) * 100:.2f}%")

    if "Quick Q&A" in show_metrics:
        with st.container(border=True):
            st.subheader("Quick Questions")
            q1, q2, q3, q4 = st.columns(4)
            quick_answer = ""
            with q1:
                if st.button("Why this recommendation?"):
                    quick_answer = ask_quick_question(result, "Why this recommendation?")
            with q2:
                if st.button("What are the biggest risks?"):
                    quick_answer = ask_quick_question(result, "What are the biggest risks?")
            with q3:
                if st.button("What could improve this score?"):
                    quick_answer = ask_quick_question(result, "What could improve this score?")
            with q4:
                if st.button("Is this overpriced or discounted?"):
                    quick_answer = ask_quick_question(result, "Is this overpriced or discounted?")

            if quick_answer:
                st.info(quick_answer)

    if "AI Chat Copilot" in show_metrics:
        with st.container(border=True):
            st.subheader("AI Chat Copilot (Gemini Flash)")
            st.caption("Ask in plain English. ProphetAI Copilot will explain real-estate terms and this property analysis.")

            if not GEMINI_API_KEY:
                st.warning("Set `GEMINI_API_KEY` in `.env` to enable live AI chat responses.")

            for msg in st.session_state["chat_history"]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            user_prompt = st.chat_input("Ask a question about this property or real-estate terms...")
            if user_prompt:
                st.session_state["chat_history"].append({"role": "user", "content": user_prompt})
                with st.chat_message("user"):
                    st.markdown(user_prompt)

                assistant_reply = ask_gemini(user_prompt, result, st.session_state["chat_history"])
                st.session_state["chat_history"].append({"role": "assistant", "content": assistant_reply})
                with st.chat_message("assistant"):
                    st.markdown(assistant_reply)
else:
    st.info("Run analysis to see recommendation, metrics, and quick Q&A insights.")
