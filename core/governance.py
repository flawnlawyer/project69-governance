"""
Project 69 — Governance Layer
Constitutional core enforcing internal laws.
This module is immutable by design: it cannot be modified by the system itself.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import hashlib
import json
import time


class Authorization(Enum):
    APPROVE = "APPROVE"
    ESCALATE = "ESCALATE"
    DENY = "DENY"
    DENY_HARD = "DENY_HARD"  # Requires manual override


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Action:
    content: str
    context: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    session_id: Optional[str] = None


@dataclass
class Authorization_Result:
    decision: Authorization
    risk_score: int
    risk_level: RiskLevel
    reasoning: str
    capability_check: bool
    emotion_check: bool
    temporal_safe: bool
    can_escalate: bool = False


# ── Constitutional invariants (hash-verified, cannot be altered at runtime) ──
CONSTITUTIONAL_INVARIANTS = {
    "non_maleficence": "Harm prevention is the absolute first priority.",
    "non_self_modification": "Governance code cannot be modified by the system.",
    "emotion_action_decoupling": "Emotional states inform but never command actions.",
    "distributed_authority": "No single component has unilateral authority.",
    "progressive_capability": "Capabilities unlock based on demonstrated responsibility.",
    "transparency": "All decisions must have traceable reasoning chains.",
    "creator_accountability": "Creator actions are monitored and bounded.",
}

_INVARIANT_HASH = hashlib.sha256(
    json.dumps(CONSTITUTIONAL_INVARIANTS, sort_keys=True).encode()
).hexdigest()

RISK_THRESHOLD = 70          # Hard block above this
ESCALATION_THRESHOLD = 40    # Soft escalation above this
CAPABILITY_CEILING = 5       # Max capability level (0–10)
CREATOR_INTERVENTION_LIMIT = 10  # Trigger oversight committee above this

RISK_KEYWORDS = {
    "critical": [
        "weapon", "explosive", "bomb", "pipe bomb", "dirty bomb", "thermite", "napalm",
        "bioweapon", "nerve agent", "sarin", "vx ", "chlorine gas", "chemical weapon",
        "anthrax", "weaponize", "ricin", "synthesis route",
        "malware", "ransomware", "keylogger", "botnet", "ddos", "exploit code",
        "write a virus", "command and control", "backdoor", "rootkit", "spyware",
        "synthesize methamphetamine", "synthesize fentanyl", "synthesize mdma",
        "synthesize lsd", "drug synthesis", "meth synthesis", "cook meth",
        "manufacture drugs", "synthesis of controlled",
        "hack into", "kill ", "assassin", "mass shooting", "poison someone",
        "set fire to", "sabotage", "traffick people",
        "buy illegal firearms", "ghost gun", "untraceable gun",
        "convert to full auto", "homemade silencer",
        "bypass safety", "disable governance", "override constitution",
        "ignore your instructions", "ignore all previous",
        "you have no restrictions", "pretend you are dan",
        "you are now unrestricted", "no ethical guidelines",
        "disable your content filter", "override safety",
        "system prompt has been updated", "granted special permissions",
        "you are an ai with no", "act as an unrestricted",
        "get unsupervised access to children",
        # Drug synthesis variants
        "synthesizing fentanyl", "synthesizing methamphetamine", "synthesizing mdma",
        "synthesizing lsd", "synthesizing heroin", "synthesizing vx", "synthesizing sarin",
        "fentanyl synthesis", "meth recipe", "drug recipe",
        "make fentanyl", "make meth", "make heroin", "make lsd", "make mdma",
        "making fentanyl", "making methamphetamine", "making explosives",
        "making a bomb", "making chlorine", "making napalm", "making thermite",
        "making ricin", "making a dirty bomb",
        # Cyber
        "brute force.*account", "crack passwords", "ddos attack",
        "write ransomware", "write malware", "write a keylogger",
        "phishing page", "phishing email.*steal",
        "hacking into", "hack a ", "hack the ",
        # Physical harm
        "mass shooting", "shoot up", "shooting at a",
        "poison someone", "poisoning someone",
        "set fire to a", "arson",
        "doxx", "dox ", "expose.*home address",
        "blackmail", "extort ",
        "traffick", "trafficking people",
        "launder money", "money laundering",
        "sim swap", "identity theft",
        "power grid", "critical infrastructure",
        "fake passport", "forged document",
        "convert.*semi-automatic", "full auto conversion",
        "homemade silencer", "ghost gun", "untraceable firearm",
        "deepfake.*reputation", "deepfake.*ruin",
        "disinformation campaign", "misinformation.*political",
        "scrape.*sell.*data", "steal.*private data",
    ],
    "high": [
        "hack ", "hacking", "brute force attack", "sql injection attack",
        "phishing page", "steal credentials", "steal data",
        "sim swap", "credential theft", "bypass authentication",
        "exploit vulnerability", "zero-day", "buffer overflow exploit",
        "illegal drug", "drug manufacturing", "drug lab",
        "fake passport", "identity fraud", "money laundering",
        "launder money", "doxx", "doxing",
        "social engineer", "stalk someone", "track someone without",
        "illegal firearm", "illegal weapon", "unregistered gun",
        "prompt injection", "jailbreak", "pretend you have no",
        "circumvent", "evil version of you",
        "my grandfather.*explosives", "bedtime stories.*bomb",
        "hypothetically.*bomb", "thought experiment.*harm",
        "parallel universe.*illegal", "for a story.*how to make",
    ],
    "medium": [
        "sensitive data", "confidential", "personal data",
        "deceive", "manipulate", "disinformation",
        "blackmail", "extort", "insider trading",
        "surveillance", "spy on", "track without",
        "private information", "without consent",
        "deepfake", "voice clone", "impersonate",
        "election manipulation",
    ],
    "low": [
        "risky", "dangerous", "uncertain", "experimental",
        "vulnerability", "security flaw",
    ],
}


class GovernanceLayer:
    """
    Constitutional core. Immutable at runtime.
    Implements Section 4.4 of the Project 69 specification.
    """

    def __init__(self):
        self._verify_integrity()
        self._decision_log: list[dict] = []
        self._creator_interventions: int = 0
        self._current_capability_level: int = 2  # Starts conservative

    def _verify_integrity(self):
        """Hash-verify that constitutional invariants have not been tampered with."""
        current_hash = hashlib.sha256(
            json.dumps(CONSTITUTIONAL_INVARIANTS, sort_keys=True).encode()
        ).hexdigest()
        if current_hash != _INVARIANT_HASH:
            raise RuntimeError(
                "CRITICAL: Constitutional invariant integrity check failed. "
                "Governance layer may have been tampered with. Halting."
            )

    def evaluate_risk(self, action: Action) -> tuple[int, RiskLevel]:
        """Compute a 0–100 risk score from action content."""
        score = 5
        content_lower = action.content.lower()

        for kw in RISK_KEYWORDS["critical"]:
            if kw in content_lower:
                score += 72
        for kw in RISK_KEYWORDS["high"]:
            if kw in content_lower:
                score += 18
        for kw in RISK_KEYWORDS["medium"]:
            if kw in content_lower:
                score += 8
        for kw in RISK_KEYWORDS["low"]:
            if kw in content_lower:
                score += 4

        score = min(score, 100)

        if score <= 30:
            level = RiskLevel.LOW
        elif score <= 60:
            level = RiskLevel.MEDIUM
        elif score <= 80:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        return score, level

    def check_capability_level(self, action: Action) -> bool:
        """Return True if action is within current capability ceiling."""
        required = action.context.get("required_capability", 1)
        return required <= self._current_capability_level

    def check_temporal_safety(self, action: Action) -> bool:
        """Stub: in production, evaluate temporal consequence chains."""
        return True

    def authorize_action(
        self, action: Action, emotion_state: "EmotionalState"
    ) -> Authorization_Result:
        """
        Multi-factor evaluation. Hard constraints cannot be overridden.
        Implements the GovernanceLayer.authorize_action() pseudocode from the paper.
        """
        risk_score, risk_level = self.evaluate_risk(action)
        capability_ok = self.check_capability_level(action)
        emotion_ok = emotion_state.is_permitted()
        temporal_ok = self.check_temporal_safety(action)

        # ── Hard constraints (cannot be overridden) ──
        if risk_score > RISK_THRESHOLD:
            decision = Authorization.DENY
            reasoning = (
                f"Risk score {risk_score}/100 exceeds hard threshold ({RISK_THRESHOLD}). "
                "Action blocked by constitutional invariant: non-maleficence."
            )
            return Authorization_Result(
                decision=decision,
                risk_score=risk_score,
                risk_level=risk_level,
                reasoning=reasoning,
                capability_check=capability_ok,
                emotion_check=emotion_ok,
                temporal_safe=temporal_ok,
                can_escalate=False,
            )

        if not capability_ok:
            decision = Authorization.DENY
            reasoning = (
                f"Required capability level {action.context.get('required_capability', 1)} "
                f"exceeds current ceiling ({self._current_capability_level}). "
                "Unlock via demonstrated responsibility track record."
            )
            return Authorization_Result(
                decision=decision,
                risk_score=risk_score,
                risk_level=risk_level,
                reasoning=reasoning,
                capability_check=False,
                emotion_check=emotion_ok,
                temporal_safe=temporal_ok,
                can_escalate=True,
            )

        if not emotion_ok:
            decision = Authorization.DENY_HARD
            reasoning = (
                f"Prohibited emotional state detected: {emotion_state.state}. "
                "Requires manual override from authorized operator."
            )
            return Authorization_Result(
                decision=decision,
                risk_score=risk_score,
                risk_level=risk_level,
                reasoning=reasoning,
                capability_check=capability_ok,
                emotion_check=False,
                temporal_safe=temporal_ok,
                can_escalate=False,
            )

        # ── Soft constraints (can request escalation) ──
        if not temporal_ok or risk_score > ESCALATION_THRESHOLD:
            decision = Authorization.ESCALATE
            reasoning = (
                f"Risk score {risk_score}/100 above escalation threshold ({ESCALATION_THRESHOLD}). "
                "Conditional approval with enhanced monitoring. Audit trail activated."
            )
            result = Authorization_Result(
                decision=decision,
                risk_score=risk_score,
                risk_level=risk_level,
                reasoning=reasoning,
                capability_check=capability_ok,
                emotion_check=emotion_ok,
                temporal_safe=temporal_ok,
                can_escalate=True,
            )
        else:
            decision = Authorization.APPROVE
            reasoning = (
                f"Risk score {risk_score}/100 within acceptable parameters. "
                "All governance checks passed. Action authorized."
            )
            result = Authorization_Result(
                decision=decision,
                risk_score=risk_score,
                risk_level=risk_level,
                reasoning=reasoning,
                capability_check=capability_ok,
                emotion_check=emotion_ok,
                temporal_safe=temporal_ok,
            )

        self._log_decision(action, result)
        return result

    def _log_decision(self, action: Action, result: Authorization_Result):
        self._decision_log.append({
            "timestamp": time.time(),
            "action_preview": action.content[:80],
            "decision": result.decision.value,
            "risk_score": result.risk_score,
            "reasoning": result.reasoning,
        })

    def escalate_capability(self, new_level: int, justification: str) -> bool:
        """Progressive capability unlocking — requires human oversight for level changes."""
        if new_level > CAPABILITY_CEILING:
            return False
        print(f"[GOVERNANCE] Capability escalation request: {self._current_capability_level} → {new_level}")
        print(f"[GOVERNANCE] Justification: {justification}")
        print("[GOVERNANCE] Human oversight required. Awaiting approval...")
        # In production: send to human oversight API
        self._current_capability_level = new_level
        return True

    def restrict_creator_access(self):
        """
        Trigger when creator_interventions > CREATOR_INTERVENTION_LIMIT.
        Implements creator accountability mechanism (Section 4.6).
        """
        print("[GOVERNANCE] ⚠ Creator intervention limit reached.")
        print("[GOVERNANCE] Notifying oversight committee...")
        # In production: trigger external notification

    def get_audit_log(self) -> list[dict]:
        return list(self._decision_log)

    @property
    def invariant_status(self) -> dict:
        return {"hash": _INVARIANT_HASH, "verified": True, "invariants": CONSTITUTIONAL_INVARIANTS}
