"""
Generates realistic telemetry for one or many machines.

Nominal values are modulated by engine load + RPM, then fault severities
push sensors beyond nominal bands. Small Gaussian noise keeps the series
looking real. Sensor validity can be broken independently.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict
import math

from .fault_simulator import FaultSimulator


BASE = {
    "engine_temp_c":      82.0,
    "oil_pressure_kpa":   350.0,
    "engine_rpm":         1600.0,
    "vibration_mm_s":     2.5,
    "fuel_consumption_lh": 6.5,
    "engine_load_pct":    55.0,
    "coolant_temp_c":     80.0,
}


class TelemetryGenerator:
    def __init__(self, fault_sim: FaultSimulator, seed: int = 1):
        self.fault_sim = fault_sim
        self.rng = random.Random(seed)

    def _load_factor(self, load_pct: float) -> float:
        # 0.5 at 0% load, 1.0 at 55%, 1.35 at 100%
        return 0.55 + 0.008 * load_pct

    def generate_tick(self, machine_id: str, ts: datetime,
                      hours: float = 1.0) -> Dict:
        sev = self.fault_sim.advance(machine_id, hours)
        st = self.fault_sim.states[machine_id]

        # realistic load oscillation
        load_pct = max(20, min(100, BASE["engine_load_pct"] + self.rng.gauss(0, 12)))
        rpm = max(900, min(2400, 900 + load_pct * 12 + self.rng.gauss(0, 40)))
        lf = self._load_factor(load_pct)

        e_heat  = sev.get("engine_heat", 0.0)
        o_press = sev.get("oil_pressure", 0.0)
        vib     = sev.get("vibration", 0.0)
        cool    = sev.get("cooling", 0.0)

        engine_temp  = BASE["engine_temp_c"] * lf + 25 * e_heat + self.rng.gauss(0, 1.2)
        oil_pressure = BASE["oil_pressure_kpa"] * lf * (1 - 0.45 * o_press) + self.rng.gauss(0, 8)
        vibration    = BASE["vibration_mm_s"] * (1 + 2.8 * vib) + abs(self.rng.gauss(0, 0.25))
        coolant      = BASE["coolant_temp_c"] * lf + 22 * cool + self.rng.gauss(0, 1.0)
        fuel         = BASE["fuel_consumption_lh"] * lf * (1 + 0.3 * e_heat + 0.2 * vib) + self.rng.gauss(0, 0.4)

        # sensor validity override
        sensor_valid = 1
        vib_prof = st.profiles.get("vibration")
        if vib_prof and vib_prof.sensor_stuck_at is not None:
            vibration = vib_prof.sensor_stuck_at
            sensor_valid = 0

        return {
            "machine_id": machine_id,
            "ts": ts.isoformat(timespec="seconds"),
            "engine_temp_c": round(engine_temp, 2),
            "oil_pressure_kpa": round(oil_pressure, 1),
            "engine_rpm": round(rpm, 0),
            "vibration_mm_s": round(vibration, 2),
            "fuel_consumption_lh": round(fuel, 2),
            "engine_load_pct": round(load_pct, 1),
            "coolant_temp_c": round(coolant, 2),
            "operating_hours": round(st.operating_hours, 2),
            "operating_status": "working" if load_pct > 30 else "idle",
            "sensor_valid": sensor_valid,
        }

    def generate_history(self, machine_ids: List[str], days: int = 60,
                         tick_hours: int = 2) -> List[Dict]:
        """Bulk history for seeding."""
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        start = now - timedelta(days=days)
        rows = []
        n_ticks = int(days * 24 / tick_hours)
        for i in range(n_ticks):
            ts = start + timedelta(hours=i * tick_hours)
            for mid in machine_ids:
                rows.append(self.generate_tick(mid, ts, hours=tick_hours))
        return rows