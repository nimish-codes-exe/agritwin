from datetime import datetime
from simulation.fault_simulator import FaultSimulator
from simulation.telemetry_generator import TelemetryGenerator


def test_inject_fault_raises_temp():
    fs = FaultSimulator(["M1"])
    gen = TelemetryGenerator(fs, seed=1)
    before = gen.generate_tick("M1", datetime.utcnow())
    fs.inject_fault("M1", "cooling")
    for _ in range(120):
        after = gen.generate_tick("M1", datetime.utcnow(), hours=1.0)
    assert after["coolant_temp_c"] > before["coolant_temp_c"]