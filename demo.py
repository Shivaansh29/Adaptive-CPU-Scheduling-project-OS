"""Live demo for the presentation (about 20 seconds).

    python demo.py              # all three parts, mixed workload W4
    python demo.py --workload W5

1. The simulator reproduces the textbook answers (with Gantt charts).
2. Why exponential averaging lags, and what the learned model does instead.
3. All 11 schedulers on the same workload, side by side.
"""
from __future__ import annotations

import argparse

import numpy as np

from scheduler.baselines import FCFS, Oracle, RoundRobin
from scheduler.configs import DESCRIPTIONS, MAIN_CONFIGS, load_models, run_policy
from scheduler.engine import Simulator
from scheduler.features import ema_estimate, extract_features
from scheduler.metrics import per_process
from scheduler.workload import PHASE, PROFILES, generate_workload, simple_processes

BOLD, GREEN, BLUE, DIM, RESET = "\033[1m", "\033[32m", "\033[34m", "\033[2m", "\033[0m"


def heading(text):
    print(f"\n{BOLD}{'=' * 74}\n{text}\n{'=' * 74}{RESET}")


def gantt(timeline, scale=1.0):
    """One text Gantt chart: each slice drawn as |P1....| with its end time below."""
    bar, ticks = "", "0"
    for start, end, pid in timeline:
        width = max(int(round((end - start) * scale)), len(f"P{pid}") + 1)
        bar += "|" + f"P{pid}".center(width - 1, "·")
        ticks += f"{end:g}".rjust(width)
    return f"    {bar}|\n    {ticks}"


def merge(timeline):
    """Join back-to-back slices of the same process so the chart stays readable."""
    merged = []
    for s, e, pid in timeline:
        if merged and merged[-1][2] == pid and abs(merged[-1][1] - s) < 1e-9:
            merged[-1] = (merged[-1][0], e, pid)
        else:
            merged.append((s, e, pid))
    return merged


def textbook():
    heading("1. Is the simulator correct?  Textbook examples (Silberschatz, Ch. 5)")
    cases = [
        ("FCFS, bursts 24, 3, 3 (all arrive at 0)", simple_processes([24, 3, 3]), FCFS(), 17.0),
        ("Shortest first (oracle), same processes", simple_processes([24, 3, 3]), Oracle(), 3.0),
        ("Round Robin q = 4, same processes", simple_processes([24, 3, 3]), RoundRobin(4), 17 / 3),
        ("SRTF, bursts 8,4,9,5 arriving at 0,1,2,3",
         simple_processes([8, 4, 9, 5], [0, 1, 2, 3]), Oracle(), 6.5),
    ]
    for title, specs, policy, expected in cases:
        result = Simulator(specs, policy, switch_cost=0.0).run()
        got = per_process(result)["waiting"].mean()
        ok = abs(got - expected) < 1e-9
        print(f"\n  {title}")
        print(gantt(merge(result.timeline), scale=1.6))
        mark = f"{GREEN}✓ matches the textbook{RESET}" if ok else "✗ WRONG"
        print(f"    average waiting time = {got:.2f} ms   (expected {expected:.2f})   {mark}")


def prediction():
    heading("2. Why the classical guess lags: a process that changes phase")
    bursts = [2, 2, 2, 2, 60, 60, 60]
    print("\n  Exponential averaging (alpha = 0.5) on bursts 2, 2, 2, 2, 60, 60, 60:")
    print("    burst  actual   guess made before it")
    for k, b in enumerate(bursts):
        print(f"    {k + 1:5d}  {b:6.0f}   {ema_estimate(bursts[:k], tau0=2):8.2f}")
    print(f"    {DIM}(after burst 7 the guess is {ema_estimate(bursts, tau0=2):.2f}: still short of 60)")
    print(f"    -> it needs 3-4 bursts to catch up, scheduling the process wrongly each time.{RESET}")

    bundle, _ = load_models()
    spec = next(s for s in generate_workload("W5", seed=0)
                if s.kind == PHASE and len(s.bursts) >= 20)
    X = np.asarray([extract_features(spec.bursts[:k], spec.ios[:k]) for k in range(len(spec.bursts))])
    ml = bundle["model"].predict(X)
    ml = np.expm1(ml) if bundle["log_target"] else ml
    half = len(spec.bursts) // 2
    print(f"\n  A real phase-changing process from workload W5 (I/O-bound, then CPU-bound "
          f"from burst {half + 1}):")
    print("    burst  actual    EMA guess   ML guess")
    for k in range(half - 2, half + 4):
        print(f"    {k + 1:5d}  {spec.bursts[k]:6.1f}   {ema_estimate(spec.bursts[:k]):9.1f}   "
              f"{BLUE}{ml[k]:8.1f}{RESET}")
    ema_err = np.mean([abs(spec.bursts[k] - ema_estimate(spec.bursts[:k])) for k in range(len(spec.bursts))])
    ml_err = np.mean(np.abs(np.asarray(spec.bursts) - ml))
    print(f"    mean error over all {len(spec.bursts)} bursts:  EMA {ema_err:.1f} ms,  "
          f"ML {BLUE}{ml_err:.1f} ms{RESET}")


def comparison(workload, seed):
    heading(f"3. All 11 schedulers on the same workload\n   {workload}: "
            f"{PROFILES[workload].description}, seed {seed}")
    specs = generate_workload(workload, seed)
    print(f"  {len(specs)} processes, {sum(len(s.bursts) for s in specs):,} CPU bursts, "
          f"context-switch cost 0.1 ms\n")
    print(f"  {'scheduler':14s}{'avg wait':>11s}{'worst wait':>12s}{'response':>10s}"
          f"{'switches':>10s}{'pred err':>10s}{'quantum':>9s}")
    print(f"  {'':14s}{'(ms)':>11s}{'(ms)':>12s}{'(ms)':>10s}{'':>10s}{'(ms)':>10s}{'(ms)':>9s}")
    rows = {}
    for name in MAIN_CONFIGS:
        _, r = run_policy(specs, name)
        rows[name] = r
        colour = BLUE + BOLD if name == "Adaptive-ML" else ""
        err = f"{r['pred_mae']:.1f}" if "pred_mae" in r else "-"
        q = f"{r['mean_quantum']:.1f}" if "mean_quantum" in r else "-"
        print(f"  {colour}{name:14s}{r['avg_wait']:11,.0f}{r['max_wait']:12,.0f}"
              f"{r['avg_response']:10.1f}{r['context_switches']:10,}{err:>10s}{q:>9s}{RESET}")

    ours, sjf, oracle = rows["Adaptive-ML"], rows["SJF-EMA"], rows["Oracle"]
    change = 100 * (ours["avg_wait"] / sjf["avg_wait"] - 1)
    gap = 100 * (sjf["avg_wait"] - ours["avg_wait"]) / (sjf["avg_wait"] - oracle["avg_wait"])
    print(f"\n  Adaptive-ML vs SJF-EMA: average wait {change:+.1f}%, worst-case wait "
          f"{100 * (ours['max_wait'] / sjf['max_wait'] - 1):+.1f}%")
    print(f"  Share of the SJF-EMA -> oracle gap closed: {gap:.0f}%")
    print(f"\n  {DIM}Oracle = {DESCRIPTIONS['Oracle']}. One seed only; the full experiment "
          f"(run_experiments.py) uses 10 seeds per workload.{RESET}")


def main():
    parser = argparse.ArgumentParser(description="Live demo of the adaptive CPU scheduler")
    parser.add_argument("--workload", default="W4", choices=list(PROFILES))
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    textbook()
    prediction()
    comparison(args.workload, args.seed)
    print()


if __name__ == "__main__":
    main()
