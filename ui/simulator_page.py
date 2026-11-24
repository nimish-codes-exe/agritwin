"""PAGE 4 — What-If Counterfactual Simulator."""
import streamlit as st
from simulation.scenario_engine import ScenarioEngine
from utils.chart_utils import scenario_comparison_chart


POLICY_LABELS = {
    "repair_now": "🔧 Repair Now",
    "delay_48h":  "⏸ Delay 48 Hours",
    "continue":   "⚠️ Continue Operating",
}


def render(twins: dict):
    st.title("🔮 What-If Simulator")
    st.caption("Counterfactual decision support — compare maintenance choices BEFORE committing")

    if not twins:
        st.warning("No machine states.")
        return

    selected = st.selectbox("Machine", sorted(twins.keys()))
    twin = twins[selected]

    st.info(f"Current: **{twin.status}** · Risk {twin.risk:.0f} · "
            f"{twin.explanation[:80]}")

    horizon = st.slider("Projection horizon (hours)", 12, 96, 48, step=12)

    engine = ScenarioEngine([selected])
    projections = {}
    summary_rows = []
    for policy in POLICY_LABELS:
        proj = engine.run_projection(selected, twin.severities,
                                      horizon_hours=horizon, policy=policy)
        projections[policy] = proj
        max_temp = max(p["engine_temp_c"] for p in proj)
        max_vib  = max(p["vibration_mm_s"] for p in proj)
        failure_risk = "HIGH" if max_temp > 110 or max_vib > 8 else \
                        "MODERATE" if max_temp > 100 or max_vib > 6 else "LOW"
        est_downtime = {"repair_now": 3, "delay_48h": 3 + 2, "continue": 3 + 8}[policy]
        est_cost = est_downtime * 120 + 45 * 3
        summary_rows.append({
            "Decision": POLICY_LABELS[policy],
            "Max Engine Temp": f"{max_temp:.1f} °C",
            "Max Vibration": f"{max_vib:.2f} mm/s",
            "Failure Risk": failure_risk,
            "Est. Downtime (h)": est_downtime,
            "Est. Cost (USD)": f"${est_cost:,.0f}",
        })

    st.subheader("📊 Projected Degradation")
    st.plotly_chart(scenario_comparison_chart(projections), use_container_width=True)

    st.subheader("📋 Side-by-Side Comparison")
    st.dataframe(summary_rows, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("✅ Recommendation")
    st.success(
        "**Repair Now** is recommended — it avoids the projected thermal escalation "
        "and keeps the machine within safe operating bounds. " if twin.risk > 50 else
        "**Continue with monitoring** — current degradation is gradual; schedule maintenance "
        "at the next natural window to minimize disruption."
    )

    st.caption(
        "⚠️ All figures are **simulated deterministic estimates**, not real-world guarantees. "
        "They help structure a decision, not replace judgement."
    )