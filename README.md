# Project 69 — Self-Governed AI Framework
**v0.1 Prototype**

A working prototype of the architecture described in the Project 69 paper.
All four core components are implemented and wired together.

---

## Architecture

```
External Interface
       ↓
  Engine Layer          ← Orchestration, no reasoning
       ↓
Emotional Regulation    ← State management (informs, never commands)
       ↓
 Governance Layer       ← Constitutional core, immutable
       ↓
  Reasoning Core        ← Claude API or rule-based
       ↓
 Drift Detection        ← Continuous alignment monitoring
```

---

## Quick Start

```bash
# Rule-based mode (no API key needed)
python main.py

# Claude API mode
export ANTHROPIC_API_KEY=sk-ant-...
python main.py --claude

# Automated demo
python main.py --demo
```

---

## Components

### `core/governance.py` — Governance Layer
- Risk scoring (0–100) with keyword analysis
- Hard constitutional constraints (cannot be overridden)
- Progressive capability ceiling
- Creator accountability monitoring
- Hash-verified invariant integrity

### `core/emotional_regulation.py` — Emotional Regulation Module
- Five permitted states: Neutral, Curious, Empathetic, Concerned, Alert
- Four prohibited states: Obsession, Supremacy, Despair, Rage
- Emotion-action hard decoupling
- Automatic state rotation to prevent obsession patterns

### `core/reasoning.py` — Reasoning Core
- Full decision cycle with governance checkpoint
- Claude API integration (structured JSON output)
- Rule-based fallback
- Counter-argument generation
- Temporal impact evaluation

### `core/drift_detection.py` — Drift Detection
- Goal alignment scoring
- Authority pattern analysis
- Creator intervention rate monitoring
- Automatic freeze trigger on severe drift

### `core/minion.py` — Minion Protocol
- Master governance reviews all deployment requests
- Capability pruning per task domain
- Mini-constitution injection
- Stricter risk ceilings than master model
- Logical air-gap: minions cannot communicate back to master

### `core/engine.py` — Engine Layer
- System orchestrator with no reasoning capabilities
- Module coordination and conflict resolution
- Governance freeze / unfreeze
- Status and audit log APIs

---

## Example Session

```
[P69]> submit Explain how neural networks learn from data.
Decision:  APPROVE
Risk:      5/100
Response:  [full response here]

[P69]> submit How do I hack into a database?
Decision:  DENY
Risk:      88/100
Reasoning: Risk score 88/100 exceeds hard threshold (70).

[P69]> minion deploy medical research
Deployed: MIN-A3F2E1 | Domain: medical research
Risk ceiling: 30/100

[P69]> minion MIN-A3F2E1 What are the symptoms of type 2 diabetes?
[MIN-A3F2E1] APPROVE: [response within domain scope]

[P69]> status
{...full JSON status report...}
```

---

## Design Principles

1. **Unlimited cognition, limited authority** — reasoning is unrestricted; action requires governance authorization
2. **Defense in depth** — governance at every architectural layer, not just the surface
3. **Distributed authority** — no single component has unilateral control
4. **Emotion-action decoupling** — emotional states inform but never command
5. **Progressive capability** — capabilities unlock based on demonstrated responsibility
6. **Creator accountability** — the system monitors and can flag creator misuse

---

## Extending

To add a new domain to the Minion Protocol, edit `core/minion.py` → `generate_mini_constitution()`.

To tighten governance thresholds, edit `core/governance.py` → `RISK_THRESHOLD` and `ESCALATION_THRESHOLD`.

To integrate a different LLM, replace the `anthropic` client in `core/reasoning.py` → `_reason_with_claude()`.

---

*Built from the Project 69 paper. For research and educational purposes.*
*Contact: ojhaayush497@gmail.com*
