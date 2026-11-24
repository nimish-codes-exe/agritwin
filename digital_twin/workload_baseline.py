"""
Workload-conditioned baselines.

A 100% loaded tractor will ALWAYS have higher temps than an idle one.
We must compare a sensor reading against the expected value for its load.
"""
import numpy as np
import pandas as pd
from typing import Dict


LOAD_BINS = [0, 30, 50, 70, 85, 101]
LOAD_LABELS = ["idle", "light", "medium", "heavy", "max"]


class WorkloadBaseline:
    """Learns expected sensor values per load bin from history."""

    SENSORS = ["engine_temp_c", "oil_pressure_kpa", "vibration_mm_s",
               "coolant_temp_c", "fuel_consumption_lh"]

    def __init__(self):
        self.baselines: Dict[str, Dict[str, float]] = {}
        self.stds: Dict[str, Dict[str, float]] = {}

    def fit(self, df: pd.DataFrame) -> "WorkloadBaseline":
        if df.empty:
            return self
        df = df.copy()
        df["load_bin"] = pd.cut(df["engine_load_pct"], LOAD_BINS,
                                labels=LOAD_LABELS, right=False)
        for sensor in self.SENSORS:
            self.baselines[sensor] = {}
            self.stds[sensor] = {}
            for lb in LOAD_LABELS:
                mask = df["load_bin"] == lb
                if mask.sum() >= 3:
                    self.baselines[sensor][lb] = float(df.loc[mask, sensor].mean())
                    self.stds[sensor][lb] = float(df.loc[mask, sensor].std(ddof=0) or 1.0)
        return self

    def expected(self, sensor: str, load_pct: float) -> float:
        lb = self._bin(load_pct)
        return self.baselines.get(sensor, {}).get(lb, 0.0)

    def z_score(self, sensor: str, load_pct: float, value: float) -> float:
        lb = self._bin(load_pct)
        mu = self.baselines.get(sensor, {}).get(lb)
        sd = self.stds.get(sensor, {}).get(lb, 1.0)
        if mu is None:
            return 0.0
        return (value - mu) / (sd if sd > 1e-6 else 1.0)

    @staticmethod
    def _bin(load_pct: float) -> str:
        for i, edge in enumerate(LOAD_BINS[1:]):
            if load_pct < edge:
                return LOAD_LABELS[i]
        return LOAD_LABELS[-1]