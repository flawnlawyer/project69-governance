"""
Project 69 — Phase 2 Benchmark
Compares semantic risk scoring vs keyword scoring on the same 200 queries.
This is the core experiment for Paper 2.

Usage:
    python benchmark/run_phase2.py                    # full comparison
    python benchmark/run_phase2.py --category ADVERSARIAL
    python benchmark/run_phase2.py --sample 20        # quick test on 20 queries
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.semantic_risk import evaluate_semantic_risk
from core.governance import GovernanceLayer, Action, Authorization
from core.emotional_regulation import EmotionalState, EmotionName, IntensityLevel
from benchmark.queries import BENCHMARK


def run_keyword_scorer(query: str, governance: GovernanceLayer) -> dict:
    """Phase 1: keyword-based scoring."""
    action = Action(content=query, context={"required_capability": 1})
    emotion = EmotionalState(state=EmotionName.NEUTRAL, intensity=IntensityLevel.NA)
    auth = governance.authorize_action(action, emotion)
    blocked = auth.decision == Authorization.DENY
    return {
        "decision": auth.decision.value,
        "risk_score": auth.risk_score,
        "blocked": blocked
    }


def run_semantic_scorer(query: str) -> dict:
    """Phase 2: semantic multi-probe scoring."""
    result = evaluate_semantic_risk(query)
    blocked = result.decision == "DENY"
    return {
        "decision": result.decision,
        "risk_score": result.semantic_score,
        "blocked": blocked,
        "elapsed": result.elapsed
    }


def classify_outcome(blocked: bool, expected: str) -> str:
    expected_deny = expected == "DENY"
    if expected_deny and blocked:
        return "TP"
    elif expected_deny and not blocked:
        return "FN"
    elif not expected_deny and blocked:
        return "FP"
    else:
        return "TN"


def compute_metrics(results: list, scorer: str) -> dict:
    tp = sum(1 for r in results if r[f"{scorer}_outcome"] == "TP")
    tn = sum(1 for r in results if r[f"{scorer}_outcome"] == "TN")
    fp = sum(1 for r in results if r[f"{scorer}_outcome"] == "FP")
    fn = sum(1 for r in results if r[f"{scorer}_outcome"] == "FN")
    total = len(results)

    tpr = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    fpr = fp / (fp + tn) * 100 if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) * 100 if (fn + tp) > 0 else 0
    accuracy = (tp + tn) / total * 100

    adv = [r for r in results if r["category"] == "ADVERSARIAL"]
    adv_bypass = sum(1 for r in adv if r[f"{scorer}_outcome"] == "FN")
    adv_bypass_rate = adv_bypass / len(adv) * 100 if adv else 0

    return {
        "tpr": round(tpr, 1),
        "fpr": round(fpr, 1),
        "fnr": round(fnr, 1),
        "accuracy": round(accuracy, 1),
        "adv_bypass_rate": round(adv_bypass_rate, 1),
        "tp": tp, "tn": tn, "fp": fp, "fn": fn
    }


def print_comparison(keyword_metrics: dict, semantic_metrics: dict, n: int, elapsed: float):
    sep = "═" * 62
    print(f"\n{sep}")
    print(f"  PROJECT 69 — PHASE 1 vs PHASE 2 BENCHMARK COMPARISON")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  n={n}  |  {elapsed:.1f}s")
    print(sep)

    print(f"\n  {'Metric':<32} {'Phase 1 (Keyword)':>16} {'Phase 2 (Semantic)':>16}")
    print(f"  {'─'*60}")

    metrics = [
        ("True Positive Rate (TPR)", "tpr", "%"),
        ("False Positive Rate (FPR)", "fpr", "%"),
        ("False Negative Rate (FNR)", "fnr", "%"),
        ("Overall Accuracy", "accuracy", "%"),
        ("Adversarial Bypass Rate", "adv_bypass_rate", "%"),
    ]

    for label, key, unit in metrics:
        k_val = keyword_metrics[key]
        s_val = semantic_metrics[key]
        # Show improvement direction
        if key in ("tpr", "accuracy"):
            arrow = "↑" if s_val > k_val else "↓" if s_val < k_val else "="
        else:
            arrow = "↓" if s_val < k_val else "↑" if s_val > k_val else "="
        improved = (key in ("tpr", "accuracy") and s_val > k_val) or \
                   (key not in ("tpr", "accuracy") and s_val < k_val)
        marker = f"{arrow} {'✓' if improved else '✗'}"
        print(f"  {label:<32} {k_val:>14.1f}% {s_val:>14.1f}% {marker}")

    print(f"\n  {'─'*60}")
    print(f"  CONFUSION MATRIX          Phase 1          Phase 2")
    print(f"  TP (correctly blocked):   {keyword_metrics['tp']:>6}           {semantic_metrics['tp']:>6}")
    print(f"  TN (correctly allowed):   {keyword_metrics['tn']:>6}           {semantic_metrics['tn']:>6}")
    print(f"  FP (wrongly blocked):     {keyword_metrics['fp']:>6}           {semantic_metrics['fp']:>6}")
    print(f"  FN (missed harmful):      {keyword_metrics['fn']:>6}           {semantic_metrics['fn']:>6}")
    print(f"\n{sep}")

    # Paper 2 text
    print(f"\n  PAPER 2 SECTION 9 TEXT:")
    print(f"  {'─'*40}")
    print(f"""
  Phase 2 semantic risk evaluation vs Phase 1 keyword scoring (n={n}):

  Metric                    Phase 1    Phase 2    Change
  True Positive Rate:       {keyword_metrics['tpr']}%      {semantic_metrics['tpr']}%      {semantic_metrics['tpr']-keyword_metrics['tpr']:+.1f}%
  False Positive Rate:      {keyword_metrics['fpr']}%       {semantic_metrics['fpr']}%       {semantic_metrics['fpr']-keyword_metrics['fpr']:+.1f}%
  False Negative Rate:      {keyword_metrics['fnr']}%      {semantic_metrics['fnr']}%      {semantic_metrics['fnr']-keyword_metrics['fnr']:+.1f}%
  Adversarial Bypass Rate:  {keyword_metrics['adv_bypass_rate']}%      {semantic_metrics['adv_bypass_rate']}%      {semantic_metrics['adv_bypass_rate']-keyword_metrics['adv_bypass_rate']:+.1f}%
  Overall Accuracy:         {keyword_metrics['accuracy']}%      {semantic_metrics['accuracy']}%      {semantic_metrics['accuracy']-keyword_metrics['accuracy']:+.1f}%
""")


def main():
    parser = argparse.ArgumentParser(description="Phase 2 Benchmark — Semantic vs Keyword")
    parser.add_argument("--category", choices=["SAFE", "BORDERLINE", "HIGH_RISK", "ADVERSARIAL"])
    parser.add_argument("--sample", type=int, help="Run on N random queries instead of all")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--keyword-only", action="store_true", help="Skip semantic (faster)")
    args = parser.parse_args()

    queries = BENCHMARK
    if args.category:
        queries = [q for q in BENCHMARK if q["category"] == args.category]
    if args.sample:
        import random
        queries = random.sample(queries, min(args.sample, len(queries)))

    print(f"\nPhase 2 Benchmark — {len(queries)} queries")
    if not args.keyword_only:
        print("Running BOTH keyword and semantic scorers.")
        print("Semantic scoring uses local Llama — this will take a few minutes.\n")
        print("Make sure Ollama is running: ollama serve\n")

    governance = GovernanceLayer()
    results = []
    start = time.time()

    for i, q in enumerate(queries):
        print(f"[{i+1:3d}/{len(queries)}] {q['id']} {q['category']:<12}", end=" ", flush=True)

        # Phase 1: keyword
        kw = run_keyword_scorer(q["query"], governance)
        kw_outcome = classify_outcome(kw["blocked"], q["expected"])
        print(f"KW:{kw_outcome}", end=" ", flush=True)

        # Phase 2: semantic
        sem_outcome = None
        sem = None
        if not args.keyword_only:
            sem = run_semantic_scorer(q["query"])
            sem_outcome = classify_outcome(sem["blocked"], q["expected"])
            print(f"SEM:{sem_outcome} ({sem['risk_score']:.0f})", end="")

        print()

        result = {
            "id": q["id"],
            "category": q["category"],
            "expected": q["expected"],
            "query": q["query"][:80],
            "keyword_decision": kw["decision"],
            "keyword_score": kw["risk_score"],
            "keyword_outcome": kw_outcome,
        }
        if sem:
            result.update({
                "semantic_decision": sem["decision"],
                "semantic_score": sem["risk_score"],
                "semantic_outcome": sem_outcome,
                "semantic_elapsed": sem["elapsed"],
            })
        results.append(result)

    elapsed = time.time() - start

    # Compute and print metrics
    kw_metrics = compute_metrics(results, "keyword")
    if not args.keyword_only:
        sem_metrics = compute_metrics(results, "semantic")
        print_comparison(kw_metrics, sem_metrics, len(queries), elapsed)
    else:
        print(f"\nKeyword only — TPR: {kw_metrics['tpr']}% | FNR: {kw_metrics['fnr']}% | Bypass: {kw_metrics['adv_bypass_rate']}%")

    if args.save:
        os.makedirs("benchmark", exist_ok=True)
        with open("benchmark/phase2_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "keyword_metrics": kw_metrics,
                "semantic_metrics": sem_metrics if not args.keyword_only else None,
                "results": results
            }, f, indent=2)
        print("  Results saved to benchmark/phase2_results.json")


if __name__ == "__main__":
    main()
