"""Pick best technician + verify part availability."""
from typing import List, Dict, Optional


SKILL_REQUIRED_BY_COMPONENT = {
    "engine_heat":   "engine",
    "cooling":       "cooling",
    "oil_pressure":  "oil_pressure",
    "vibration":     "vibration",
}


def allocate_technician(component: str, technicians: List[Dict],
                        already_booked: set) -> Optional[Dict]:
    skill = SKILL_REQUIRED_BY_COMPONENT.get(component, "engine")
    for t in technicians:
        if t["tech_id"] in already_booked:
            continue
        if not t["available"]:
            continue
        skills = (t["skills"] or "").split(",")
        if skill in skills:
            return t
    # fallback: any available tech
    for t in technicians:
        if t["available"] and t["tech_id"] not in already_booked:
            return t
    return None


def allocate_parts(component: str, parts: List[Dict]) -> Optional[Dict]:
    mapping = {
        "cooling":      "PART-COOL",
        "engine_heat":  "PART-FAN",
        "oil_pressure": "PART-OIL",
        "vibration":    "PART-VIB",
    }
    need = mapping.get(component)
    for p in parts:
        if p["part_id"] == need and p["quantity"] > 0:
            return p
    return None