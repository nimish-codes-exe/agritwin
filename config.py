"""Central configuration for AgriTwin AI."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "agritwin.db"

# Simulation
SIM_MACHINES = 12
SIM_HISTORY_DAYS = 60
SIM_HOURS_PER_TICK = 1
SIM_FUEL_COST_PER_L = 1.5

# Thresholds (workload-adjusted at runtime)
THRESHOLDS = {
    "engine_temp_c":      {"nominal": (75, 95),  "warn": 100, "critical": 108},
    "oil_pressure_kpa":   {"nominal": (280, 420),"warn": 220, "critical": 180},
    "vibration_mm_s":     {"nominal": (1.5, 4.0),"warn": 6.0, "critical": 8.5},
    "coolant_temp_c":     {"nominal": (70, 90),  "warn": 98,  "critical": 105},
    "fuel_consumption_lh":{"nominal": (4.0, 9.0),"warn": 11.0,"critical": 13.5},
}

STATUS_LABELS = ["Healthy", "Warning", "High Risk", "Critical"]

# Maintenance cost model (USD)
COST = {
    "tech_hour": 45,
    "downtime_per_hour": 120,
    "failure_multiplier": 4.0,
    "parts_pressure_base": 200,
}

# Scheduler
TECH_WORK_HOURS = 8
MAX_JOBS_PER_TECH_PER_DAY = 2