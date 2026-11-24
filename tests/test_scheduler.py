from optimization.maintenance_scheduler import run_scheduler


def test_scheduler_defers_when_no_techs():
    states = [{"machine_id": "M1", "risk_score": 90, "status": "Critical",
               "degradation": {"cooling": 0.9}}]
    machines = [{"machine_id": "M1", "farm_id": "F1"}]
    schedule = run_scheduler(states, machines, [], [], [], [])
    assert schedule[0]["decision"] == "Deferred"


def test_scheduler_assigns_with_resource():
    states = [{"machine_id": "M1", "risk_score": 90, "status": "Critical",
               "degradation": {"cooling": 0.9}}]
    machines = [{"machine_id": "M1", "farm_id": "F1"}]
    techs = [{"tech_id": "T1", "name": "Alice", "skills": "cooling", "available": 1}]
    parts = [{"part_id": "PART-COOL", "name": "Coolant", "unit_cost": 100,
              "quantity": 2, "reorder_level": 1}]
    schedule = run_scheduler(states, machines, [], techs, parts, [])
    assert schedule[0]["decision"] == "Scheduled"
    assert schedule[0]["tech"] == "Alice"