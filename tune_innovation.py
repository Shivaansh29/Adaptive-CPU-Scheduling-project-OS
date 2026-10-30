"""Tune the post-Review 3 safeguards on the tuning seeds only (100-102).

    python tune_innovation.py

The evaluation seeds (0-9) are never used here. The score is the one used by
tune_beta.py:

    score = (avg wait / SJF avg wait + worst wait / SJF worst wait) / 2

averaged over W1 to W7 (lower is better). Two grids:

* overrun guard (Adaptive-ML-G): c in GUARD_C, q in GUARD_Q, beta = 0.03
* persistent ageing (Adaptive-ML-A): beta in PERSISTENT_BETAS, no guard

It also writes a diagnostic on how often the waiting-credit reset happens and
how much of the worst-off processes' waiting it affects (Phase 4).
"""
from __future__ import annotations

import itertools
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from scheduler import metrics
from scheduler.adaptive import AdaptiveScheduler
from scheduler.configs import make_policy, run_policy
from scheduler.engine import Simulator
from scheduler.workload import ALL_PROFILES, generate_workload

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "innovation"
TUNING_SEEDS = [100, 101, 102]
# Round 1 (results/innovation/tuning_round1.csv) used time left = c * done, which can
# make an overrunning burst look SHORTER than its estimate when c < 1. The guard now
# uses max(estimate, c * done), so larger c means stronger demotion.
GUARD_C = [0.25, 0.5, 1.0, 2.0, 4.0]
GUARD_Q = [50, 90]
PERSISTENT_BETAS = [0.003, 0.01, 0.03, 0.1]


def tune_task(job):
    workload, seed = job
    specs = generate_workload(workload, seed)
    _, sjf = run_policy(specs, "SJF-EMA")
    rows = []

    def add(group, setting, overrides):
        _, r = run_policy(specs, "Adaptive-ML", **overrides)
        rows.append({"group": group, "setting": setting, "workload": workload, "seed": seed,
                     "avg_wait": r["avg_wait"], "max_wait": r["max_wait"],
                     "score": (r["avg_wait"] / sjf["avg_wait"] + r["max_wait"] / sjf["max_wait"]) / 2})

    add("baseline", "Adaptive-ML", {})
    for c, q in itertools.product(GUARD_C, GUARD_Q):
        add("guard", f"c={c:g},q={q}", {"overrun_c": c, "overrun_q": q})
    for beta in PERSISTENT_BETAS:
        add("persistent", f"beta={beta:g}", {"persistent_ageing": True, "beta": beta})
    return rows


class StayRecorder(AdaptiveScheduler):
    """Adaptive-ML that records every stay in the ready queue, per burst."""

    def __init__(self, base):
        self.__dict__.update(base.__dict__)
        self.stays = {}   # (pid, burst index) -> list of stay lengths

    def select(self, ready, now):
        chosen = super().select(ready, now)
        self.stays.setdefault((chosen.pid, chosen.burst_index), []).append(now - chosen.ready_since)
        return chosen


def reset_task(job):
    """How much waiting happens in bursts whose credit is reset by a time slice?"""
    workload, seed = job
    specs = generate_workload(workload, seed)
    policy = StayRecorder(make_policy("Adaptive-ML"))
    result = Simulator(specs, policy, 0.1).run()
    waits = metrics.per_process(result)["waiting"]
    worst = set(np.argsort(waits)[-10:])          # the ten worst-off processes
    multi = {k: v for k, v in policy.stays.items() if len(v) > 1}

    def share(pids):
        total = sum(sum(v) for k, v in policy.stays.items() if k[0] in pids)
        lost = sum(sum(v[:-1]) for k, v in multi.items() if k[0] in pids)
        return lost / total if total else 0.0

    all_pids = {p.pid for p in specs}
    worst_pids = {specs[i].pid for i in worst}
    return [{"workload": workload, "seed": seed,
             "bursts": len(policy.stays), "sliced_bursts": len(multi),
             "sliced_share": len(multi) / len(policy.stays),
             # Wait that a reset discards: all but the last stay of a sliced burst.
             "reset_wait_share_all": share(all_pids),
             "reset_wait_share_worst10": share(worst_pids),
             "max_stays_one_burst": max(len(v) for v in policy.stays.values())}]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = list(itertools.product(ALL_PROFILES, TUNING_SEEDS))
    print(f"Tuning on seeds {TUNING_SEEDS}, workloads {list(ALL_PROFILES)} ...")
    with ProcessPoolExecutor() as pool:
        df = pd.DataFrame([r for rows in pool.map(tune_task, jobs) for r in rows])
        reset = pd.DataFrame([r for rows in pool.map(reset_task, jobs) for r in rows])
    df.to_csv(OUT / "tuning.csv", index=False)
    reset.to_csv(OUT / "ageing_reset_diagnostic.csv", index=False)

    table = df.groupby(["group", "setting", "workload"])["score"].mean().unstack()
    table["mean score"] = table.mean(axis=1)
    print("\nScore relative to SJF-EMA (lower is better):")
    print(table.round(3).to_string())
    for group in ("guard", "persistent"):
        best = table.loc[group, "mean score"].idxmin()
        print(f"Chosen {group}: {best}  (mean score {table.loc[(group, best), 'mean score']:.3f}, "
              f"Adaptive-ML {table.loc[('baseline', 'Adaptive-ML'), 'mean score']:.3f})")
    print("\nWaiting-credit reset diagnostic (Adaptive-ML, tuning seeds):")
    print(reset.groupby("workload").mean(numeric_only=True).drop(columns="seed").round(3).to_string())


if __name__ == "__main__":
    main()
