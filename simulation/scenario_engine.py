"""
Provides repeatable "what-if" simulations without DB writes.
"""
import math
from typing import List, Dict
from datetime import datetime, timedelta
from .fault_simulator import FaultSimulator, FaultProfile, DEGRADE_WINDOW_H
from .telemetry_generator import TelemetryGenerator


class ScenarioEngine:
    def __init__(self, machine_ids, seed=99):
        self.machine_ids = machine_ids
        self.seed = seed

    def run_projection(self, machine_id: str, starting_severity: dict,
                       horizon_hours: int, policy: str) -> List[Dict]:
        """
        policy: 'repair_now' | 'delay_48h' | 'continue'
        """
        fs = FaultSimulator([machine_id])
        st = fs.states[machine_id]
        st.profiles.clear()

        for comp, sev in starting_severity.items():
            if sev <= 0.02:
                continue
            window = DEGRADE_WINDOW_H.get(comp, 250)
            sev = min(max(sev, 0.01), 0.99)
            x = 0.5 + (math.log(sev / (1 - sev)) / 6.0)
            st.profiles[comp] = FaultProfile(
                component=comp,
                onset_hour=-x * window,
                rng_seed=0,
            )

        gen = TelemetryGenerator(fs, seed=self.seed)
        reset_at = {"repair_now": 0, "delay_48h": 48, "continue": None}[policy]
        rows = []
        start = datetime.utcnow()
        for h in range(horizon_hours):
            if reset_at is not None and h == reset_at:
                st.profiles.clear()
            row = gen.generate_tick(machine_id, start + timedelta(hours=h), hours=1.0)
            row["hour"] = h
            rows.append(row)
        return rows