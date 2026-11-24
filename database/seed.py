"""Idempotent seed data for first launch."""
import random
from datetime import datetime, timedelta
from . import repository as repo


FARM_TEMPLATE = [
    ("FARM-N", "North Ridge Farms", "North", 420.0),
    ("FARM-S", "South Valley Co-op", "South", 310.0),
    ("FARM-E", "East Meadow Estates", "East", 260.0),
]

MACHINE_MODELS = ["JohnDeere 6120M", "Mahindra 575 DI", "Massey 241 DI",
                  "New Holland TD5", "Kubota MU5501"]

TECH_TEMPLATE = [
    ("TECH-1", "Alice Rivera", ["cooling", "engine"]),
    ("TECH-2", "Bob Chen",     ["vibration", "engine"]),
    ("TECH-3", "Carla Diaz",   ["oil_pressure", "cooling"]),
    ("TECH-4", "Dan Okafor",   ["engine", "vibration", "cooling"]),
]

PARTS_TEMPLATE = [
    ("PART-COOL", "Coolant Pump",       180.0, 4, 2),
    ("PART-OIL",  "Oil Filter Kit",      40.0, 10, 3),
    ("PART-VIB",  "Engine Mount Set",   260.0, 3, 2),
    ("PART-FAN",  "Cooling Fan Assembly",95.0, 6, 2),
    ("PART-SENS", "Temperature Sensor",  55.0, 8, 3),
]


def ensure_seeded() -> None:
    """Insert base data only if the DB is empty."""
    if repo.table_count("farms") == 0:
        for f in FARM_TEMPLATE:
            repo.upsert_farm(*f)
    if repo.table_count("machines") == 0:
        random.seed(7)
        for i in range(12):
            mid = f"TRACTOR-{i+1:03d}"
            farm = FARM_TEMPLATE[i % 3][0]
            repo.upsert_machine(mid, random.choice(MACHINE_MODELS), farm, 2018 + i % 6)
    if repo.table_count("technicians") == 0:
        for t in TECH_TEMPLATE:
            repo.upsert_technician(*t)
    if repo.table_count("spare_parts") == 0:
        for p in PARTS_TEMPLATE:
            repo.upsert_part(*p)
    if repo.table_count("harvest_calendar") == 0:
        now = datetime.utcnow()
        repo.upsert_harvest("FARM-N", (now + timedelta(days=10)).date().isoformat(),
                            (now + timedelta(days=20)).date().isoformat(), 1, 4)
        repo.upsert_harvest("FARM-S", (now + timedelta(days=25)).date().isoformat(),
                            (now + timedelta(days=35)).date().isoformat(), 3, 3)
        repo.upsert_harvest("FARM-E", (now + timedelta(days=40)).date().isoformat(),
                            (now + timedelta(days=50)).date().isoformat(), 5, 2)