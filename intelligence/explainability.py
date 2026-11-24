"""
Plain-English explanations + per-sensor contribution breakdown.
No LLMs. Rule-based templates.
"""
from typing import Dict
import pandas as pd
from config import THRESHOLDS


FRIENDLY = {
    "engine_heat": "engine overheating",
    "cooling":     "cooling system degradation",
    "oil_pressure":"oil pressure loss",
    "vibration":   "abnormal engine vibration",
}


def contribution_breakdown(severities: Dict[str, float]) -> Dict[str, float]:
    from .risk_engine import COMPONENT_WEIGHTS
    total = sum(COMPONENT_WEIGHTS.get(c, 0.1) * s
                for c, s in severities.items()) or 1e-9
    out = {}
    for c, s in severities.items():
        w = COMPONENT_WEIGHTS.get(c, 0.1)
        out[c] = round(w * s / total * 100, 1)
    return out


def explain(machine_id: str, severities: Dict[str, float],
            df: pd.DataFrame, baseline) -> str:
    if not severities:
        return f"{machine_id}: no significant sensor deviation."
    worst_comp = max(severities, key=severities.get)
    worst_sev = severities[worst_comp]
    if worst_sev < 0.15:
        return f"{machine_id}: all sensor signals within expected workload bands."

    parts = [FRIENDLY.get(worst_comp, worst_comp)]
    contributors = sorted(severities.items(), key=lambda x: -x[1])[:2]
    driver_txt = ", ".join(f"{FRIENDLY.get(c, c)} ({int(s*100)}%)"
                            for c, s in contributors if s > 0.1)

    return (f"{machine_id}: developing {parts[0]}. "
            f"Primary drivers: {driver_txt}. "
            f"Compared against workload-conditioned baselines.")