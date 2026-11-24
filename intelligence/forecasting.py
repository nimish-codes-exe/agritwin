"""Deterministic linear severity forecast — no ML."""
from typing import List


def forecast_severity(history_severities: List[float], horizon: int = 24) -> List[float]:
    if len(history_severities) < 3:
        return [history_severities[-1] if history_severities else 0.0] * horizon
    # simple least-squares slope on last N
    n = min(len(history_severities), 30)
    ys = history_severities[-n:]
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs) or 1e-9
    slope = num / den
    last = ys[-1]
    return [max(0.0, min(1.0, last + slope * h)) for h in range(1, horizon + 1)]