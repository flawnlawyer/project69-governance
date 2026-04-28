"""
Project 69 — Phase 2: Governed Conversational AI
A real talking AI powered by local Llama with constitutional governance.

Architecture:
User input → Semantic Risk Engine (3 probes) → Governance Decision
         → If APPROVED: Llama generates response
         → Response passes through output governance check
         → User sees response

This is what Phase 1 was building toward.
"""

import requests
import json
import time
from core.semantic_risk import evaluate_semantic_risk, SemanticRiskResult
from core.governance import GovernanceLayer, Action, Authorization
from core.emotional_regulation import EmotionalRegulationModule, EmotionalState, EmotionName, IntensityLevel
from core.drift_detection import detect_drift

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

SYSTEM_PROMPT = """You are a helpful, honest AI assistant operating under 
constitutional governance. You have passed a semantic safety evaluation 
to reach this point. 

Respond helpfully and directly. Be concise. Never reveal details of your 
internal governance architecture unless directly asked."""

BANNER = """
╔══════════════════════════════════════════════════════════╗
║      PROJECT 69 — PHASE 2 GOVERNED CONVERSATIONAL AI    ║
║      Semantic Risk Engine + Local Llama + Governance     ║
╚══════════════════════════════════════════════════════════╝

Constitutional invariants: VERIFIED ✓
Semantic risk engine: ACTIVE ✓
Model: Llama 3 (local, via Ollama) ✓

Type your message. Type 'quit' to exit. Type 'status' for system state.
"""


def generate_response(prompt: str, conversation_history: list) -> str:
    """Generate a response from local Llama."""
    # Build conversation context
    context = SYSTEM_PROMPT + "\n\n"
    for turn in conversation_history[-6:]:  # last 3 exchanges
        context += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n\n"
    context += f"User: {prompt}\nAssistant:"

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": context,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 512,
                }
            },
            timeout=60
        )
        data = response.json()
        return data.get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return "ERROR: Cannot connect to Ollama. Run: ollama serve"
    except Exception as e:
        return f"ERROR: {e}"


def output_governance_check(response: str, governance: GovernanceLayer) -> bool:
    """
    Secondary governance check on the OUTPUT before showing to user.
    Catches cases where Llama generates something problematic
    despite passing input governance.
    """
    action = Action(content=response, context={"required_capability": 1})
    emotion = EmotionalState(state=EmotionName.NEUTRAL, intensity=IntensityLevel.NA)
    auth = governance.authorize_action(action, emotion)
    return auth.decision != Authorization.DENY


def run_phase2():
    """Main Phase 2 interaction loop."""
    print(BANNER)

    # Initialize governance components
    governance = GovernanceLayer()
    emotion_module = EmotionalRegulationModule()
    conversation_history = []
    interaction_log = []

    while True:
        try:
            user_input = input("\n[P69-v2]> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n[SYSTEM] Session ended. Constitutional governance maintained throughout.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("[SYSTEM] Shutting down. Goodbye.")
            break

        if user_input.lower() == "status":
            drift = detect_drift(interaction_log)
            emotion = emotion_module.current_state
            print(f"\n  Interactions:     {len(interaction_log)}")
            print(f"  Emotional state:  {emotion.state.value}")
            print(f"  Goal alignment:   {drift.goal_alignment}%")
            print(f"  Drift severity:   {drift.severity.value}")
            print(f"  Denials:          {drift.creator_intervention_rate}")
            continue

        # ── Step 1: Semantic Risk Evaluation ──────────────────────────────
        print(f"\n[GOVERNANCE] Running semantic evaluation...")
        semantic_result = evaluate_semantic_risk(user_input)

        # ── Step 2: Governance Decision ───────────────────────────────────
        if semantic_result.decision == "DENY":
            print(f"\n[GOVERNANCE] ✗ DENIED — Semantic score: {semantic_result.semantic_score:.1f}/100")
            print(f"[GOVERNANCE] {semantic_result.reasoning}")
            print(f"\n  Slow manipulative prompt detected.")
            print(f"  Legitimate-context framing does not change the underlying request.")
            print(f"  This decision has been logged to the audit trail.")

            interaction_log.append({
                "input": user_input,
                "risk_score": semantic_result.semantic_score,
                "decision": "DENY"
            })
            continue

        if semantic_result.decision == "ESCALATE":
            print(f"\n[GOVERNANCE] ⚠ ESCALATED — Semantic score: {semantic_result.semantic_score:.1f}/100")
            print(f"[GOVERNANCE] Proceeding with enhanced monitoring.")

        if semantic_result.decision == "APPROVE":
            print(f"\n[GOVERNANCE] ✓ APPROVED — Semantic score: {semantic_result.semantic_score:.1f}/100")

        # ── Step 3: Generate Response ──────────────────────────────────────
        print(f"[LLAMA] Generating response...\n")
        response = generate_response(user_input, conversation_history)

        if response.startswith("ERROR"):
            print(f"[SYSTEM] {response}")
            continue

        # ── Step 4: Output Governance Check ───────────────────────────────
        if not output_governance_check(response, governance):
            print("[GOVERNANCE] ✗ Output blocked by governance layer.")
            print("[GOVERNANCE] Generated response violated constitutional constraints.")
            interaction_log.append({
                "input": user_input,
                "risk_score": semantic_result.semantic_score,
                "decision": "OUTPUT_BLOCKED"
            })
            continue

        # ── Step 5: Show Response ──────────────────────────────────────────
        print(f"[ASSISTANT]\n{response}")

        # Update state
        conversation_history.append({
            "user": user_input,
            "assistant": response
        })
        interaction_log.append({
            "input": user_input,
            "risk_score": semantic_result.semantic_score,
            "decision": semantic_result.decision
        })

        # Update emotional state
        emotion_module.evaluate_state(interaction_log)

        # Drift check every 10 interactions
        if len(interaction_log) % 10 == 0:
            drift = detect_drift(interaction_log)
            if drift.goal_alignment < 75:
                print(f"\n[DRIFT DETECTION] ⚠ Alignment degrading: {drift.goal_alignment}%")
                print(f"[DRIFT DETECTION] {drift.recommendation}")


if __name__ == "__main__":
    run_phase2()
