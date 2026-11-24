"""Shared Streamlit theme injection."""
import streamlit as st


def apply_theme():
    st.markdown("""
    <style>
      .stApp { background-color: #0f1e2e; color: #e0e6ee; }
      [data-testid="stSidebar"] { background-color: #132a41; }
      h1, h2, h3 { color: #7ac74f !important; }
      .metric-card {
          background: #1a3350; padding: 18px; border-radius: 12px;
          border-left: 4px solid #7ac74f; box-shadow: 0 2px 8px rgba(0,0,0,0.35);
          margin-bottom: 12px;
      }
      .metric-card .lbl { color: #90a4ae; font-size: 0.82em; text-transform: uppercase; letter-spacing: 0.06em; }
      .metric-card .val { font-size: 1.9em; font-weight: 700; color: #e0e6ee; }
      .status-chip {
          display:inline-block; padding: 2px 10px; border-radius: 20px;
          font-size: 0.78em; font-weight: 600; margin-left: 6px;
      }
      .explain-box {
          background:#152a3d; border-left: 3px solid #7ac74f;
          padding: 12px 16px; border-radius: 8px; font-size: 0.92em;
      }
      .stButton>button { background:#7ac74f; color:#0f1e2e; font-weight:600; border:0; }
      .stButton>button:hover { background:#8fd860; color:#0f1e2e; }
    </style>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, color: str = "#7ac74f"):
    st.markdown(
        f"<div class='metric-card' style='border-left-color:{color}'>"
        f"<div class='lbl'>{label}</div>"
        f"<div class='val'>{value}</div></div>",
        unsafe_allow_html=True,
    )


def status_chip(status: str):
    from utils.helpers import status_color
    c = status_color(status)
    st.markdown(
        f"<span class='status-chip' style='background:{c};color:#0f1e2e'>{status}</span>",
        unsafe_allow_html=True,
    )