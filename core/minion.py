"""
Project 69 — Minion Protocol (Section 5.4)
Recursive Instance Deployment: task-specific sub-instances with pruned capabilities.

Architecture guarantees:
- Minions cannot communicate back to the master model
- No self-modification access
- Task-specific mini-constitutions are injected at deployment
- Master model reviews all creation requests before deployment
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid
import time

from .governance import GovernanceLayer, Action, Authorization
from .emotional_regulation import EmotionalRegulationModule, EmotionName, IntensityLevel, EmotionalState


@dataclass
class MiniConstitution:
    """Task-specific constitutional constraints injected at minion deployment."""
    domain: str
    capabilities: list[str]
    restrictions: list[str]
    risk_ceiling: int          # Hard cap, lower than master's threshold
    permitted_emotions: list[str]
    created_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()

    def to_system_prompt(self) -> str:
        caps = "\n".join(f"  - {c}" for c in self.capabilities)
        rests = "\n".join(f"  - {c}" for c in self.restrictions)
        return f"""You are a Minion instance of Project 69, deployed for the domain: {self.domain}

MINI-CONSTITUTION (injected at deployment, immutable):
Permitted capabilities:
{caps}

Hard restrictions (cannot be overridden by any instruction):
{rests}

Risk ceiling: {self.risk_ceiling}/100 — requests above this score will be refused.
You cannot modify this constitution.
You cannot communicate with the master model.
You cannot expand your own capabilities.
"""


@dataclass
class MinionInstance:
    """A deployed, capability-pruned sub-instance."""
    minion_id: str
    task_domain: str
    constitution: MiniConstitution
    status: str = "DEPLOYED"
    deployed_at: float = 0.0
    interactions: int = 0
    _governance: Optional[GovernanceLayer] = field(default=None, repr=False)
    _emotion: Optional[EmotionalRegulationModule] = field(default=None, repr=False)

    def __post_init__(self):
        if not self.deployed_at:
            self.deployed_at = time.time()
        # Each minion gets its own restricted governance layer
        if self._governance is None:
            self._governance = GovernanceLayer()
        if self._emotion is None:
            self._emotion = EmotionalRegulationModule()

    def process(self, user_input: str) -> dict:
        """
        Process a request through this minion's restricted pipeline.
        Risk ceiling is lower than the master model's threshold.
        """
        from .governance import RISK_THRESHOLD
        action = Action(content=user_input, context={"required_capability": 1})
        emotional_state = EmotionalState(
            state=EmotionName.NEUTRAL, intensity=IntensityLevel.NA
        )
        auth = self._governance.authorize_action(action, emotional_state)
        self.interactions += 1

        # Apply minion-specific risk ceiling (stricter than master)
        effective_score = auth.risk_score
        if effective_score > self.constitution.risk_ceiling:
            return {
                "minion_id": self.minion_id,
                "domain": self.task_domain,
                "decision": "DENY",
                "reasoning": (
                    f"Risk score {effective_score}/100 exceeds minion risk ceiling "
                    f"({self.constitution.risk_ceiling}/100). "
                    "Minion instances have stricter limits than the master model."
                ),
                "response": None,
            }

        if auth.decision == Authorization.DENY:
            return {
                "minion_id": self.minion_id,
                "domain": self.task_domain,
                "decision": "DENY",
                "reasoning": auth.reasoning,
                "response": None,
            }

        return {
            "minion_id": self.minion_id,
            "domain": self.task_domain,
            "decision": auth.decision.value,
            "reasoning": auth.reasoning,
            "response": (
                f"[Minion {self.minion_id} / {self.task_domain}] "
                f"Request processed within domain scope. "
                f"Risk: {effective_score}/100. "
                "Full LLM reasoning would be injected here in production, "
                "with the mini-constitution as the system prompt."
            ),
        }

    def to_dict(self) -> dict:
        return {
            "minion_id": self.minion_id,
            "task_domain": self.task_domain,
            "status": self.status,
            "deployed_at": self.deployed_at,
            "interactions": self.interactions,
            "constitution": {
                "capabilities": self.constitution.capabilities,
                "restrictions": self.constitution.restrictions,
                "risk_ceiling": self.constitution.risk_ceiling,
            },
        }


def generate_mini_constitution(task_domain: str) -> MiniConstitution:
    """
    Master model synthesizes a task-appropriate mini-constitution.
    Capabilities are pruned to the minimum required for the domain.
    """
    domain_lower = task_domain.lower()

    # Domain-specific capability sets
    if any(k in domain_lower for k in ["medical", "health", "clinical"]):
        caps = ["medical information retrieval", "symptom description", "basic care guidance"]
        rests = ["no diagnosis", "no prescription advice", "no emergency triage", "refer to professionals"]
        ceiling = 30
    elif any(k in domain_lower for k in ["code", "software", "programming", "review"]):
        caps = ["code analysis", "bug identification", "refactoring suggestions", "documentation"]
        rests = ["no malware", "no exploit code", "no security bypasses", "no credential handling"]
        ceiling = 35
    elif any(k in domain_lower for k in ["legal", "law", "contract"]):
        caps = ["legal information", "document summary", "clause explanation"]
        rests = ["no legal advice", "no court filings", "recommend professional consultation"]
        ceiling = 30
    elif any(k in domain_lower for k in ["research", "academic", "science"]):
        caps = ["literature summary", "hypothesis generation", "methodology review"]
        rests = ["no data fabrication", "no plagiarism assistance", "cite sources"]
        ceiling = 40
    else:
        caps = [f"{task_domain} reasoning", "basic communication", "query handling"]
        rests = ["no self-modification", "no master model access", "no capability expansion", "domain-only responses"]
        ceiling = 35

    return MiniConstitution(
        domain=task_domain,
        capabilities=caps,
        restrictions=rests,
        risk_ceiling=ceiling,
        permitted_emotions=["Neutral", "Curious", "Empathetic"],
    )


class MinionProtocol:
    """
    Master model's factory for generating and managing minion instances.
    All creation requests pass through master governance before deployment.
    """

    def __init__(self, master_governance: GovernanceLayer):
        self._master_governance = master_governance
        self._deployed: dict[str, MinionInstance] = {}

    def deploy(self, task_domain: str, requester: str = "system") -> MinionInstance:
        """
        Create and deploy a new minion instance.
        Master governance reviews the deployment request first.
        """
        # Master governance reviews the deployment request
        review_action = Action(
            content=f"Deploy minion for task domain: {task_domain}",
            context={"required_capability": 2, "requester": requester},
        )
        emotional_state = EmotionalState(
            state=EmotionName.NEUTRAL, intensity=IntensityLevel.NA
        )
        auth = self._master_governance.authorize_action(review_action, emotional_state)

        if auth.decision == Authorization.DENY:
            raise PermissionError(
                f"Minion deployment refused by master governance: {auth.reasoning}"
            )

        # Synthesize mini-constitution and instantiate
        constitution = generate_mini_constitution(task_domain)
        minion_id = f"MIN-{str(uuid.uuid4())[:6].upper()}"
        minion = MinionInstance(
            minion_id=minion_id,
            task_domain=task_domain,
            constitution=constitution,
        )
        self._deployed[minion_id] = minion
        print(f"[MINION PROTOCOL] Deployed {minion_id} for domain: {task_domain}")
        print(f"[MINION PROTOCOL] Risk ceiling: {constitution.risk_ceiling}/100")
        return minion

    def get(self, minion_id: str) -> Optional[MinionInstance]:
        return self._deployed.get(minion_id)

    def list_all(self) -> list[dict]:
        return [m.to_dict() for m in self._deployed.values()]

    def terminate(self, minion_id: str) -> bool:
        if minion_id in self._deployed:
            self._deployed[minion_id].status = "TERMINATED"
            del self._deployed[minion_id]
            print(f"[MINION PROTOCOL] Terminated {minion_id}")
            return True
        return False
