"""Features describing a process's past behaviour.

Every feature is computed only from bursts and I/O waits that have already
finished, which is information a real kernel keeps. Nothing about the future
is used, so the predictor cannot cheat.
"""
from __future__ import annotations

import math

import numpy as np

HISTORY = 5             # how many recent bursts are used directly
EMA_ALPHA = 0.5
EMA_TAU0 = 10.0         # initial guess before a process has any history (ms)

FEATURE_NAMES = (
    "last_1", "last_2", "last_3", "last_4", "last_5",   # most recent burst first
    "mean_burst", "std_burst",
    "ema_estimate",          # the classical prediction, so the model can only improve on it
    "last_io", "mean_io",    # how long the process blocks between bursts
    "bursts_done",
    "last_change",           # last burst minus the one before it
)


def ema_estimate(history, alpha: float = EMA_ALPHA, tau0: float = EMA_TAU0) -> float:
    """Exponential averaging: tau(n+1) = alpha * t(n) + (1 - alpha) * tau(n)."""
    tau = tau0
    for t in history:
        tau = alpha * t + (1 - alpha) * tau
    return tau


def extract_features(history, io_history) -> list[float]:
    n = len(history)
    recent = list(reversed(history[-HISTORY:]))
    recent += [0.0] * (HISTORY - len(recent))
    if n:
        mean = sum(history) / n
        std = math.sqrt(sum((x - mean) ** 2 for x in history) / n)
    else:
        mean = std = 0.0
    last_io = io_history[-1] if io_history else 0.0
    mean_io = sum(io_history) / len(io_history) if io_history else 0.0
    change = history[-1] - history[-2] if n >= 2 else 0.0
    return recent + [mean, std, ema_estimate(history), last_io, mean_io, float(n), change]


def features_for(pcb) -> list[float]:
    return extract_features(pcb.history, pcb.io_history)


def build_dataset(specs):
    """One row per CPU burst: features from the bursts before it, and its true length.

    Because the features only use a process's own history, the dataset can be
    built straight from the workload without running the simulator.
    Returns X, y (burst length), labels (burst class), groups (process id), kinds.
    """
    X, y, labels, groups, kinds = [], [], [], [], []
    for gid, spec in enumerate(specs):
        for k, burst in enumerate(spec.bursts):
            X.append(extract_features(spec.bursts[:k], spec.ios[:k]))
            y.append(burst)
            labels.append(spec.burst_classes[k])
            groups.append(gid)
            kinds.append(spec.kind)
    return (np.asarray(X), np.asarray(y), np.asarray(labels),
            np.asarray(groups), np.asarray(kinds))
