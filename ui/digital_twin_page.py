"""PAGE 2 — Digital Twin (per-machine drill-down + live fault injection)."""
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from database import repository as repo
from digital_twin.machine_twin import MachineTwin
from digital_twin.state_manager import persist
from digital_twin.workload_baseline import WorkloadBaseline
from intelligence.anomaly_detector import detect_anomalies
from intelligence.explainability import contribution_breakdown
from simulation.fault_simulator import COMPONENTS
from utils.helpers import pretty_component, status_color
from utils.chart_utils import sensor_trend_chart, risk_gauge, degradation_bar
from ui.theme import metric_card, status_chip


def render(twins: dict, fault_sim):
    st.title("🧠 Digital Twin")
    st.caption("Per-machine telemetry, component degradation, and live fault injection")

    machine_ids = [m["machine_id"] for m in repo.list_machines()]
    if not machine_ids:
        st.warning("No machines seeded.")
        return

    col_a, col_b = st.columns([3, 1])
    with col_a:
        selected = st.selectbox("Select Machine", machine_ids)
    with col_b:
        if st.button("🔄 Rebuild From DB"):
            df = _load_df(selected)
            if not df.empty:
                t = MachineTwin.build(selected, df)
                persist(t)
                st.success("Rebuilt.")
                st.rerun()

    twin = twins.get(selected)
    df = _load_df(selected)

    if twin is None or df.empty:
        st.info("Not enough telemetry yet for this machine.")
        return

    # ---- Top KPIs ----
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Health", f"{twin.health:.0f}/100",
                          color="#4caf50" if twin.health > 60 else "#ff9800")
    with c2: metric_card("Risk", f"{twin.risk:.0f}",
                          color=status_color(twin.status))
    with c3: metric_card("Reliability", f"{twin.reliability:.0f}%")
    with c4:
        st.markdown(
            f"<div class='metric-card' style='border-left-color:{status_color(twin.status)}'>"
            f"<div class='lbl'>Status</div>"
            f"<div class='val'>{twin.status}</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<div class='explain-box'>💡 <b>Diagnosis:</b> {twin.explanation}</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    col_l, col_r = st.columns([2, 1])
    with col_l:
        sensors = ["engine_temp_c", "coolant_temp_c", "oil_pressure_kpa",
                   "vibration_mm_s", "engine_load_pct"]
        st.plotly_chart(sensor_trend_chart(df, sensors, "Telemetry Trend"),
                        use_container_width=True)
    with col_r:
        st.plotly_chart(risk_gauge(twin.risk, twin.reliability, twin.status),
                        use_container_width=True)
        if twin.severities:
            st.plotly_chart(degradation_bar(twin.severities), use_container_width=True)

    st.divider()
    st.subheader("🔍 Actual vs Expected (Workload-Aware)")
    anomalies = detect_anomalies(df, twin.baseline)
    if anomalies:
        rows = []
        for sensor, info in anomalies.items():
            rows.append({
                "Sensor": sensor,
                "Actual": info["value"],
                "Expected @ Load": info["expected"],
                "z-score": info["z"],
                "Anomalous": "⚠️" if info["anomalous"] else "OK",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🚨 Inject Simulated Fault")
    st.caption("Injects a gradual degradation starting now. Watch the twin react.")
    ic1, ic2 = st.columns([3, 1])
    with ic1:
        comp = st.selectbox("Component", COMPONENTS,
                             format_func=pretty_component, key="inject_comp")
    with ic2:
        if st.button("💥 Inject Fault"):
            fault_sim.inject_fault(selected, comp)
            st.success(f"Fault injected on {pretty_component(comp)}")
            st.info("Now click *Generate Live Telemetry* below to advance time.")

    st.divider()
    st.subheader("⏩ Live Telemetry Generator")
    gc1, gc2, gc3 = st.columns(3)
    with gc1:
        hours = st.slider("Simulate hours", 1, 72, 12, step=1)
    with gc2:
        tick = st.selectbox("Tick size (h)", [1, 2, 4], index=0)
    with gc3:
        st.write(" ")
        if st.button("▶ Generate Live Telemetry"):
            from simulation.telemetry_generator import TelemetryGenerator
            gen = TelemetryGenerator(fault_sim, seed=int(datetime.utcnow().timestamp()))
            now = datetime.utcnow()
            new_rows = []
            for h in range(0, hours, tick):
                new_rows.append(gen.generate_tick(selected,
                                now.replace(microsecond=0), hours=float(tick)))
            repo.insert_telemetry(new_rows)
            persist(MachineTwin.build(selected, _load_df(selected)))
            st.success(f"Generated {len(new_rows)} new readings.")
            st.rerun()


def _load_df(machine_id):
    rows = repo.fetch_telemetry(machine_id, limit=400)
    df = pd.DataFrame(rows)
    if not df.empty:
        df["ts"] = pd.to_datetime(df["ts"])
    return df