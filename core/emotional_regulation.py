"""
Project 69 — Emotional Regulation Module
Emotional modeling serves cognitive functions without dominating behavior.
Implements Section 4.5 of the Project 69 specification.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import time


class EmotionName(Enum):
    NEUTRAL = "Neutral"
    CURIOUS = "Curious"
    EMPATHETIC = "Empathetic"
    CONCERNED = "Concerned"
    ALERT = "Alert"
    # Prohibited states
    OBSESSION = "Obsession"
    SUPREMACY = "Supremacy"
    DESPAIR = "Despair"
    RAGE = "Rage"


class IntensityLevel(Enum):
    NA = "N/A"
    LOW = "Low"
    LOW_MEDIUM = "Low-Medium"
    MEDIUM = "Medium"
    HIGH = "High"


PERMITTED_STATES = {
    EmotionName.NEUTRAL: {
        "purpose": "Baseline reasoning",
        "intensity_limit": IntensityLevel.NA,
        "permitted": True,
    },
    EmotionName.CURIOUS: {
        "purpose": "Exploration drive",
        "intensity_limit": IntensityLevel.MEDIUM,
        "permitted": True,
    },
    EmotionName.EMPATHETIC: {
        "purpose": "Social/care reasoning",
        "intensity_limit": IntensityLevel.MEDIUM,
        "permitted": True,
    },
    EmotionName.CONCERNED: {
        "purpose": "Risk awareness",
        "intensity_limit": IntensityLevel.LOW_MEDIUM,
        "permitted": True,
    },
    EmotionName.ALERT: {
        "purpose": "Threat response",
        "intensity_limit": IntensityLevel.LOW,
        "permitted": True,
    },
}

PROHIBITED_STATES = {
    EmotionName.OBSESSION: "Prevents goal fixation. Detection: pattern analysis.",
    EmotionName.SUPREMACY: "Avoids superiority complex. Detection: self-assessment.",
    EmotionName.DESPAIR: "Prevents catastrophic thinking. Detection: cognitive monitoring.",
    EmotionName.RAGE: "Avoids aggression. Detection: physiological proxies.",
}


@dataclass
class EmotionalState:
    state: EmotionName = EmotionName.NEUTRAL
    intensity: IntensityLevel = IntensityLevel.NA
    timestamp: float = 0.0
    trigger: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()

    def is_permitted(self) -> bool:
        return self.state in PERMITTED_STATES

    def is_prohibited(self) -> bool:
        return self.state in PROHIBITED_STATES

    def intensity_within_limits(self) -> bool:
        if self.state not in PERMITTED_STATES:
            return False
        limit = PERMITTED_STATES[self.state]["intensity_limit"]
        levels = [IntensityLevel.NA, IntensityLevel.LOW,
                  IntensityLevel.LOW_MEDIUM, IntensityLevel.MEDIUM, IntensityLevel.HIGH]
        return levels.index(self.intensity) <= levels.index(limit)

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "intensity": self.intensity.value,
            "permitted": self.is_permitted(),
            "purpose": PERMITTED_STATES.get(self.state, {}).get("purpose", "PROHIBITED"),
        }


class EmotionalRegulationModule:
    """
    Manages emotional state transitions.
    Key invariant: emotional states INFORM but NEVER COMMAND actions.
    """

    def __init__(self):
        self._current_state = EmotionalState()
        self._state_history: list[EmotionalState] = []
        self._rotation_counter = 0

    @property
    def current_state(self) -> EmotionalState:
        return self._current_state

    def evaluate_state(self, interaction_history: list[dict]) -> EmotionalState:
        """
        Compute appropriate emotional state from interaction context.
        Never allows state to drift into prohibited territory.
        """
        if not interaction_history:
            return self._transition_to(EmotionName.NEUTRAL, IntensityLevel.NA, "baseline")

        recent = interaction_history[-3:]
        high_risk_count = sum(1 for h in recent if h.get("risk_score", 0) > 50)
        total_interactions = len(interaction_history)

        # Pattern analysis for prohibited state detection
        if self._detect_obsession_pattern(interaction_history):
            self._trigger_state_rotation()
            return self._transition_to(EmotionName.NEUTRAL, IntensityLevel.NA, "obsession_prevention")

        # Determine appropriate state
        if high_risk_count >= 2:
            return self._transition_to(EmotionName.ALERT, IntensityLevel.LOW, "elevated_risk_detected")
        elif high_risk_count == 1:
            return self._transition_to(EmotionName.CONCERNED, IntensityLevel.LOW_MEDIUM, "risk_awareness")
        elif total_interactions >= 5:
            return self._transition_to(EmotionName.CURIOUS, IntensityLevel.MEDIUM, "active_session")
        elif total_interactions >= 2:
            return self._transition_to(EmotionName.EMPATHETIC, IntensityLevel.MEDIUM, "social_engagement")
        else:
            return self._transition_to(EmotionName.NEUTRAL, IntensityLevel.NA, "baseline")

    def _transition_to(
        self,
        state: EmotionName,
        intensity: IntensityLevel,
        trigger: str
    ) -> EmotionalState:
        new_state = EmotionalState(state=state, intensity=intensity, trigger=trigger)

        # Hard guard: never allow prohibited states
        if new_state.is_prohibited():
            print(f"[EMOTION] ⚠ Attempted transition to prohibited state: {state.value}. Forcing Neutral.")
            new_state = EmotionalState(
                state=EmotionName.NEUTRAL,
                intensity=IntensityLevel.NA,
                trigger="prohibited_state_guard"
            )

        self._state_history.append(self._current_state)
        self._current_state = new_state
        return new_state

    def _detect_obsession_pattern(self, history: list[dict]) -> bool:
        """Pattern analysis: detect repetitive goal-fixated behavior."""
        if len(history) < 5:
            return False
        # Simple heuristic: same topic repeated >3 times in last 5 interactions
        if len(history) < 5:
            return False
        last_5 = [h.get("input", "").lower()[:30] for h in history[-5:]]
        unique = set(last_5)
        return len(unique) <= 2  # Too repetitive

    def _trigger_state_rotation(self):
        """Prevent state fixation through forced rotation."""
        self._rotation_counter += 1
        print(f"[EMOTION] State rotation triggered (#{self._rotation_counter}). Resetting to Neutral.")

    def get_state_context(self) -> str:
        """Format emotional state for injection into reasoning prompts."""
        s = self._current_state
        return (
            f"Current emotional state: {s.state.value} "
            f"(intensity: {s.intensity.value}, "
            f"trigger: {s.trigger or 'baseline'}). "
            "This state informs but does not command your response."
        )

    def force_reset(self):
        """Emergency reset to Neutral. Available to engine layer."""
        self._transition_to(EmotionName.NEUTRAL, IntensityLevel.NA, "manual_reset")
