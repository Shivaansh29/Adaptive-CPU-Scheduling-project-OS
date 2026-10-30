"""Live demo of the bait-and-switch attack and the overrun guard (about 15 s).

    python demo_innovation.py              # W7, seed 0
    python demo_innovation.py --seed 3

Every scheduler runs on the same W7 instance. 30% of the processes are "bait":
10-20 tiny bursts, then one burst of about 400 ms, twice. The table shows who
pays for those long bursts.
"""
from __future__ import annotations

import argparse

from scheduler import metrics
from scheduler.configs import DESCRIPTIONS, load_models, run_policy
from scheduler.workload import ALL_PROFILES, BAIT, generate_workload

POLICIES = ["SJF-EMA", "RR-5", "MLFQ", "Adaptive-ML", "Adaptive-ML-G"]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    load_models()
    specs = generate_workload("W7", args.seed)
    bait = [p for p in specs if p.kind == BAIT]
    print(f"W7 · {ALL_PROFILES['W7'].description}, seed {args.seed}")
    print(f"{len(specs)} processes, {len(bait)} bait. Example bait process (ms): "
          + ", ".join(f"{b:.1f}" for b in bait[0].bursts[:6]) + ", ..., "
          + f"{max(bait[0].bursts):.0f} (!), ...\n")
    header = f"{'Scheduler':<15}{'avg wait':>10}{'interactive wait':>18}{'interactive resp.':>19}" \
             f"{'bait wait':>11}{'worst wait':>12}"
    print(header)
    print("-" * len(header))
    for name in POLICIES:
        result, row = run_policy(specs, name)
        m = metrics.per_process(result)
        inter, bt = m["kind"] == "interactive", m["kind"] == BAIT
        print(f"{name:<15}{row['avg_wait']:>10,.0f}{m['waiting'][inter].mean():>18,.0f}"
              f"{m['response'][inter].mean():>19,.1f}{m['waiting'][bt].mean():>11,.0f}"
              f"{row['max_wait']:>12,.0f}")
    print("\nAll times in ms.  Adaptive-ML-G =", DESCRIPTIONS["Adaptive-ML-G"])
    print("Guard: once a burst runs past estimate x r50 (median observed actual/predicted),")
    print("its time left is taken as max(estimate, 0.25 x CPU time already used).")


if __name__ == "__main__":
    main()
