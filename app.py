"""
AgriTwin AI — Streamlit entrypoint.

Run: streamlit run app.py
"""
import streamlit as st

from config import SIM_MACHINES
from database import init_database
from database import seed
from database import repository as repo
from digital_twin.state_manager import rebuild_all
from simulation.fault_simulator import FaultSimulator
from simulation.telemetry_generator import TelemetryGenerator
from ui.theme import apply_theme
from ui import (dashboard, digital_twin_page, diagnostics_page,
                simulator_page, maintenance_page, analytics_page)


st.set_page_config(page_title="AgriTwin AI", page_icon="🚜", layout="wide")
apply_theme()


# ---------- One-time bootstrap ----------
@st.cache_resource
def bootstrap():
    init_database()
    seed.ensure_seeded()

    machine_ids = [m["machine_id"] for m in repo.list_machines()]

    # Seed 60 days of telemetry if DB is empty
    if repo.table_count("telemetry") == 0:
        fs = FaultSimulator(machine_ids)
        gen = TelemetryGenerator(fs, seed=1)
        rows = gen.generate_history(machine_ids, days=60, tick_hours=2)
        repo.insert_telemetry(rows)

    # Persistent fault simulator (shared across pages so injection persists)
    fs = FaultSimulator(machine_ids)
    # Restore live state by advancing through last 24h worth of ticks
    for mid in machine_ids:
        fs.advance(mid, 0)  # no-op, keeps initial state
    return fs


@st.cache_data(ttl=30, show_spinner=False)
def get_twins():
    return rebuild_all()


fault_sim = bootstrap()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🚜 **AgriTwin AI**")
    st.caption("Uncertainty-Aware Predictive Maintenance Digital Twin")
    st.divider()
    page = st.radio("Navigate", [
        "🏠 Fleet Overview",
        "🧠 Digital Twin",
        "🔍 AI Diagnostics",
        "🔮 What-If Simulator",
        "🛠️ Maintenance Optimizer",
        "📈 Performance Analytics",
    ])
    st.divider()
    st.caption(f"**Machines:** {len(repo.list_machines())}")
    st.caption(f"**Telemetry rows:** {repo.table_count('telemetry'):,}")
    st.caption(f"**Active faults logged:** {len(repo.list_faults(limit=100))}")
    if st.button("🔄 Rebuild All Twins"):
        st.cache_data.clear()
        st.rerun()

twins = get_twins()

# ---------- Route ----------
if page == "🏠 Fleet Overview":
    dashboard.render(twins)
elif page == "🧠 Digital Twin":
    digital_twin_page.render(twins, fault_sim)
elif page == "🔍 AI Diagnostics":
    diagnostics_page.render(twins)
elif page == "🔮 What-If Simulator":
    simulator_page.render(twins)
elif page == "🛠️ Maintenance Optimizer":
    maintenance_page.render(twins)
elif page == "📈 Performance Analytics":
    analytics_page.render()

st.divider()
st.caption(
    "**AgriTwin AI** · Deterministic digital twin · No ML training · "
    "No external APIs · All estimates simulated."
)