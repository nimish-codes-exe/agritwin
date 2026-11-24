"""
Greedy constrained scheduler.

Priority = risk_score × harvest_multiplier × machine_criticality
Assign tech + parts; schedule next business-hour slot.
"""
from datetime import datetime, timedelta
from typing import List, Dict
from config import COST, TECH_WORK_HOURS
from .resource_allocator import allocate_technician, allocate_parts
from .harvest_planner import harvest_urgency_multiplier


MACHINE_CRITICALITY = {"TRACTOR-001": 1.2, "TRACTOR-002": 1.1}  # examples


def _expected_duration(component: str) -> float:
    return {"cooling": 3.0, "engine_heat": 4.0,
            "oil_pressure": 2.5, "vibration": 3.5}.get(component, 3.0)


def run_scheduler(states: List[Dict], machines: List[Dict],
                  farms: List[Dict], technicians: List[Dict],
                  parts: List[Dict], harvests: List[Dict]) -> List[Dict]:
    """
    Input states: from machine_states table (machine_id, risk_score, status,
    degradation dict).
    Returns ordered list of scheduling decisions with explanations.
    """
    machine_to_farm = {m["machine_id"]: m["farm_id"] for m in machines}

    candidates = []
    for s in states:
        if s["status"] in ("Healthy", "Low Confidence"):
            continue
        deg = s.get("degradation") or {}
        if not deg:
            continue
        worst_comp = max(deg, key=deg.get)
        farm_id = machine_to_farm.get(s["machine_id"])
        hmul = harvest_urgency_multiplier(s["machine_id"], farm_id, harvests)
        cmul = MACHINE_CRITICALITY.get(s["machine_id"], 1.0)
        priority = s["risk_score"] * hmul * cmul
        candidates.append({
            "machine_id": s["machine_id"],
            "risk": s["risk_score"],
            "status": s["status"],
            "worst_component": worst_comp,
            "harvest_mult": hmul,
            "criticality": cmul,
            "priority": priority,
        })

    candidates.sort(key=lambda x: -x["priority"])

    schedule = []
    booked_techs = set()
    slot = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)
    parts_left = {p["part_id"]: p["quantity"] for p in parts}

    for c in candidates:
        tech = allocate_technician(c["worst_component"], technicians, booked_techs)
        if tech is None:
            schedule.append({**c, "decision": "Deferred",
                             "reason": "No technician available with required skill",
                             "tech": None, "eta": None, "parts_ok": False,
                             "duration_h": None, "est_cost": None})
            continue

        comp_part = {"cooling": "PART-COOL", "engine_heat": "PART-FAN",
                     "oil_pressure": "PART-OIL", "vibration": "PART-VIB"}.get(c["worst_component"])

        parts_ok = True
        parts_note = "All parts in stock"
        if comp_part:
            if parts_left.get(comp_part, 0) <= 0:
                parts_ok = False
                parts_note = f"Backordered: {comp_part}"
            else:
                parts_left[comp_part] -= 1

        dur = _expected_duration(c["worst_component"])
        cost = COST["tech_hour"] * dur + COST["downtime_per_hour"] * dur

        decision = "Scheduled" if parts_ok else "Partial"
        reason = (f"Risk {c['risk']:.0f}, harvest boost ×{c['harvest_mult']:.2f}, "
                  f"{parts_note}")
        schedule.append({
            **c,
            "decision": decision,
            "reason": reason,
            "tech": tech["name"],
            "tech_id": tech["tech_id"],
            "eta": slot.isoformat(timespec="minutes"),
            "parts_ok": parts_ok,
            "duration_h": dur,
            "est_cost": cost,
        })
        if parts_ok:
            booked_techs.add(tech["tech_id"])
        slot += timedelta(hours=dur + 1)

    return schedule