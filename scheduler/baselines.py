"""Classical scheduling policies used as baselines."""
from __future__ import annotations

from .engine import PCB, Policy
from .predictor import BurstPredictor


def estimated_remaining(estimate: float, done: float) -> float:
    """Predicted time left in a burst that has already run for `done` ms.

    If the burst has already outrun its prediction, the prediction was wrong
    and we have nothing better than the original estimate.
    """
    left = estimate - done
    return left if left > 0 else estimate


class FCFS(Policy):
    """First-Come-First-Served: run in arrival order until the process blocks."""
    name = "FCFS"

    def select(self, ready, now):
        return ready[0]


class RoundRobin(Policy):
    """FIFO order with a fixed time quantum."""

    def __init__(self, quantum: float):
        self.quantum = quantum
        self.name = f"RR-{quantum:g}"

    def select(self, ready, now):
        return ready[0]

    def time_slice(self, pcb, now):
        return self.quantum


class PredictivePolicy(Policy):
    """Base for policies that need a predicted burst length for each process."""

    def __init__(self, predictor: BurstPredictor):
        self.predictor = predictor

    def on_ready(self, pcb: PCB, now: float) -> None:
        if pcb.est_for != pcb.burst_index:   # a new burst: predict it once
            pcb.estimate = self.predictor.predict(pcb)
            pcb.est_for = pcb.burst_index

    def on_burst_complete(self, pcb, length, now):
        self.predictor.observe(pcb, length)

    def stats(self):
        return self.predictor.stats()


class SJF(PredictivePolicy):
    """Non-preemptive Shortest-Job-First using predicted (not true) bursts."""

    def __init__(self, predictor):
        super().__init__(predictor)
        self.name = f"SJF-{predictor.name}"

    def select(self, ready, now):
        return min(ready, key=lambda p: p.estimate)


class SRTF(PredictivePolicy):
    """Shortest-Remaining-Time-First using predicted bursts.

    Preempts the running process when a newly ready process has a shorter
    predicted remaining time.
    """
    preemptive = True

    def __init__(self, predictor):
        super().__init__(predictor)
        self.name = f"SRTF-{predictor.name}"

    def select(self, ready, now):
        return min(ready, key=lambda p: estimated_remaining(p.estimate, p.burst_done))

    def should_preempt(self, running, ran, newcomer, now):
        left = estimated_remaining(running.estimate, running.burst_done + ran)
        return estimated_remaining(newcomer.estimate, newcomer.burst_done) < left


class Oracle(Policy):
    """Best possible case: SRTF that knows every true burst length.

    No real scheduler can do this. It is the reference point for how much of
    the achievable improvement a predictor captures.
    """
    name = "Oracle"
    preemptive = True

    def select(self, ready, now):
        return min(ready, key=lambda p: p.remaining)

    def should_preempt(self, running, ran, newcomer, now):
        return newcomer.remaining < running.remaining - ran


class MLFQ(Policy):
    """Multilevel feedback queue (OSTEP style).

    Three levels with quanta 4, 8 and 16 ms. A process that uses its whole
    quantum moves down a level. Every 200 ms all processes are boosted back to
    the top level so long jobs cannot starve. A process in a higher level
    preempts one running from a lower level.
    """
    name = "MLFQ"
    preemptive = True

    def __init__(self, quanta=(4.0, 8.0, 16.0), boost_period: float = 200.0):
        self.quanta = quanta
        self.boost_period = boost_period
        self._next_boost = boost_period
        self._seen: list[PCB] = []
        self._seen_ids: set[int] = set()

    def on_ready(self, pcb, now):
        if pcb.pid not in self._seen_ids:
            self._seen_ids.add(pcb.pid)
            self._seen.append(pcb)

    def _maybe_boost(self, now):
        if now < self._next_boost:
            return
        self._seen = [p for p in self._seen if p.finish is None]
        for p in self._seen:
            p.level = 0
        while self._next_boost <= now:
            self._next_boost += self.boost_period

    def select(self, ready, now):
        self._maybe_boost(now)
        return min(ready, key=lambda p: (p.level, p.ready_since))

    def time_slice(self, pcb, now):
        return self.quanta[pcb.level]

    def on_quantum_expired(self, pcb, ran, now):
        pcb.level = min(pcb.level + 1, len(self.quanta) - 1)

    def should_preempt(self, running, ran, newcomer, now):
        return newcomer.level < running.level
