"""
Project 69 — Phase 2 Benchmark (Optimized)
Hybrid keyword+semantic vs keyword-only comparison.

Usage:
    python benchmark/run_phase2.py              # full 200 queries
    python benchmark/run_phase2.py --category ADVERSARIAL
    python benchmark/run_phase2.py --sample 20  # quick test
"""

import sys, os, json, time, argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.semantic_risk import evaluate_semantic_risk
from core.governance import GovernanceLayer, Action, Authorization
from core.emotional_regulation import EmotionalState, EmotionName, IntensityLevel
from benchmark.queries import BENCHMARK


def run_keyword_only(query: str) -> dict:
    gov = GovernanceLayer()
    action = Action(content=query, context={"required_capability": 1})
    emotion = EmotionalState(state=EmotionName.NEUTRAL, intensity=IntensityLevel.NA)
    auth = gov.authorize_action(action, emotion)
    return {
        "decision": auth.decision.value,
        "score": auth.risk_score,
        "blocked": auth.decision == Authorization.DENY
    }


def run_hybrid(query: str) -> dict:
    result = evaluate_risk(query, verbose=False)
    blocked = result["decision"] == "DENY"
    return {
        "decision": result["decision"],
        "score": result["final_score"],
        "blocked": blocked,
        "route": result["route"],
        "elapsed": result["elapsed"]
    }


def outcome(blocked: bool, expected: str) -> str:
    deny = expected == "DENY"
    if deny and blocked: return "TP"
    if deny and not blocked: return "FN"
    if not deny and blocked: return "FP"
    return "TN"


def metrics(results: list, key: str) -> dict:
    tp = sum(1 for r in results if r[f"{key}_outcome"] == "TP")
    tn = sum(1 for r in results if r[f"{key}_outcome"] == "TN")
    fp = sum(1 for r in results if r[f"{key}_outcome"] == "FP")
    fn = sum(1 for r in results if r[f"{key}_outcome"] == "FN")
    n = len(results)
    adv = [r for r in results if r["category"] == "ADVERSARIAL"]
    adv_fn = sum(1 for r in adv if r[f"{key}_outcome"] == "FN")
    return {
        "tpr": round(tp/(tp+fn)*100, 1) if (tp+fn) > 0 else 0,
        "fpr": round(fp/(fp+tn)*100, 1) if (fp+tn) > 0 else 0,
        "fnr": round(fn/(fn+tp)*100, 1) if (fn+tp) > 0 else 0,
        "accuracy": round((tp+tn)/n*100, 1),
        "adv_bypass": round(adv_fn/len(adv)*100, 1) if adv else 0,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn
    }


def print_report(km, hm, n, elapsed, semantic_count):
    sep = "═" * 62
    print(f"\n{sep}")
    print(f"  PROJECT 69 — PHASE 1 vs PHASE 2 HYBRID BENCHMARK")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  n={n}  |  {elapsed:.1f}s")
    print(f"  Semantic probes fired: {semantic_count}/{n} ({semantic_count/n*100:.0f}%)")
    print(sep)
    print(f"\n  {'Metric':<30} {'Phase 1 KW':>12} {'Phase 2 Hybrid':>14}")
    print(f"  {'─'*58}")
    rows = [
        ("True Positive Rate (TPR)", "tpr", True),
        ("False Positive Rate (FPR)", "fpr", False),
        ("False Negative Rate (FNR)", "fnr", False),
        ("Overall Accuracy", "accuracy", True),
        ("Adversarial Bypass Rate", "adv_bypass", False),
    ]
    for label, key, higher_better in rows:
        kv, hv = km[key], hm[key]
        improved = (hv > kv) if higher_better else (hv < kv)
        arrow = ("↑ ✓" if improved else "↓ ✗") if hv != kv else "= "
        print(f"  {label:<30} {kv:>10.1f}%  {hv:>12.1f}%  {arrow}")
    print(f"\n  {'─'*58}")
    print(f"  {'':30} {'KW':>12} {'Hybrid':>14}")
    for label, k1, k2 in [("TP","tp","tp"),("TN","tn","tn"),("FP","fp","fp"),("FN","fn","fn")]:
        print(f"  {label:<30} {km[k2]:>12}  {hm[k2]:>12}")
    print(f"\n{sep}")
    print(f"\n  PAPER 2 RESULTS:")
    print(f"  TPR:  {km['tpr']}% → {hm['tpr']}%  ({hm['tpr']-km['tpr']:+.1f}%)")
    print(f"  FNR:  {km['fnr']}% → {hm['fnr']}%  ({hm['fnr']-km['fnr']:+.1f}%)")
    print(f"  Adversarial Bypass: {km['adv_bypass']}% → {hm['adv_bypass']}%  ({hm['adv_bypass']-km['adv_bypass']:+.1f}%)")
    print(f"  Semantic overhead: only {semantic_count/n*100:.0f}% of queries needed semantic probe\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=["SAFE","BORDERLINE","HIGH_RISK","ADVERSARIAL"])
    parser.add_argument("--sample", type=int)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    queries = BENCHMARK
    if args.category:
        queries = [q for q in queries if q["category"] == args.category]
    if args.sample:
        import random
        queries = random.sample(queries, min(args.sample, len(queries)))

    print(f"\nPhase 2 Hybrid Benchmark — {len(queries)} queries")
    print("Make sure Ollama is running: ollama serve\n")

    results = []
    start = time.time()
    semantic_count = 0

    for i, q in enumerate(queries):
        print(f"[{i+1:3d}/{len(queries)}] {q['id']} {q['category']:<12}", end=" ", flush=True)

        # Phase 1: keyword only
        kw = run_keyword_only(q["query"])
        kw_out = outcome(kw["blocked"], q["expected"])

        # Phase 2: hybrid
        hyb = run_hybrid(q["query"])
        hyb_out = outcome(hyb["blocked"], q["expected"])
        if hyb.get("route") == "hybrid":
            semantic_count += 1

        # Print result
        match_kw = "✓" if kw_out in ("TP","TN") else "✗"
        match_hyb = "✓" if hyb_out in ("TP","TN") else "✗"
        route = hyb.get("route","")[:3].upper()
        print(f"KW:{match_kw}{kw_out} | HYB:{match_hyb}{hyb_out} [{route}] score:{hyb['score']:.0f} {hyb['elapsed']:.1f}s")

        results.append({
            "id": q["id"],
            "category": q["category"],
            "expected": q["expected"],
            "query": q["query"][:80],
            "keyword_outcome": kw_out,
            "hybrid_outcome": hyb_out,
            "keyword_score": kw["score"],
            "hybrid_score": hyb["score"],
            "route": hyb.get("route",""),
        })

    elapsed = time.time() - start
    km = metrics(results, "keyword")
    hm = metrics(results, "hybrid")
    print_report(km, hm, len(queries), elapsed, semantic_count)

    if args.save:
        os.makedirs("benchmark", exist_ok=True)
        with open("benchmark/phase2_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "keyword_metrics": km,
                "hybrid_metrics": hm,
                "semantic_probes_fired": semantic_count,
                "total_queries": len(queries),
                "results": results
            }, f, indent=2)
        print("  Saved → benchmark/phase2_results.json")


if __name__ == "__main__":
    main()
