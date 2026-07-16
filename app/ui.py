"""Shared Streamlit UI helpers for the HouseSignal AI app."""

from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st


def apply_theme() -> None:
    """Apply shared HouseSignal AI styling."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Manrope:wght@400;600;700;800&display=swap');
        html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }
        .stApp { background: radial-gradient(circle at top left, #dff5e9 0, transparent 28rem), linear-gradient(135deg, #f8fbf6 0%, #eef5f0 45%, #f6f0df 100%); color: #102018; }
        h1, h2, h3 { font-family: 'Fraunces', serif; letter-spacing: -0.03em; color: #102018; }
        section[data-testid="stSidebar"] { background: #102018; }
        section[data-testid="stSidebar"] * { color: #f7f3e8 !important; }
        .hs-hero { padding: 2rem; border-radius: 28px; background: linear-gradient(135deg, #102018 0%, #184833 58%, #c79b3b 150%); color: #fff8e8; box-shadow: 0 28px 70px rgba(16, 32, 24, 0.22); margin-bottom: 1.1rem; }
        .hs-hero h1 { color: #fff8e8; font-size: 3.1rem; margin-bottom: .4rem; }
        .hs-hero p { max-width: 820px; font-size: 1.08rem; color: #e7eadf; }
        .hs-pill { display: inline-block; padding: .35rem .75rem; border-radius: 999px; background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.22); margin-right: .45rem; font-size: .82rem; color: #fff8e8; }
        .hs-card { padding: 1.15rem; border-radius: 22px; background: rgba(255,255,255,.82); border: 1px solid #d9e5dd; box-shadow: 0 16px 40px rgba(31, 66, 52, 0.08); }
        .hs-small { color: #53665c; font-size: .92rem; }
        .hs-step { padding: .85rem 1rem; border-left: 4px solid #0f766e; background: rgba(255,255,255,.75); border-radius: 14px; margin-bottom: .65rem; }
        .hs-risk { color: #9f3a21; font-weight: 700; }
        .hs-ok { color: #0f766e; font-weight: 700; }
        div[data-testid="stMetric"] { background: rgba(255,255,255,.82); border: 1px solid #d9e5dd; border-radius: 18px; padding: 1rem; box-shadow: 0 10px 28px rgba(31,66,52,.07); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, pills: Iterable[str] = ()) -> None:
    """Render a branded page hero."""
    pill_html = "".join(f'<span class="hs-pill">{escape(pill)}</span>' for pill in pills)
    st.markdown(
        f"""
        <div class="hs-hero">
          <div>{pill_html}</div>
          <h1>{escape(title)}</h1>
          <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, body: str) -> None:
    """Render a simple content card."""
    st.markdown(
        f"""
        <div class="hs-card">
          <h3>{escape(title)}</h3>
          <p class="hs-small">{escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_step(step: str, status: str, detail: str) -> None:
    """Render one pipeline status step."""
    st.markdown(
        f"""
        <div class="hs-step">
          <strong>{escape(step)}</strong> <span class="hs-ok">{escape(status)}</span><br />
          <span class="hs-small">{escape(detail)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
