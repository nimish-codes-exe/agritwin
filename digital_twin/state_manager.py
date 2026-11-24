"""Persists twin summaries to machine_states table."""
import pandas as pd
from database import repository as repo
from .machine_twin import MachineTwin


class StateManager:
    @staticmethod
    def persist(twin: MachineTwin):
        repo.upsert_machine_state(
            machine_id=twin.machine_id,
            health=twin.health,
            risk=twin.risk,
            reliability=twin.reliability,
            status=twin.status,
            degradation=twin.severities,
        )

    @staticmethod
    def rebuild_all() -> dict:
        twins = {}
        for m in repo.list_machines():
            mid = m["machine_id"]
            df = StateManager._load_df(mid)
            if df.empty:
                continue
            t = MachineTwin.build(mid, df)
            StateManager.persist(t)
            twins[mid] = t
        return twins

    @staticmethod
    def _load_df(machine_id):
        rows = repo.fetch_telemetry(machine_id, limit=400)
        df = pd.DataFrame(rows)
        if not df.empty:
            df["ts"] = pd.to_datetime(df["ts"])
        return df


# Backwards-compatible module-level helpers
persist = StateManager.persist
rebuild_all = StateManager.rebuild_all