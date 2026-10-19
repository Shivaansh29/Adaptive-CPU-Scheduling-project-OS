"""Run every experiment and save the raw numbers to results/*.csv.

    python run_experiments.py           # full run (about 3 minutes on 10 cores)
    python run_experiments.py --quick   # 3 seeds, no sweeps (under a minute)

Main experiment: 6 workloads x 11 schedulers x 10 seeds = 660 runs. Every
scheduler sees the same 10 workload instances, so comparisons are paired.
Also: an ablation on W4 and W5, parameter sweeps on W4, a context-switch cost
sensitivity check, and two traces used for figures.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import platform
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from scheduler import metrics
from scheduler.configs import ABLATIONS, ADAPTIVE_DEFAULTS, MAIN_CONFIGS, load_models, run_policy
from scheduler.features import ema_estimate, extract_features
from scheduler.workload import PHASE, PROFILES, generate_workload, shifting_workload

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
ABLATION_WORKLOADS = ("W4", "W5")
SWEEPS = {"beta": [0.0, 0.01, 0.03, 0.1, 0.3, 1.0], "p": [60, 70, 80, 90], "epoch": [20, 50, 100]}
SWITCH_COSTS = [0.05, 0.1, 0.5]
SWITCH_POLICIES = ["SJF-EMA", "RR-5", "RR-20", "MLFQ", "Adaptive-ML"]
STARVATION_FACTOR = 5   # starved = waited more than 5x the cross-policy mean wait


def main_task(workload, seed, n_processes):
    """All 11 schedulers (and the ablation variants) on one workload instance."""
    specs = generate_workload(workload, seed, n_processes)
    rows, waits = [], {}
    for name in MAIN_CONFIGS:
        result, row = run_policy(specs, name)
        waits[name] = metrics.per_process(result)["waiting"]
        rows.append({"workload": workload, "seed": seed, "policy": name, **row})
    theta = STARVATION_FACTOR * np.mean([r["avg_wait"] for r in rows])
    for r in rows:
        r["starved"] = metrics.count_starved(waits[r["policy"]], theta)

    ablation = []
    if workload in ABLATION_WORKLOADS:
        for variant, overrides in ABLATIONS.items():
            result, row = run_policy(specs, "Adaptive-ML", **overrides)
            row["starved"] = metrics.count_starved(metrics.per_process(result)["waiting"], theta)
            ablation.append({"workload": workload, "seed": seed, "variant": variant, **row})
    return "main", rows, ablation


def sweep_task(param, value, seed, n_processes):
    specs = generate_workload("W4", seed, n_processes)
    _, row = run_policy(specs, "Adaptive-ML", **{param: value})
    return "sweep", [{"param": param, "value": value, "seed": seed, **row}], []


def switch_task(cost, seed, n_processes):
    specs = generate_workload("W4", seed, n_processes)
    rows = []
    for name in SWITCH_POLICIES:
        _, row = run_policy(specs, name, switch_cost=cost)
        rows.append({"switch_cost": cost, "seed": seed, "policy": name, **row})
    return "switch", rows, []


def quantum_trace():
    """Adaptive-ML on a workload whose mix changes every 30 s."""
    rows = []
    for name in ("Adaptive-ML", "Adaptive-EMA"):
        result, _ = run_policy(shifting_workload(seed=0), name)
        for t, q, target, p in result.policy_obj.controller.trace:
            rows.append({"policy": name, "time_ms": t, "quantum": q, "target": target,
                         "percentile": p})
    return pd.DataFrame(rows)


def prediction_trace(n_examples=3):
    """Actual bursts vs the two predictors for a few phase-changing processes."""
    bundle, _ = load_models()
    model, log_target = bundle["model"], bundle["log_target"]
    specs = [s for s in generate_workload("W5", seed=0) if s.kind == PHASE and len(s.bursts) >= 20]
    rows = []
    for spec in specs[:n_examples]:
        X = np.asarray([extract_features(spec.bursts[:k], spec.ios[:k])
                        for k in range(len(spec.bursts))])
        ml = model.predict(X)
        ml = np.expm1(ml) if log_target else ml
        for k, actual in enumerate(spec.bursts):
            rows.append({"pid": spec.pid, "burst": k, "actual": actual,
                         "ema": ema_estimate(spec.bursts[:k]), "ml": max(float(ml[k]), 0.1)})
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--processes", type=int, default=200)
    parser.add_argument("--quick", action="store_true", help="3 seeds and no sweeps")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = parser.parse_args()
    seeds = range(3 if args.quick else args.seeds)
    n = args.processes
    load_models()   # fail early with a clear message if the models are missing

    jobs = [(main_task, (w, s, n)) for w, s in itertools.product(PROFILES, seeds)]
    if not args.quick:
        jobs += [(sweep_task, (param, v, s, n))
                 for param, values in SWEEPS.items() for v in values for s in seeds]
        jobs += [(switch_task, (c, s, n)) for c in SWITCH_COSTS for s in seeds]

    print(f"Running {len(jobs)} jobs on {args.workers} worker processes "
          f"({len(PROFILES)} workloads x {len(MAIN_CONFIGS)} schedulers x {len(seeds)} seeds "
          f"= {len(PROFILES) * len(MAIN_CONFIGS) * len(seeds)} main runs) ...")
    start = time.time()
    collected = {"main": [], "ablation": [], "sweep": [], "switch": []}
    with ProcessPoolExecutor(args.workers) as pool:
        futures = [pool.submit(fn, *a) for fn, a in jobs]
        for i, future in enumerate(as_completed(futures), 1):
            kind, rows, ablation = future.result()
            collected[kind] += rows
            collected["ablation"] += ablation
            if i % 10 == 0 or i == len(futures):
                print(f"  {i:4d}/{len(futures)} jobs done  ({time.time() - start:5.0f} s)", flush=True)

    RESULTS.mkdir(exist_ok=True)
    order = ["workload", "seed"]
    pd.DataFrame(collected["main"]).sort_values(order + ["policy"]).to_csv(
        RESULTS / "main_results.csv", index=False)
    pd.DataFrame(collected["ablation"]).sort_values(order + ["variant"]).to_csv(
        RESULTS / "ablation.csv", index=False)
    if collected["sweep"]:
        pd.DataFrame(collected["sweep"]).sort_values(["param", "value", "seed"]).to_csv(
            RESULTS / "sweeps.csv", index=False)
        pd.DataFrame(collected["switch"]).sort_values(["switch_cost", "seed", "policy"]).to_csv(
            RESULTS / "switch_cost.csv", index=False)

    print("Recording traces for the figures ...")
    quantum_trace().to_csv(RESULTS / "quantum_trace.csv", index=False)
    prediction_trace().to_csv(RESULTS / "prediction_trace.csv", index=False)

    info = {"seeds": list(seeds), "processes_per_run": n, "quick": args.quick,
            "main_runs": len(collected["main"]), "ablation_runs": len(collected["ablation"]),
            "sweep_runs": len(collected["sweep"]), "switch_cost_runs": len(collected["switch"]),
            "adaptive_defaults": ADAPTIVE_DEFAULTS, "wall_seconds": round(time.time() - start, 1),
            "python": platform.python_version(), "machine": platform.platform()}
    (RESULTS / "run_info.json").write_text(json.dumps(info, indent=2))
    print(f"Done in {time.time() - start:.0f} s. Raw results are in results/. "
          f"Next:  python analyse.py")


if __name__ == "__main__":
    main()
