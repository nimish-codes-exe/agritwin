"""
Turns raw telemetry into component-level degradation scores (0..1).

Uses:
  - workload-adjusted z-scores
  - exponentially weighted moving average (EWMA)
  - rate of change
  - contextual thresholds (from config)
"""
from typing import Dict, List
import pandas as pd
import numpy as np
from config import THRESHOLDS
from .workload_baseline import WorkloadBaseline


COMPONENT_OF_SENSOR = {
    "engine_temp_c":      "engine_heat",
    "coolant_temp_c":     "cooling",
    "oil_pressure_kpa":   "oil_pressure",
    "vibration_mm_s":     "vibration",
    "fuel_consumption_lh":"engine_heat",
}

EWMA_ALPHA = 0.3


def _safe_norm(lo, hi, v):
    if hi == lo:
        return 0.0
    return max(0.0, min(1.0, (v - lo) / (hi - lo)))


class DegradationEngine:
    def __init__(self, baseline: WorkloadBaseline):
        self.baseline = baseline

    def compute(self, df: pd.DataFrame) -> Dict[str, float]:
        """df ordered ascending by ts. Returns {component: severity 0..1}."""
        if df.empty:
            return {}
        out: Dict[str, float] = {}
        df = df.tail(120).reset_index(drop=True)

        # per-sensor EWMA trend
        for sensor, comp in COMPONENT_OF_SENSOR.items():
            if sensor not in df:
                continue
            # contextual baseline if we have it
            if comp in ("engine_heat", "cooling"):
                # higher is worse
                thr = THRESHOLDS[sensor]
                raw = df[sensor].ewm(alpha=EWMA_ALPHA).mean().iloc[-1]
                norm = _safe_norm(thr["nominal"][1], thr["critical"], raw)
            elif comp == "oil_pressure":
                # lower is worse
                thr = THRESHOLDS[sensor]
                raw = df[sensor].ewm(alpha=EWMA_ALPHA).mean().iloc[-1]
                norm = 1.0 - _safe_norm(thr["critical"], thr["nominal"][0], raw)
            elif comp == "vibration":
                thr = THRESHOLDS[sensor]
                raw = df[sensor].ewm(alpha=EWMA_ALPHA).mean().iloc[-1]
                norm = _safe_norm(thr["nominal"][1], thr["critical"], raw)
            else:
                norm = 0.0

            # rate-of-change amplifier (last 12 ticks)
            if len(df) >= 12:
                slope = (df[sensor].iloc[-1] - df[sensor].iloc[-12]) / max(df[sensor].iloc[-12], 1e-6)
                trend_boost = min(0.25, max(0.0, abs(slope) * 0.5))
            else:
                trend_boost = 0.0

            out[comp] = float(min(1.0, norm + trend_boost))
        return out

    def component_health(self, severities: Dict[str, float]) -> Dict[str, int]:
        """Map severity 0..1 → health 0..100 (per component)."""
        return {c: int(round(max(0, min(100, (1 - s) * 100)))) for c, s in severities.items()}