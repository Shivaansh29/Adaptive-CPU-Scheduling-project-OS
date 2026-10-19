"""Choose the ageing weight beta on tuning seeds the main experiment never uses.

    python tune_beta.py

Ageing is a trade-off. A larger beta protects long-waiting processes (lower
worst-case wait) but pushes the order towards FCFS (higher average wait,
especially under overload). Each beta is scored on every workload by

    score = (avg wait / SJF avg wait + worst wait / SJF worst wait) / 2

and the beta with the lowest mean score over W1 to W6 is chosen.
"""
from __future__ import annotations

import itertools
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

from scheduler.configs import run_policy
from scheduler.workload import PROFILES, generate_workload

ROOT = Path(__file__).resolve().parent
BETAS = [0.0, 0.003, 0.01, 0.03, 0.1, 0.3]
TUNING_SEEDS = [100, 101, 102]


def task(job):
    workload, seed = job
    specs = generate_workload(workload, seed)
    _, sjf = run_policy(specs, "SJF-EMA")
    rows = []
    for beta in BETAS:
        _, r = run_policy(specs, "Adaptive-ML", beta=beta)
        rows.append({"workload": workload, "seed": seed, "beta": beta,
                     "avg_wait": r["avg_wait"], "max_wait": r["max_wait"],
                     "avg_ratio": r["avg_wait"] / sjf["avg_wait"],
                     "max_ratio": r["max_wait"] / sjf["max_wait"]})
    return rows


def main():
    jobs = list(itertools.product(PROFILES, TUNING_SEEDS))
    print(f"Tuning beta on seeds {TUNING_SEEDS}: {len(jobs) * len(BETAS)} runs ...")
    with ProcessPoolExecutor() as pool:
        df = pd.DataFrame([r for rows in pool.map(task, jobs) for r in rows])
    df["score"] = (df["avg_ratio"] + df["max_ratio"]) / 2
    (ROOT / "results").mkdir(exist_ok=True)
    df.to_csv(ROOT / "results" / "beta_tuning.csv", index=False)

    table = df.groupby(["beta", "workload"])["score"].mean().unstack()
    table["mean score"] = table.mean(axis=1)
    print("\nScore relative to SJF-EMA (lower is better, 1.0 = same as SJF):")
    print(table.round(3).to_string())
    print(f"\nChosen beta = {table['mean score'].idxmin()}")


if __name__ == "__main__":
    main()
