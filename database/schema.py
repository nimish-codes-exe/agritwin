"""All table definitions. Executed once on first launch."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS farms (
    farm_id       TEXT PRIMARY KEY,
    farm_name     TEXT NOT NULL,
    region        TEXT,
    total_area_ha REAL
);

CREATE TABLE IF NOT EXISTS machines (
    machine_id    TEXT PRIMARY KEY,
    model         TEXT NOT NULL,
    farm_id       TEXT REFERENCES farms(farm_id),
    acquired_year INTEGER,
    status        TEXT DEFAULT 'operational'
);

CREATE TABLE IF NOT EXISTS telemetry (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id     TEXT NOT NULL REFERENCES machines(machine_id),
    ts             TEXT NOT NULL,
    engine_temp_c  REAL,
    oil_pressure_kpa REAL,
    engine_rpm     REAL,
    vibration_mm_s REAL,
    fuel_consumption_lh REAL,
    engine_load_pct REAL,
    coolant_temp_c REAL,
    operating_hours REAL,
    operating_status TEXT,
    sensor_valid   INTEGER DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_telemetry_machine_ts ON telemetry(machine_id, ts);

CREATE TABLE IF NOT EXISTS machine_states (
    machine_id     TEXT PRIMARY KEY REFERENCES machines(machine_id),
    updated_at     TEXT,
    health_score   REAL,
    risk_score     REAL,
    reliability    REAL,
    status         TEXT,
    degradation_json TEXT
);

CREATE TABLE IF NOT EXISTS fault_events (
    event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id  TEXT REFERENCES machines(machine_id),
    ts          TEXT,
    component   TEXT,
    severity    TEXT,
    reason      TEXT,
    resolved    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS maintenance_records (
    record_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id   TEXT REFERENCES machines(machine_id),
    completed_at TEXT,
    task         TEXT,
    cost_usd     REAL,
    notes        TEXT
);

CREATE TABLE IF NOT EXISTS technicians (
    tech_id      TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    skills       TEXT,           -- comma-separated component skills
    available    INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS spare_parts (
    part_id     TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    unit_cost   REAL
);

CREATE TABLE IF NOT EXISTS spare_part_inventory (
    part_id     TEXT PRIMARY KEY REFERENCES spare_parts(part_id),
    quantity    INTEGER DEFAULT 0,
    reorder_level INTEGER DEFAULT 2
);

CREATE TABLE IF NOT EXISTS harvest_calendar (
    harvest_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id       TEXT REFERENCES farms(farm_id),
    start_date    TEXT,
    end_date      TEXT,
    priority      INTEGER DEFAULT 5,   -- 1=highest
    required_machines INTEGER
);

CREATE TABLE IF NOT EXISTS maintenance_schedules (
    schedule_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id   TEXT REFERENCES machines(machine_id),
    tech_id      TEXT REFERENCES technicians(tech_id),
    scheduled_at TEXT,
    duration_h   REAL,
    task         TEXT,
    status       TEXT DEFAULT 'pending',
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS simulation_scenarios (
    scenario_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT,
    params_json  TEXT,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);
"""