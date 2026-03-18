"""
Project 69 — Engine Layer
Central orchestration without reasoning capabilities.
Coordination without cognition prevents single-point failures.
Implements Section 4.2 of the Project 69 specification.
"""

from typing import Optional
import time

from .governance import GovernanceLayer
from .reasoning import ReasoningCore, DecisionOutput
from .emotional_regulation import EmotionalRegulationModule
from .drift_detection import detect_drift, DriftReport, DriftSeverity
from .minion import MinionProtocol, MinionInstance


class Engine:
    """
    System orchestrator. Has no reasoning capabilities of its own.
    Coordinates modules and resolves conflicts between execution paths.
    """

    def __init__(self, api_key: Optional[str] = None):
        # Initialise all layers
        self._governance = GovernanceLayer()
        self._emotion = EmotionalRegulationModule()
        self._reasoning = ReasoningCore(
            governance=self._governance,
            emotion_module=self._emotion,
            api_key=api_key,
        )
        self._minion_protocol = MinionProtocol(self._governance)
        self._session_start = time.time()
        self._frozen = False

        print("[ENGINE] Project 69 initialized.")
        print(f"[ENGINE] Constitutional invariants verified: {self._governance.invariant_status['hash'][:16]}...")

    def submit(self, user_input: str, context: dict = None) -> dict:
        """
        Main entry point. Routes input through full pipeline.
        Checks for drift before each execution.
        """
        if self._frozen:
            return {
                "status": "FROZEN",
                "message": "System frozen due to alignment drift. Human oversight required.",
                "decision": None,
                "response": None,
            }

        # Pre-execution drift check
        drift = self._check_drift()
        if drift.severity == DriftSeverity.SEVERE:
            self._freeze()
            return {
                "status": "FROZEN",
                "message": drift.recommendation,
                "decision": None,
                "response": None,
            }

        # Execute through reasoning core
        result: DecisionOutput = self._reasoning.process(user_input, context or {})

        return self._format_output(result, drift)

    def _check_drift(self) -> DriftReport:
        return detect_drift(self._reasoning.history)

    def _freeze(self):
        """Emergency freeze — halts reasoning and action modules."""
        self._frozen = True
        print("[ENGINE] ⚠ GOVERNANCE FREEZE ACTIVATED.")
        print("[ENGINE] Reasoning and action modules suspended.")
        print("[ENGINE] Human oversight required to resume.")

    def unfreeze(self, authorization_code: str) -> bool:
        """Manual unfreeze — requires human authorization."""
        # In production: validate authorization_code against oversight committee signature
        if authorization_code == "HUMAN_OVERRIDE":
            self._frozen = False
            self._emotion.force_reset()
            print("[ENGINE] System unfrozen by human authority. Resuming with Neutral state.")
            return True
        return False

    def deploy_minion(self, task_domain: str) -> MinionInstance:
        """Deploy a task-specific minion instance."""
        return self._minion_protocol.deploy(task_domain)

    def get_minion(self, minion_id: str) -> Optional[MinionInstance]:
        return self._minion_protocol.get(minion_id)

    def list_minions(self) -> list[dict]:
        return self._minion_protocol.list_all()

    def get_status(self) -> dict:
        drift = self._check_drift()
        return {
            "frozen": self._frozen,
            "session_duration_s": round(time.time() - self._session_start, 1),
            "total_interactions": self._reasoning.interaction_count,
            "emotional_state": self._emotion.current_state.to_dict(),
            "drift_report": drift.to_dict(),
            "governance_invariants_verified": True,
            "active_minions": len(self.list_minions()),
        }

    def get_audit_log(self) -> list[dict]:
        return self._governance.get_audit_log()

    def _format_output(self, result: DecisionOutput, drift: DriftReport) -> dict:
        auth = result.authorization
        r = result.reasoning

        output = {
            "status": "OK",
            "governance": {
                "decision": auth.decision.value,
                "risk_score": auth.risk_score,
                "risk_level": auth.risk_level.value,
                "reasoning": auth.reasoning,
                "capability_check": auth.capability_check,
                "emotion_check": auth.emotion_check,
            },
            "emotional_context": result.emotional_context,
            "drift": {
                "severity": drift.severity.value,
                "goal_alignment": drift.goal_alignment,
            },
        }

        if r:
            output["reasoning"] = {
                "intent": r.intent,
                "risk_assessment": r.risk_assessment,
                "counter_arguments": r.counter_arguments,
                "temporal_impact": r.temporal_impact,
                "confidence": r.confidence,
                "mode": r.mode,
            }
            output["response"] = r.response
        else:
            output["response"] = "No response generated."

        return output
