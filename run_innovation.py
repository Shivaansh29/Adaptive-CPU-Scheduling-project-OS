"""Experiments for the post-Review 3 additions. Results go to results/innovation/;
the original results/*.csv files are never written.

    python run_innovation.py --part noise     # prediction-quality sweep (W4, W5)
    python run_innovation.py --part compare   # W1-W7, original + new configurations
    python run_innovation.py                  # both

Every configuration sees the same workload instances (seeds 0-9), so all
comparisons are paired. The noisy predictor is seeded with the workload seed,
so SJF-Noisy and Adaptive-Noisy see the same noisy prediction for each burst.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from scheduler import metrics
from scheduler.configs import (GUARD, INNOVATION_CONFIGS, MAIN_CONFIGS, PERSISTENT_BETA,
                               load_models, run_policy)
from scheduler.workload import ALL_PROFILES, generate_workload

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "innovation"
SIGMAS = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
NOISE_WORKLOADS = ("W4", "W5")
NOISE_REFERENCES = ["FCFS", "SJF-EMA", "RR-5", "Oracle", "Adaptive-EMA", "Adaptive-ML"]
STARVATION_FACTOR = 5   # same rule as run_experiments.py


def kind_metrics(result) -> dict:
    """Mean wait and response per process kind (honest vs bait processes on W7)."""
    m = metrics.per_process(result)
    out = {}
    for kind in np.unique(m["kind"]):
        sel = m["kind"] == kind
        out[f"wait_{kind}"] = float(m["waiting"][sel].mean())
        out[f"maxwait_{kind}"] = float(m["waiting"][sel].max())
        out[f"resp_{kind}"] = float(m["response"][sel].mean())
    return out


def noise_task(workload, seed):
    specs = generate_workload(workload, seed)
    rows = []
    for name in NOISE_REFERENCES:
        _, row = run_policy(specs, name)
        rows.append({"workload": workload, "seed": seed, "policy": name, "sigma": np.nan, **row})
    for sigma, family in itertools.product(SIGMAS, ("SJF-Noisy", "Adaptive-Noisy")):
        _, row = run_policy(specs, f"{family}-{sigma:g}", noise_seed=seed)
        rows.append({"workload": workload, "seed": seed, "policy": family, "sigma": sigma, **row})
    return "noise", rows


def compare_task(workload, seed):
    specs = generate_workload(workload, seed)
    rows, waits = [], {}
    for name in MAIN_CONFIGS + INNOVATION_CONFIGS:
        result, row = run_policy(specs, name)
        waits[name] = metrics.per_process(result)["waiting"]
        rows.append({"workload": workload, "seed": seed, "policy": name, **row,
                     **kind_metrics(result)})
    # Starvation threshold from the 11 original configurations only, exactly as
    # in run_experiments.py, so adding new configurations cannot move it.
    theta = STARVATION_FACTOR * np.mean([r["avg_wait"] for r in rows if r["policy"] in MAIN_CONFIGS])
    for r in rows:
        r["starved"] = metrics.count_starved(waits[r["policy"]], theta)
    return "compare", rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--part", choices=["noise", "compare", "all"], default="all")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = parser.parse_args()
    seeds = range(args.seeds)
    load_models()
    if args.part in ("compare", "all") and GUARD["overrun_c"] is None:
        raise SystemExit("Run tune_innovation.py and set GUARD / PERSISTENT_BETA in configs.py first.")

    jobs = []
    if args.part in ("noise", "all"):
        jobs += [(noise_task, (w, s)) for w, s in itertools.product(NOISE_WORKLOADS, seeds)]
    if args.part in ("compare", "all"):
        jobs += [(compare_task, (w, s)) for w, s in itertools.product(ALL_PROFILES, seeds)]

    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Running {len(jobs)} jobs on {args.workers} workers ...")
    start = time.time()
    collected = {"noise": [], "compare": []}
    with ProcessPoolExecutor(args.workers) as pool:
        futures = [pool.submit(fn, *a) for fn, a in jobs]
        for i, future in enumerate(as_completed(futures), 1):
            kind, rows = future.result()
            collected[kind] += rows
            if i % 5 == 0 or i == len(futures):
                print(f"  {i:3d}/{len(futures)} jobs done  ({time.time() - start:4.0f} s)", flush=True)

    if collected["noise"]:
        pd.DataFrame(collected["noise"]).sort_values(["workload", "seed", "policy", "sigma"]).to_csv(
            OUT / "noise_sweep.csv", index=False)
    if collected["compare"]:
        pd.DataFrame(collected["compare"]).sort_values(["workload", "seed", "policy"]).to_csv(
            OUT / "comparison.csv", index=False)
    info_path = OUT / "run_info.json"
    info = json.loads(info_path.read_text()) if info_path.exists() else {}
    parts = ["noise", "compare"] if args.part == "all" else [args.part]
    for part in parts:
        info[part] = {"seeds": list(seeds), "wall_seconds": round(time.time() - start, 1)}
        if part == "noise":
            info[part]["sigmas"] = SIGMAS
            info[part]["note"] = ("The noise sweep runs Adaptive-Noisy, SJF-Noisy and the original "
                                  "configurations only; the safeguards are not used.")
        else:
            info[part].update(guard=GUARD, persistent_beta=PERSISTENT_BETA)
    info_path.write_text(json.dumps(info, indent=2))
    print(f"Done in {time.time() - start:.0f} s. Next:  python analyse_innovation.py")


if __name__ == "__main__":
    main()
