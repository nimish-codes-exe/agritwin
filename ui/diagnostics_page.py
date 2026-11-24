"""PAGE 3 — AI Diagnostics."""
import streamlit as st
import pandas as pd
from database import repository as repo
from intelligence.anomaly_detector import detect_anomalies
from intelligence.explainability import contribution_breakdown
from intelligence.risk_engine import COMPONENT_WEIGHTS
from utils.helpers import pretty_component, status_color
from ui.theme import status_chip


def render(twins: dict):
    st.title("🔍 AI Diagnostics")
    st.caption("Transparent, rule-based diagnostics — no ML black boxes")

    if not twins:
        st.warning("No twin states yet.")
        return

    selected = st.selectbox("Machine", sorted(twins.keys()))
    twin = twins[selected]

    c1, c2, c3 = st.columns(3)
    c1.metric("Risk Score", f"{twin.risk:.1f}")
    c2.metric("Reliability", f"{twin.reliability:.0f}%")
    c3.metric("Status", twin.status)

    if twin.reliability < 40:
        st.error("⚠️ **Low data reliability** — insufficient telemetry for confident diagnosis. "
                 "Physical inspection recommended.")
    elif twin.reliability < 70:
        st.warning("Data reliability moderate — treat predictions with caution.")

    st.divider()
    st.subheader("Component Health")
    if twin.severities:
        cols = st.columns(len(twin.severities))
        for i, (comp, sev) in enumerate(twin.severities.items()):
            health = int(round((1 - sev) * 100))
            color = "#4caf50" if health > 70 else "#ff9800" if health > 40 else "#f44336"
            with cols[i]:
                st.markdown(
                    f"<div class='metric-card' style='border-left-color:{color}'>"
                    f"<div class='lbl'>{pretty_component(comp)}</div>"
                    f"<div class='val'>{health}%</div></div>",
                    unsafe_allow_html=True)
    else:
        st.info("No significant degradation detected.")

    st.divider()
    st.subheader("Sensor Contribution Breakdown")
    st.caption("How each component contributes to the overall risk score")
    if twin.severities:
        contrib = contribution_breakdown(twin.severities)
        rows = [{"Component": pretty_component(c),
                 "Weight in Model": f"{COMPONENT_WEIGHTS.get(c, 0.1):.0%}",
                 "Contribution": f"{v:.1f}%"}
                for c, v in contrib.items()]
        st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Anomaly Detection (Contextual Z-Score)")
    st.caption("Compares each reading to expected value for current engine load")
    df = _load_df(selected)
    if not df.empty:
        anomalies = detect_anomalies(df, twin.baseline)
        if anomalies:
            rows = [{"Sensor": s, "Value": i["value"], "Expected": i["expected"],
                     "z-score": i["z"], "Flag": "⚠️" if i["anomalous"] else "OK"}
                    for s, i in anomalies.items()]
            st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("💡 Recommended Action")
    st.markdown(f"<div class='explain-box'>{twin.explanation}</div>",
                unsafe_allow_html=True)

    st.caption(
        "**Distinction:** *Observed* = raw sensor value. "
        "*Estimated* = degradation score. *Predicted* = risk score. "
        "*Confirmed* = physically verified — not shown in this dashboard."
    )


def _load_df(machine_id):
    rows = repo.fetch_telemetry(machine_id, limit=400)
    df = pd.DataFrame(rows)
    if not df.empty:
        df["ts"] = pd.to_datetime(df["ts"])
    return df