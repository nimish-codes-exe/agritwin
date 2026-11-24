"""PAGE 1 — Fleet Overview."""
import streamlit as st
import plotly.graph_objects as go
from utils.helpers import status_color, fmt_pct
from database import repository as repo


def render(twins: dict):
    st.title("🚜 Fleet Overview")
    st.caption("Live digital twin view across your entire machinery fleet")

    if not twins:
        st.warning("No machine states yet. Go to *Digital Twin* → Rebuild all.")
        return

    total    = len(twins)
    healthy  = sum(1 for t in twins.values() if t.status == "Healthy")
    warning  = sum(1 for t in twins.values() if t.status == "Warning")
    high     = sum(1 for t in twins.values() if t.status == "High Risk")
    critical = sum(1 for t in twins.values() if t.status == "Critical")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Machines", total)
    c2.metric("🟢 Healthy", healthy)
    c3.metric("🟡 Warning", warning)
    c4.metric("🟠 High Risk", high)
    c5.metric("🔴 Critical", critical)

    st.divider()

    col1, col2 = st.columns([3, 2])
    with col1:
        # Risk-by-machine bar
        order = sorted(twins.values(), key=lambda t: -t.risk)
        fig = go.Figure(go.Bar(
            x=[t.machine_id for t in order],
            y=[t.risk for t in order],
            marker_color=[status_color(t.status) for t in order],
            text=[f"{t.risk:.0f}" for t in order],
            textposition="outside",
        ))
        fig.update_layout(
            title="Risk Score by Machine",
            paper_bgcolor="#0f1e2e", plot_bgcolor="#0f1e2e",
            font=dict(color="#e0e6ee"),
            xaxis=dict(gridcolor="#1e3247"),
            yaxis=dict(gridcolor="#1e3247", range=[0, 105]),
            height=380, margin=dict(l=20, r=20, t=40, b=60),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Status donut
        fig2 = go.Figure(go.Pie(
            values=[healthy, warning, high, critical],
            labels=["Healthy", "Warning", "High Risk", "Critical"],
            hole=0.55,
            marker=dict(colors=["#4caf50", "#ff9800", "#ff5722", "#f44336"]),
        ))
        fig2.update_layout(
            title="Status Distribution", height=380,
            paper_bgcolor="#0f1e2e", font=dict(color="#e0e6ee"),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📋 Machine Snapshot")
    rows = []
    for t in sorted(twins.values(), key=lambda x: -x.risk):
        rows.append({
            "Machine":      t.machine_id,
            "Status":       t.status,
            "Health":       f"{t.health:.0f}",
            "Risk":         f"{t.risk:.0f}",
            "Reliability":  f"{t.reliability:.0f}%",
            "Primary Issue": t.explanation.split(".")[0][:70],
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("🧾 Recent Fault Events")
    faults = repo.list_faults(limit=10)
    if not faults:
        st.info("No fault events recorded yet.")
    else:
        st.dataframe(faults, use_container_width=True, hide_index=True)