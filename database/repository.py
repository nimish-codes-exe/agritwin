"""All CRUD. No UI imports. No business logic beyond mapping."""
import json
from datetime import datetime
from typing import Optional, List, Dict
from .connection import db_cursor


# ---------- FARMS ----------
def upsert_farm(farm_id, farm_name, region, total_area_ha):
    with db_cursor() as c:
        c.execute(
            "INSERT OR IGNORE INTO farms VALUES (?,?,?,?)",
            (farm_id, farm_name, region, total_area_ha),
        )


def list_farms() -> List[Dict]:
    with db_cursor() as c:
        return [dict(r) for r in c.execute("SELECT * FROM farms").fetchall()]


# ---------- MACHINES ----------
def upsert_machine(machine_id, model, farm_id, acquired_year):
    with db_cursor() as c:
        c.execute(
            "INSERT OR IGNORE INTO machines VALUES (?,?,?,?, 'operational')",
            (machine_id, model, farm_id, acquired_year),
        )


def list_machines() -> List[Dict]:
    with db_cursor() as c:
        return [dict(r) for r in c.execute("SELECT * FROM machines ORDER BY machine_id").fetchall()]


# ---------- TELEMETRY ----------
TELEMETRY_COLS = [
    "machine_id", "ts", "engine_temp_c", "oil_pressure_kpa", "engine_rpm",
    "vibration_mm_s", "fuel_consumption_lh", "engine_load_pct",
    "coolant_temp_c", "operating_hours", "operating_status", "sensor_valid",
]


def insert_telemetry(rows: List[dict]) -> None:
    if not rows:
        return
    with db_cursor() as c:
        c.executemany(
            f"INSERT INTO telemetry ({','.join(TELEMETRY_COLS)}) "
            f"VALUES ({','.join(['?']*len(TELEMETRY_COLS))})",
            [tuple(r.get(k) for k in TELEMETRY_COLS) for r in rows],
        )


def fetch_telemetry(machine_id: str, limit: int = 500) -> List[Dict]:
    with db_cursor() as c:
        rows = c.execute(
            "SELECT * FROM telemetry WHERE machine_id=? ORDER BY ts DESC LIMIT ?",
            (machine_id, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]


def fetch_latest_telemetry_all() -> List[Dict]:
    with db_cursor() as c:
        rows = c.execute("""
            SELECT t.* FROM telemetry t
            JOIN (SELECT machine_id, MAX(ts) AS mts FROM telemetry GROUP BY machine_id) m
              ON t.machine_id = m.machine_id AND t.ts = m.mts
        """).fetchall()
        return [dict(r) for r in rows]


# ---------- MACHINE STATE ----------
def upsert_machine_state(machine_id, health, risk, reliability, status, degradation: dict):
    with db_cursor() as c:
        c.execute("""
            INSERT INTO machine_states(machine_id, updated_at, health_score, risk_score,
                                       reliability, status, degradation_json)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(machine_id) DO UPDATE SET
                updated_at=excluded.updated_at,
                health_score=excluded.health_score,
                risk_score=excluded.risk_score,
                reliability=excluded.reliability,
                status=excluded.status,
                degradation_json=excluded.degradation_json
        """, (machine_id, datetime.utcnow().isoformat(), health, risk,
              reliability, status, json.dumps(degradation)))


def fetch_machine_states() -> List[Dict]:
    with db_cursor() as c:
        rows = c.execute("SELECT * FROM machine_states").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["degradation"] = json.loads(d.pop("degradation_json") or "{}")
            out.append(d)
        return out


# ---------- FAULT EVENTS ----------
def log_fault(machine_id, component, severity, reason):
    with db_cursor() as c:
        c.execute(
            "INSERT INTO fault_events(machine_id, ts, component, severity, reason) "
            "VALUES (?,?,?,?,?)",
            (machine_id, datetime.utcnow().isoformat(), component, severity, reason),
        )


def list_faults(limit: int = 20) -> List[Dict]:
    with db_cursor() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM fault_events ORDER BY event_id DESC LIMIT ?", (limit,)
        ).fetchall()]


# ---------- TECHNICIANS ----------
def upsert_technician(tech_id, name, skills):
    with db_cursor() as c:
        c.execute(
            "INSERT OR IGNORE INTO technicians(tech_id,name,skills,available) VALUES (?,?,?,1)",
            (tech_id, name, ",".join(skills)),
        )


def list_technicians() -> List[Dict]:
    with db_cursor() as c:
        return [dict(r) for r in c.execute("SELECT * FROM technicians").fetchall()]


def set_tech_availability(tech_id, available: bool):
    with db_cursor() as c:
        c.execute("UPDATE technicians SET available=? WHERE tech_id=?",
                  (1 if available else 0, tech_id))


# ---------- PARTS ----------
def upsert_part(part_id, name, unit_cost, qty, reorder_level):
    with db_cursor() as c:
        c.execute("INSERT OR IGNORE INTO spare_parts VALUES (?,?,?)",
                  (part_id, name, unit_cost))
        c.execute("INSERT OR IGNORE INTO spare_part_inventory VALUES (?,?,?)",
                  (part_id, qty, reorder_level))


def list_parts() -> List[Dict]:
    with db_cursor() as c:
        rows = c.execute("""
            SELECT p.part_id, p.name, p.unit_cost, i.quantity, i.reorder_level
            FROM spare_parts p JOIN spare_part_inventory i USING(part_id)
        """).fetchall()
        return [dict(r) for r in rows]


def consume_part(part_id, qty=1) -> bool:
    with db_cursor() as c:
        cur = c.execute("SELECT quantity FROM spare_part_inventory WHERE part_id=?", (part_id,))
        row = cur.fetchone()
        if not row or row["quantity"] < qty:
            return False
        c.execute("UPDATE spare_part_inventory SET quantity=quantity-? WHERE part_id=?",
                  (qty, part_id))
        return True


# ---------- HARVEST ----------
def upsert_harvest(farm_id, start, end, priority, required_machines):
    with db_cursor() as c:
        c.execute("""
            INSERT INTO harvest_calendar(farm_id,start_date,end_date,priority,required_machines)
            VALUES (?,?,?,?,?)
        """, (farm_id, start, end, priority, required_machines))


def list_harvests() -> List[Dict]:
    with db_cursor() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM harvest_calendar ORDER BY start_date").fetchall()]


# ---------- MAINTENANCE SCHEDULE ----------
def insert_schedule(machine_id, tech_id, scheduled_at, duration_h, task):
    with db_cursor() as c:
        c.execute("""
            INSERT INTO maintenance_schedules(machine_id,tech_id,scheduled_at,duration_h,task)
            VALUES (?,?,?,?,?)
        """, (machine_id, tech_id, scheduled_at, duration_h, task))


def list_schedules() -> List[Dict]:
    with db_cursor() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM maintenance_schedules ORDER BY scheduled_at").fetchall()]


def clear_pending_schedules():
    with db_cursor() as c:
        c.execute("DELETE FROM maintenance_schedules WHERE status='pending'")


# ---------- COUNTS (for seed guard) ----------
def table_count(name: str) -> int:
    with db_cursor() as c:
        return c.execute(f"SELECT COUNT(*) AS n FROM {name}").fetchone()["n"]