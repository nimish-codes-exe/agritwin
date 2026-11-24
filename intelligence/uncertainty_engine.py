"""
Reliability score (0..100). Distinct from risk.

Penalties:
  - missing readings
  - stuck / invalid sensors
  - too-few samples
  - conflicting sensor signals
"""
import pandas as pd


def compute_reliability(df: pd.DataFrame) -> float:
    if df.empty or len(df) < 5:
        return 15.0
    score = 100.0
    recent = df.tail(30)

    # missing values
    miss_frac = recent[["engine_temp_c", "oil_pressure_kpa",
                        "vibration_mm_s", "coolant_temp_c"]].isna().mean().mean()
    score -= miss_frac * 60

    # invalid sensor flags
    if "sensor_valid" in recent:
        invalid_frac = 1 - recent["sensor_valid"].mean()
        score -= invalid_frac * 50

    # not enough samples
    if len(recent) < 10:
        score -= (10 - len(recent)) * 3

    # conflict: engine heat high but coolant low  → suspicious
    try:
        if recent["engine_temp_c"].iloc[-1] > 100 and recent["coolant_temp_c"].iloc[-1] < 75:
            score -= 15
    except Exception:
        pass

    return round(max(0, min(100, score)), 1)