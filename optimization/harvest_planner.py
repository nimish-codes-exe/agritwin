"""Boosts a machine's priority if its farm has an upcoming harvest."""
from datetime import datetime, timedelta
from typing import List, Dict


def harvest_urgency_multiplier(machine_id: str, farm_id: str,
                                harvests: List[Dict]) -> float:
    """Return a multiplier in [1.0, 1.8] based on harvest proximity."""
    now = datetime.utcnow().date()
    mult = 1.0
    for h in harvests:
        if h["farm_id"] != farm_id:
            continue
        start = datetime.fromisoformat(h["start_date"]).date()
        days_to = (start - now).days
        if 0 <= days_to <= 14:
            # closer harvest = higher urgency (priority 1 -> biggest boost)
            pr_factor = (6 - h["priority"]) / 5.0
            proximity = 1.0 - days_to / 14.0
            mult = max(mult, 1.0 + 0.8 * pr_factor * proximity)
    return round(mult, 2)