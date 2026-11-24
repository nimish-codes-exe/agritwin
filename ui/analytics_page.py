"""PAGE 6 — Performance Analytics."""
import streamlit as st
import pandas as pd
import plotly.express as px
from analytics.performance_metrics import simulate_strategies
from analytics.baseline_comparison import comparison_table


def render():
    st.title("📈 Performance Analytics")
    st.caption("Rigorous comparison: conventional vs threshold vs AgriTwin")

    runs = st.slider("Simulation runs", 10, 100, 30, step=10)

    if st.button("▶ Run Comparison Study"):
        with st.spinner("Simulating identical fault scenarios across 3 strategies..."):
            sim = simulate_strategies(n_runs=runs, horizon_hours=240)
        st.session_state["sim_result"] = sim

    sim = st.session_state.get("sim_result")
    if not sim:
        st.info("Click **Run Comparison Study** above to generate results.")
        return

    df = comparison_table(sim)
    st.subheader("📊 Results")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("💵 Average Cost per Incident")
    fig1 = px.bar(df, x="Strategy", y="Avg Cost (USD)", color="Strategy",
                   color_discrete_sequence=["#f44336", "#ff9800", "#7ac74f"])
    fig1.update_layout(paper_bgcolor="#0f1e2e", plot_bgcolor="#0f1e2e",
                        font=dict(color="#e0e6ee"))
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("⏱️ Average Downtime")
    fig2 = px.bar(df, x="Strategy", y="Avg Downtime (h)", color="Strategy",
                   color_discrete_sequence=["#f44336", "#ff9800", "#7ac74f"])
    fig2.update_layout(paper_bgcolor="#0f1e2e", plot_bgcolor="#0f1e2e",
                        font=dict(color="#e0e6ee"))
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("💾 Export")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, "agritwin_comparison.csv", "text/csv")

    st.caption(
        f"**Method:** {sim['runs']} identical fault scenarios × 240h horizon. "
        "Fixed-Hour = 200h calendar. Threshold = raw sensor critical. "
        "AgriTwin = composite risk > 50. All deterministic."
    )