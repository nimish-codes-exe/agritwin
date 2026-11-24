"""Formats the output of simulate_strategies for the UI table."""
import pandas as pd
from .performance_metrics import STRATEGIES


def comparison_table(sim: dict) -> pd.DataFrame:
    r = sim["results"]
    return pd.DataFrame([
        {
            "Strategy": s,
            "Avg Downtime (h)": r[s]["avg_downtime"],
            "Avg Cost (USD)":   r[s]["avg_cost"],
            "Detection Rate (%)": r[s]["detection_rate"],
            "False Alarm Rate (%)": r[s]["false_alarm_rate"],
        }
        for s in STRATEGIES
    ])