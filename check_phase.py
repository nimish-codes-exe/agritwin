"""
Smoke-test for Phase 1. Run: python check_phase1.py
Expected: prints 12 rows with health/risk/reliability, then 3 scenario projections.
"""
import time
from datetime import datetime

from config import SIM_MACHINES, SIM_HISTORY_DAYS
from database import init_database
from database import seed
from database import repository as repo
from simulation.fault_simulator import FaultSimulator
from simulation.telemetry_generator import TelemetryGenerator
from simulation.scenario_engine import ScenarioEngine
from digital_twin.state_manager import rebuild_all
from intelligence.forecasting import forecast_severity


def banner(msg):
    print("\n" + "=" * 70)
    print(msg)
    print("=" * 70)


def main():
    banner("STEP 1 — Init DB and seed")
    init_database()
    seed.ensure_seeded()
    print("Machines:", len(repo.list_machines()))
    print("Farms:",    len(repo.list_farms()))
    print("Techs:",    len(repo.list_technicians()))
    print("Parts:",    len(repo.list_parts()))
    print("Harvests:", len(repo.list_harvests()))

    banner("STEP 2 — Generate 60 days of history (first launch only)")
    if repo.table_count("telemetry") == 0:
        machine_ids = [m["machine_id"] for m in repo.list_machines()]
        fs = FaultSimulator(machine_ids)
        gen = TelemetryGenerator(fs, seed=1)
        t0 = time.time()
        rows = gen.generate_history(machine_ids, days=SIM_HISTORY_DAYS, tick_hours=2)
        print(f"Generated {len(rows)} telemetry rows in {time.time()-t0:.2f}s")
        repo.insert_telemetry(rows)
    else:
        print(f"Skipping — telemetry table already has "
              f"{repo.table_count('telemetry')} rows")

    banner("STEP 3 — Build digital twins for all machines")
    t0 = time.time()
    twins = rebuild_all()
    print(f"Built {len(twins)} twins in {time.time()-t0:.2f}s")

    banner("STEP 4 — Twin summary table")
    print(f"{'MACHINE':<14}{'STATUS':<14}{'HEALTH':>8}{'RISK':>8}"
          f"{'RELIAB':>8}   EXPLANATION")
    for mid, tw in sorted(twins.items()):
        print(f"{mid:<14}{tw.status:<14}{tw.health:>8.1f}{tw.risk:>8.1f}"
              f"{tw.reliability:>8.1f}   {tw.explanation[:60]}...")

    banner("STEP 5 — Persistence check (read back from DB)")
    saved = repo.fetch_machine_states()
    print(f"machine_states rows: {len(saved)}")
    if saved:
        s = saved[0]
        print(f"Example: {s['machine_id']}  health={s['health_score']} "
              f"risk={s['risk_score']} status={s['status']}")

    banner("STEP 6 — Scenario engine (What-If) on worst machine")
    worst = max(twins.values(), key=lambda t: t.risk)
    print(f"Testing on: {worst.machine_id}  (current risk {worst.risk})")
    engine = ScenarioEngine([worst.machine_id])
    for policy in ("repair_now", "delay_48h", "continue"):
        proj = engine.run_projection(worst.machine_id, worst.severities,
                                     horizon_hours=24, policy=policy)
        temps = [p["engine_temp_c"] for p in proj]
        vibs  = [p["vibration_mm_s"] for p in proj]
        print(f"  {policy:<12} temp[min={min(temps):.1f} max={max(temps):.1f}] "
              f"vib[min={min(vibs):.2f} max={max(vibs):.2f}]")

    banner("STEP 7 — Fault injection demo")
    fs = FaultSimulator([worst.machine_id])
    gen = TelemetryGenerator(fs, seed=42)
    before = gen.generate_tick(worst.machine_id, datetime.utcnow())
    print(f"BEFORE inject: engine_temp={before['engine_temp_c']} "
          f"coolant={before['coolant_temp_c']}")
    fs.inject_fault(worst.machine_id, "cooling")
    for i in range(120):  # advance 120 hours
        after = gen.generate_tick(worst.machine_id, datetime.utcnow(), hours=1.0)
    print(f"AFTER 120h:    engine_temp={after['engine_temp_c']} "
          f"coolant={after['coolant_temp_c']}  (should be elevated)")

    banner("STEP 8 — Forecast (deterministic)")
    hist = [max(0.01, min(0.99, worst.severities.get('cooling', 0) * (0.3 + 0.02 * i)))
            for i in range(20)]
    fc = forecast_severity(hist, horizon=24)
    print(f"cooling severity forecast (24h): min={min(fc):.2f} max={max(fc):.2f}")

    banner("✅ ALL PHASE 1 CHECKS PASSED")


if __name__ == "__main__":
    main()