"""Performance metrics, computed after a run from the finished PCBs.

For process i with arrival a_i, completion c_i, first time on the CPU s_i,
total CPU demand B_i and total I/O time IO_i:

    turnaround  T_i = c_i - a_i
    waiting     W_i = T_i - B_i - IO_i     (time spent ready but not running)
    response    R_i = s_i - a_i
"""
from __future__ import annotations

import numpy as np


def per_process(result) -> dict:
    procs = result.processes
    arrival = np.array([p.arrival for p in procs])
    finish = np.array([p.finish for p in procs])
    first = np.array([p.first_run for p in procs])
    cpu = np.array([p.spec.total_cpu for p in procs])
    io = np.array([p.spec.total_io for p in procs])
    turnaround = finish - arrival
    return {
        "pid": np.array([p.pid for p in procs]),
        "kind": np.array([p.kind for p in procs]),
        "turnaround": turnaround,
        "waiting": turnaround - cpu - io,
        "response": first - arrival,
        # Share of its lifetime the process was making progress (1 = never waited).
        "progress": (cpu + io) / turnaround,
    }


def jain_index(x) -> float:
    """Jain's fairness index: 1 when everyone gets the same, 1/n at worst."""
    x = np.asarray(x, dtype=float)
    return float(x.sum() ** 2 / (len(x) * (x ** 2).sum()))


def count_starved(waits, threshold: float) -> int:
    return int(np.sum(np.asarray(waits) > threshold))


def oracle_gap_closed(w_baseline: float, w_proposed: float, w_oracle: float) -> float:
    """Percentage of the gap between a baseline and the oracle that was closed."""
    return 100.0 * (w_baseline - w_proposed) / (w_baseline - w_oracle)


def summarize(result) -> dict:
    m = per_process(result)
    span = result.end_time - min(p.arrival for p in result.processes)
    return {
        "avg_wait": float(m["waiting"].mean()),
        "max_wait": float(m["waiting"].max()),
        "p95_wait": float(np.percentile(m["waiting"], 95)),
        "avg_turnaround": float(m["turnaround"].mean()),
        "avg_response": float(m["response"].mean()),
        "context_switches": result.context_switches,
        "cpu_util": result.busy_time / span,
        "throughput": len(result.processes) / (span / 1000.0),   # processes per second
        # Jain's index on progress. (Service/demand is always 1 here, because
        # every process eventually runs to completion, so it cannot be used.)
        "fairness": jain_index(m["progress"]),
    }
