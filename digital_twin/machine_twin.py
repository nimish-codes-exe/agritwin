"""One twin = one machine. Combines baseline, degradation, risk, uncertainty."""
from dataclasses import dataclass, field
from typing import Dict
import pandas as pd

from .workload_baseline import WorkloadBaseline
from .degradation_engine import DegradationEngine
from intelligence.risk_engine import compute_risk, classify_status
from intelligence.uncertainty_engine import compute_reliability
from intelligence.explainability import explain


@dataclass
class MachineTwin:
    machine_id: str
    baseline: WorkloadBaseline
    degradation_engine: DegradationEngine
    severities: Dict[str, float] = field(default_factory=dict)
    risk: float = 0.0
    health: float = 100.0
    reliability: float = 100.0
    status: str = "Healthy"
    explanation: str = ""

    @classmethod
    def build(cls, machine_id: str, history_df: pd.DataFrame) -> "MachineTwin":
        baseline = WorkloadBaseline().fit(history_df)
        engine = DegradationEngine(baseline)
        twin = cls(machine_id=machine_id, baseline=baseline, degradation_engine=engine)
        twin.update(history_df)
        return twin

    def update(self, history_df: pd.DataFrame) -> None:
        self.severities = self.degradation_engine.compute(history_df)
        self.risk = compute_risk(self.severities)
        self.reliability = compute_reliability(history_df)
        self.health = round(100 - self.risk * 0.85, 1)
        self.status = classify_status(self.risk, self.reliability)
        self.explanation = explain(self.machine_id, self.severities, history_df,
                                    self.baseline)