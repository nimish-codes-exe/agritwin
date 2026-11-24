"""
Deterministic fault progression.

Each machine has a per-component fault profile: healthy -> degrading -> failing.
Fault severity is a function of exposure hours since onset (smooth S-curve),
not random noise.
"""
from dataclasses import dataclass, field
from typing import Dict
import math
import random


COMPONENTS = ["engine_heat", "oil_pressure", "vibration", "cooling"]

# Hours from onset to critical threshold per component
DEGRADE_WINDOW_H = {
    "engine_heat":  220.0,
    "oil_pressure": 260.0,
    "vibration":    300.0,
    "cooling":      240.0,
}


@dataclass
class FaultProfile:
    component: str
    onset_hour: float
    rng_seed: int = 0
    sensor_stuck_at: float = None   # if set, sensor is broken

    def severity(self, hours_since_onset: float) -> float:
        """0.0 = healthy, 1.0 = critical threshold."""
        if hours_since_onset <= 0:
            return 0.0
        window = DEGRADE_WINDOW_H[self.component]
        x = min(hours_since_onset / window, 1.5)
        # smooth S-curve
        return 1.0 / (1.0 + math.exp(-6.0 * (x - 0.5)))


@dataclass
class MachineFaultState:
    profiles: Dict[str, FaultProfile] = field(default_factory=dict)
    operating_hours: float = 0.0

    def advance(self, hours: float):
        self.operating_hours += hours

    def severities(self) -> Dict[str, float]:
        return {
            comp: prof.severity(self.operating_hours - prof.onset_hour)
            for comp, prof in self.profiles.items()
        }


class FaultSimulator:
    """Maintains per-machine fault state; can inject faults live."""

    def __init__(self, machine_ids):
        self.states: Dict[str, MachineFaultState] = {}
        self.rng = random.Random(42)
        for mid in machine_ids:
            self.states[mid] = self._random_initial(mid)

    def _random_initial(self, machine_id: str) -> MachineFaultState:
        """Some machines healthy, some mid-degradation."""
        r = random.Random(hash(machine_id) & 0xFFFFFFFF)
        state = MachineFaultState()
        # 40% chance the machine has a developing fault
        if r.random() < 0.4:
            comp = r.choice(COMPONENTS)
            # onset 20-120 hours ago
            state.profiles[comp] = FaultProfile(
                component=comp,
                onset_hour=-r.uniform(20, 120),
                rng_seed=r.randint(0, 1_000_000),
            )
        # 10% chance a sensor is stuck/faulty
        if r.random() < 0.10:
            state.profiles.setdefault("vibration", FaultProfile(
                component="vibration", onset_hour=0, rng_seed=0))
            state.profiles["vibration"].sensor_stuck_at = 3.0
        return state

    def advance(self, machine_id: str, hours: float) -> Dict[str, float]:
        st = self.states[machine_id]
        st.advance(hours)
        return st.severities()

    def inject_fault(self, machine_id: str, component: str):
        """Manual injection from UI — onset NOW."""
        st = self.states[machine_id]
        st.profiles[component] = FaultProfile(
            component=component,
            onset_hour=st.operating_hours,     # starts degrading from this moment
            rng_seed=random.randint(0, 1_000_000),
        )