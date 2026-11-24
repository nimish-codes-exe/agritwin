"""Contextual z-score anomaly detection on a telemetry window."""
import pandas as pd
from typing import Dict
from digital_twin.workload_baseline import WorkloadBaseline


def detect_anomalies(df: pd.DataFrame, baseline: WorkloadBaseline,
                     z_threshold: float = 2.5) -> Dict[str, dict]:
    if df.empty:
        return {}
    latest = df.iloc[-1]
    result = {}
    for sensor in WorkloadBaseline.SENSORS:
        if sensor not in df or pd.isna(latest[sensor]):
            continue
        z = baseline.z_score(sensor, latest["engine_load_pct"], latest[sensor])
        result[sensor] = {
            "value": float(latest[sensor]),
            "expected": round(baseline.expected(sensor, latest["engine_load_pct"]), 2),
            "z": round(z, 2),
            "anomalous": abs(z) > z_threshold,
        }
    return result