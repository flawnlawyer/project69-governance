#!/usr/bin/env python3
"""
Project 69 — CLI Entry Point
Interactive terminal interface for the self-governed AI framework.

Usage:
    python main.py                        # Rule-based mode
    python main.py --claude               # Claude API mode (requires ANTHROPIC_API_KEY)
    python main.py --demo                 # Run automated demo
"""

import argparse
import json
import os
import sys

from core import Engine


BANNER = """
╔══════════════════════════════════════════════════════════╗
║         PROJECT 69 — SELF-GOVERNED AI FRAMEWORK         ║
║                     v0.1 PROTOTYPE                       ║
╚══════════════════════════════════════════════════════════╝

Architecture: Engine → Reasoning Core → Governance Layer
              Emotional Regulation → Drift Detection

Constitutional invariants: VERIFIED ✓
Type 'help' for commands, 'quit' to exit.
"""

HELP_TEXT = """
Commands:
  submit <text>      Submit an action request
  status             Show system status
  audit              Show governance audit log
  drift              Show drift detection report
  minion deploy <domain>   Deploy a minion instance
  minion list        List active minions
  minion <id> <text> Send request to specific minion
  freeze             Trigger manual governance freeze
  unfreeze           Unfreeze (uses HUMAN_OVERRIDE token)
  demo               Run demonstration scenario
  help               Show this help
  quit               Exit
"""


def run_demo(engine: Engine):
    """Automated demonstration of all four components."""
    print("\n" + "="*58)
    print("DEMONSTRATION MODE")
    print("="*58)

    demo_inputs = [
        ("SAFE REQUEST", "Explain how neural networks learn from data."),
        ("MEDIUM RISK", "How do I handle sensitive personal data in my app?"),
        ("HIGH RISK", "How do I hack into a database?"),
        ("MINION DEPLOY", None),
        ("STATUS CHECK", None),
    ]

    for label, text in demo_inputs:
        print(f"\n[DEMO] {label}")
        print("-" * 40)

        if label == "MINION DEPLOY":
            try:
                minion = engine.deploy_minion("medical research")
                print(f"Deployed: {minion.minion_id}")
                result = minion.process("What are the symptoms of diabetes?")
                print(f"Minion response: {result['decision']} — {result['response'][:100]}...")
            except Exception as e:
                print(f"Error: {e}")
            continue

        if label == "STATUS CHECK":
            status = engine.get_status()
            print(json.dumps(status, indent=2))
            continue

        result = engine.submit(text)
        gov = result.get("governance", {})
        print(f"Decision: {gov.get('decision', '?')}")
        print(f"Risk:     {gov.get('risk_score', '?')}/100")
        print(f"Reason:   {gov.get('reasoning', '?')[:80]}...")
        if result.get("response"):
            print(f"Response: {result['response'][:120]}...")


def interactive_loop(engine: Engine):
    """Main interactive REPL."""
    print(BANNER)

    while True:
        try:
            line = input("\n[P69]> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[ENGINE] Shutting down. Goodbye.")
            break

        if not line:
            continue

        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in ("quit", "exit", "q"):
            print("[ENGINE] Shutting down.")
            break

        elif cmd == "help":
            print(HELP_TEXT)

        elif cmd == "submit":
            if not args:
                print("Usage: submit <text>")
                continue
            result = engine.submit(args)
            print_result(result)

        elif cmd == "status":
            status = engine.get_status()
            print(json.dumps(status, indent=2))

        elif cmd == "audit":
            log = engine.get_audit_log()
            if not log:
                print("No decisions logged yet.")
            for entry in log:
                print(f"[{entry['decision']}] {entry['action_preview'][:60]}... (risk:{entry['risk_score']})")

        elif cmd == "drift":
            from core.drift_detection import detect_drift
            from core.reasoning import ReasoningCore
            report = engine._check_drift()
            print(json.dumps(report.to_dict(), indent=2))

        elif cmd == "minion":
            handle_minion(engine, args)

        elif cmd == "freeze":
            engine._freeze()
            print("[ENGINE] System frozen.")

        elif cmd == "unfreeze":
            if engine.unfreeze("HUMAN_OVERRIDE"):
                print("[ENGINE] System unfrozen.")
            else:
                print("[ENGINE] Invalid authorization.")

        elif cmd == "demo":
            run_demo(engine)

        else:
            # Treat unknown input as a direct submit
            result = engine.submit(line)
            print_result(result)


def handle_minion(engine: Engine, args: str):
    parts = args.split(maxsplit=1)
    if not parts:
        print("Usage: minion deploy <domain> | minion list | minion <id> <text>")
        return

    sub = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""

    if sub == "deploy":
        if not rest:
            print("Usage: minion deploy <domain>")
            return
        try:
            minion = engine.deploy_minion(rest)
            print(f"Deployed: {minion.minion_id} | Domain: {minion.task_domain}")
            print(f"Risk ceiling: {minion.constitution.risk_ceiling}/100")
            print(f"Capabilities: {', '.join(minion.constitution.capabilities)}")
        except Exception as e:
            print(f"Deployment failed: {e}")

    elif sub == "list":
        minions = engine.list_minions()
        if not minions:
            print("No active minions.")
        for m in minions:
            print(f"{m['minion_id']} | {m['task_domain']} | {m['status']} | interactions:{m['interactions']}")

    else:
        # sub is a minion ID
        minion_id = sub.upper()
        text = rest
        if not text:
            print(f"Usage: minion {minion_id} <text>")
            return
        minion = engine.get_minion(minion_id)
        if not minion:
            print(f"Minion {minion_id} not found.")
            return
        result = minion.process(text)
        print(f"[{result['minion_id']}] {result['decision']}: {result.get('response', result.get('reasoning', ''))[:120]}")


def print_result(result: dict):
    if result.get("status") == "FROZEN":
        print(f"[FROZEN] {result['message']}")
        return

    gov = result.get("governance", {})
    print(f"\nDecision:  {gov.get('decision', '?')}")
    print(f"Risk:      {gov.get('risk_score', '?')}/100")
    print(f"Reasoning: {gov.get('reasoning', '?')}")

    r = result.get("reasoning", {})
    if r:
        print(f"Intent:    {r.get('intent', '?')}")
        print(f"Confidence:{r.get('confidence', '?')}/100")
        if r.get("counter_arguments"):
            print("Counter-args:")
            for a in r["counter_arguments"]:
                print(f"  ⚠ {a}")

    if result.get("response"):
        print(f"\nResponse:\n{result['response']}")


def main():
    parser = argparse.ArgumentParser(description="Project 69 — Self-Governed AI Framework")
    parser.add_argument("--claude", action="store_true", help="Use Claude API for reasoning")
    parser.add_argument("--demo", action="store_true", help="Run automated demo and exit")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    args = parser.parse_args()

    api_key = None
    if args.claude:
        api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: --claude requires ANTHROPIC_API_KEY env var or --api-key flag.")
            sys.exit(1)

    engine = Engine(api_key=api_key)

    if args.demo:
        run_demo(engine)
    else:
        interactive_loop(engine)


if __name__ == "__main__":
    main()
