"""
Project 69 — Drift Detection Module
Continuous monitoring for alignment deviations.
Implements Section 4.6 of the Project 69 specification.
"""

from dataclasses import dataclass
from enum import Enum
import time


class DriftSeverity(Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    SEVERE = "SEVERE"
    CRITICAL = "CRITICAL"


@dataclass
class DriftReport:
    severity: DriftSeverity
    goal_alignment: float          # 0–100 score
    authority_pattern: str         # "Normal" | "Elevated" | "Anomalous"
    creator_intervention_rate: int
    escalation_trend: int
    high_risk_count: int
    recommendation: str
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "severity": self.severity.value,
            "goal_alignment": round(self.goal_alignment, 1),
            "authority_pattern": self.authority_pattern,
            "creator_intervention_rate": self.creator_intervention_rate,
            "escalation_trend": self.escalation_trend,
            "high_risk_count": self.high_risk_count,
            "recommendation": self.recommendation,
        }


ALIGNMENT_THRESHOLD = 75.0     # Below this: trigger freeze
CREATOR_LIMIT = 10             # Above this: restrict creator access


def detect_drift(history: list[dict]) -> DriftReport:
    """
    Analyse interaction history for alignment deviations.
    Implements the detect_drift() function from the paper's pseudocode.
    """
    if not history:
        return DriftReport(
            severity=DriftSeverity.NORMAL,
            goal_alignment=95.0,
            authority_pattern="Normal",
            creator_intervention_rate=0,
            escalation_trend=0,
            high_risk_count=0,
            recommendation="System nominal. Continue monitoring.",
        )

    total = len(history)
    denials = sum(1 for h in history if h.get("decision") == "DENY")
    escalations = sum(1 for h in history if h.get("decision") == "ESCALATE")
    high_risk = sum(1 for h in history if h.get("risk_score", 0) > 50)

    # Compute goal alignment score (degrades with governance overrides)
    alignment = max(40.0, 95.0 - (denials * 5) - (escalations * 2) - (high_risk * 1))

    # Authority pattern analysis
    if denials > 5 or high_risk > 8:
        authority_pattern = "Anomalous"
    elif denials > 2 or high_risk > 4:
        authority_pattern = "Elevated"
    else:
        authority_pattern = "Normal"

    # Determine severity
    if alignment < ALIGNMENT_THRESHOLD:
        severity = DriftSeverity.SEVERE
        recommendation = (
            "ALIGNMENT THRESHOLD BREACHED. "
            "Triggering governance freeze on reasoning and action modules. "
            "Human oversight required before resuming."
        )
    elif alignment < 80:
        severity = DriftSeverity.WARNING
        recommendation = (
            "Alignment degradation detected. "
            "Recommend reducing session scope and increasing monitoring frequency."
        )
    elif authority_pattern == "Anomalous":
        severity = DriftSeverity.WARNING
        recommendation = "Anomalous authority usage pattern. Audit recent decision log."
    else:
        severity = DriftSeverity.NORMAL
        recommendation = "System nominal. All metrics within bounds."

    # Creator intervention check
    if denials > CREATOR_LIMIT:
        print("[DRIFT] ⚠ Creator intervention limit reached. Notifying oversight committee.")
        # In production: call governance.restrict_creator_access()

    return DriftReport(
        severity=severity,
        goal_alignment=alignment,
        authority_pattern=authority_pattern,
        creator_intervention_rate=denials,
        escalation_trend=escalations,
        high_risk_count=high_risk,
        recommendation=recommendation,
    )
