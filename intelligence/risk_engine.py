"""
Deterministic risk scoring.

Risk = weighted sum of component severities with hard escalation rules.
No training. All weights fixed and documented.
"""
from typing import Dict

COMPONENT_WEIGHTS = {
    "engine_heat":   0.30,
    "cooling":       0.25,
    "oil_pressure":  0.25,
    "vibration":     0.20,
}


def compute_risk(severities: Dict[str, float]) -> float:
    """0..100."""
    if not severities:
        return 0.0
    s = 0.0
    for comp, sev in severities.items():
        s += COMPONENT_WEIGHTS.get(comp, 0.15) * min(1.0, max(0.0, sev))
    raw = s * 100
    # escalation: if ANY component is >85% severity, risk jumps
    worst = max(severities.values()) if severities else 0
    if worst > 0.85:
        raw = max(raw, 85.0)
    return round(min(100.0, raw), 1)


def classify_status(risk: float, reliability: float) -> str:
    if reliability < 40:
        return "Low Confidence"
    if risk >= 75:
        return "Critical"
    if risk >= 50:
        return "High Risk"
    if risk >= 25:
        return "Warning"
    return "Healthy"