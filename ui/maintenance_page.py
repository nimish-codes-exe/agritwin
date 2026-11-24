"""PAGE 5 — Maintenance Optimizer."""
import streamlit as st
import pandas as pd
from database import repository as repo
from optimization.maintenance_scheduler import run_scheduler


def render(twins: dict):
    st.title("🛠️ Maintenance Optimizer")
    st.caption("Resource-constrained scheduling with harvest-window awareness")

    states = repo.fetch_machine_states()
    machines = repo.list_machines()
    farms = repo.list_farms()
    techs = repo.list_technicians()
    parts = repo.list_parts()
    harvests = repo.list_harvests()

    st.subheader("📦 Resource Snapshot")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Technicians Available", sum(1 for t in techs if t["available"]))
        st.dataframe([{"Name": t["name"], "Skills": t["skills"]} for t in techs],
                     use_container_width=True, hide_index=True)
    with c2:
        st.metric("Parts In Stock", sum(p["quantity"] for p in parts))
        st.dataframe([{"Part": p["name"], "Qty": p["quantity"]} for p in parts],
                     use_container_width=True, hide_index=True)
    with c3:
        st.metric("Upcoming Harvests", len(harvests))
        st.dataframe([{"Farm": h["farm_id"], "Start": h["start_date"],
                       "Priority": h["priority"]} for h in harvests],
                     use_container_width=True, hide_index=True)

    st.divider()
    if st.button("🧮 Run Optimizer"):
        schedule = run_scheduler(states, machines, farms, techs, parts, harvests)
        if not schedule:
            st.info("No maintenance required — all machines healthy.")
        else:
            st.success(f"Schedule generated for {len(schedule)} machines.")
            df = pd.DataFrame([
                {
                    "Machine": r["machine_id"],
                    "Risk": f"{r['risk']:.0f}",
                    "Component": r["worst_component"],
                    "Harvest Boost": f"×{r['harvest_mult']:.2f}",
                    "Priority": f"{r['priority']:.0f}",
                    "Decision": r["decision"],
                    "Tech": r["tech"] or "—",
                    "ETA": r["eta"] or "—",
                    "Duration (h)": r["duration_h"],
                    "Est. Cost": f"${r['est_cost']:,.0f}" if r["est_cost"] else "—",
                    "Reason": r["reason"],
                }
                for r in schedule
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.subheader("🧠 Decision Explanations")
            for r in schedule[:6]:
                icon = "✅" if r["decision"] == "Scheduled" else "⏸"
                st.markdown(
                    f"**{icon} {r['machine_id']}** — {r['decision']}: {r['reason']}"
                )

            if st.button("💾 Commit Schedule to DB"):
                repo.clear_pending_schedules()
                for r in schedule:
                    if r["decision"] == "Scheduled":
                        repo.insert_schedule(r["machine_id"], r["tech_id"],
                                              r["eta"], r["duration_h"],
                                              f"Repair {r['worst_component']}")
                st.success("Committed.")

    st.divider()
    st.subheader("📅 Current Schedule")
    sched = repo.list_schedules()
    if sched:
        st.dataframe(sched, use_container_width=True, hide_index=True)
    else:
        st.info("No schedules committed yet.")