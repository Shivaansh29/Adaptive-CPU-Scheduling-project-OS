"""Synthetic workload generation.

Every process alternates CPU bursts and I/O waits:

    cpu[0], io[0], cpu[1], io[1], ..., cpu[n-1]

so a process with n CPU bursts has n - 1 I/O waits. All times are in
milliseconds. Burst lengths are fixed when the workload is generated, so every
scheduling policy runs on exactly the same processes.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

CPU, IO, INTERACTIVE, PHASE = "cpu", "io", "interactive", "phase"

# Labels a single burst can have. A phase-changing process produces I/O-bound
# bursts first and CPU-bound bursts later, so "phase" is never a burst label.
BURST_CLASSES = (CPU, IO, INTERACTIVE)

# Per-class parameters from the Review 1 plan.
CLASS_PARAMS = {
    CPU: {"burst": ("lognormal", 100.0), "io_mean": 5.0, "count": (3, 8)},
    IO: {"burst": ("exponential", 2.0), "io_mean": 30.0, "count": (20, 60)},
    INTERACTIVE: {"burst": ("exponential", 5.0), "io_mean": 100.0, "count": (10, 40)},
}
PHASE_COUNT = (10, 30)
LOGNORMAL_SIGMA = 0.5   # CPU-bound bursts: median 100 ms, mean about 113 ms
MIN_TIME = 0.05         # floor so exponential draws never give near-zero times


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    mix: dict                    # process kind -> fraction of processes
    rate_multiplier: float = 1.0
    stream: int = 0              # profiles sharing a stream get the same processes


_MIXED = {INTERACTIVE: 0.4, CPU: 0.3, IO: 0.2, PHASE: 0.1}

PROFILES = {p.name: p for p in [
    Profile("W1", "All CPU-bound", {CPU: 1.0}, stream=1),
    Profile("W2", "All I/O-bound", {IO: 1.0}, stream=2),
    Profile("W3", "All interactive", {INTERACTIVE: 1.0}, stream=3),
    Profile("W4", "Mixed (40% interactive, 30% CPU, 20% I/O, 10% phase)", _MIXED, stream=4),
    Profile("W5", "All phase-changing", {PHASE: 1.0}, stream=5),
    Profile("W6", "Mixed at 3x arrival rate (overload)", _MIXED, 3.0, stream=4),
]}


@dataclass(frozen=True)
class ProcessSpec:
    """Everything about a process that is fixed before the simulation starts."""
    pid: int
    arrival: float
    kind: str
    bursts: tuple
    ios: tuple
    burst_classes: tuple   # true class of each burst (training labels only)

    @property
    def total_cpu(self) -> float:
        return sum(self.bursts)

    @property
    def total_io(self) -> float:
        return sum(self.ios)


def _draw_burst(rng, cls: str) -> float:
    dist, scale = CLASS_PARAMS[cls]["burst"]
    if dist == "lognormal":
        value = rng.lognormal(np.log(scale), LOGNORMAL_SIGMA)
    else:
        value = rng.exponential(scale)
    return max(float(value), MIN_TIME)


def _draw_io(rng, cls: str) -> float:
    return max(float(rng.exponential(CLASS_PARAMS[cls]["io_mean"])), MIN_TIME)


def make_process(rng, pid: int, kind: str, arrival: float = 0.0) -> ProcessSpec:
    """Draw one process of the given kind."""
    if kind == PHASE:
        n = int(rng.integers(PHASE_COUNT[0], PHASE_COUNT[1] + 1))
        half = n // 2
        classes = [IO] * half + [CPU] * (n - half)
    else:
        lo, hi = CLASS_PARAMS[kind]["count"]
        n = int(rng.integers(lo, hi + 1))
        classes = [kind] * n
    bursts = tuple(_draw_burst(rng, c) for c in classes)
    # The I/O wait after burst i follows the class of burst i.
    ios = tuple(_draw_io(rng, c) for c in classes[:-1])
    return ProcessSpec(pid, float(arrival), kind, bursts, ios, tuple(classes))


def generate_workload(profile, seed: int, n_processes: int = 200,
                      load: float = 0.85) -> list[ProcessSpec]:
    """Generate one instance of a workload profile (W1 to W6).

    Arrivals are Poisson. The arrival rate is chosen so that the offered CPU
    load (arrival rate x mean CPU demand per process) equals `load`, and is
    then multiplied by the profile's rate multiplier (3x for W6).
    """
    prof = PROFILES[profile] if isinstance(profile, str) else profile
    rng = np.random.default_rng([seed, prof.stream])
    kinds = list(prof.mix)
    chosen = rng.choice(len(kinds), size=n_processes, p=[prof.mix[k] for k in kinds])
    procs = [make_process(rng, i, kinds[c]) for i, c in enumerate(chosen)]

    mean_demand = float(np.mean([p.total_cpu for p in procs]))
    gaps = rng.exponential(mean_demand / load, n_processes) / prof.rate_multiplier
    arrivals = np.concatenate([[0.0], np.cumsum(gaps[1:])])
    return [replace(p, arrival=float(a)) for p, a in zip(procs, arrivals)]


SHIFT_SEGMENT_MS = 30_000.0
SHIFT_KINDS = (INTERACTIVE, CPU, IO)


def shifting_workload(seed: int = 0, segment_ms: float = SHIFT_SEGMENT_MS, load: float = 0.85,
                      kinds=SHIFT_KINDS) -> list[ProcessSpec]:
    """A workload whose process mix changes over time.

    Each segment of `segment_ms` brings only one kind of process. Used to show
    the time quantum following the workload.
    """
    rng = np.random.default_rng([seed, 99])
    procs, start = [], 0.0
    for kind in kinds:
        mean_demand = np.mean([make_process(rng, -1, kind).total_cpu for _ in range(300)])
        t = start
        while t < start + segment_ms:
            procs.append(make_process(rng, len(procs), kind, arrival=t))
            t += rng.exponential(mean_demand / load)
        start += segment_ms
    return procs


def simple_processes(bursts, arrivals=None) -> list[ProcessSpec]:
    """Single-burst processes with no I/O, for textbook examples."""
    arrivals = arrivals or [0.0] * len(bursts)
    return [ProcessSpec(i + 1, float(a), CPU, (float(b),), (), (CPU,))
            for i, (b, a) in enumerate(zip(bursts, arrivals))]
