"""The proposed adaptive scheduler.

The predicted burst length is used twice:

1. Ordering the ready queue. Each ready process gets
       P = predicted time left in its burst - beta * time it has waited in the queue
   and the lowest P runs next. With beta = 0 this is exactly SJF on predicted
   bursts. The ageing term stops long processes from starving.

2. Sizing the time quantum, through the QuantumController.

Two optional safeguards (both off by default, so Adaptive-ML is unchanged):

* Overrun guard. Once a burst has run longer than estimate * r_q, where r_q is
  the q-th percentile of recently observed actual / predicted ratios, the
  prediction is treated as wrong and the time left is taken as
  max(estimate, c * time already run). It never looks shorter than before, and
  a burst that keeps running loses priority in proportion to the CPU time it
  has had, instead of looking like a short job every time it comes back from a
  time slice.
* Persistent ageing. The waiting term normally counts only the current stay in
  the ready queue, which restarts after every time slice. With this option it
  counts all ready-queue time since the burst started.
"""
from __future__ import annotations

import math

from .baselines import PredictivePolicy, estimated_remaining
from .quantum import QuantumController


def priority_score(predicted_left: float, waited: float, beta: float) -> float:
    return predicted_left - beta * waited


def guarded_remaining(estimate: float, done: float, limit_ratio: float, c: float) -> float:
    """Time left in a burst, distrusting the estimate once it is clearly exceeded."""
    if done <= estimate * max(limit_ratio, 1.0):
        return estimated_remaining(estimate, done)
    return max(estimate, c * done)


class AdaptiveScheduler(PredictivePolicy):

    def __init__(self, predictor, controller: QuantumController, beta: float = 0.1,
                 use_quantum: bool = True, name: str | None = None,
                 overrun_c: float | None = None, overrun_q: float = 90,
                 persistent_ageing: bool = False):
        super().__init__(predictor)
        self.controller = controller
        self.beta = beta
        self.use_quantum = use_quantum   # False = run each burst to completion
        self.name = name or f"Adaptive-{predictor.name}"
        self.decisions = 0
        self.overrun_c = overrun_c       # None = no overrun guard
        self.overrun_q = overrun_q
        self.limit_ratio = 1.0           # r_q, refreshed every epoch
        self.persistent_ageing = persistent_ageing
        self._credit: dict = {}          # pid -> ready time in earlier stays of this burst
        self.overruns = 0                # priority evaluations made by the guard

    def on_ready(self, pcb, now):
        new_burst = pcb.est_for != pcb.burst_index
        super().on_ready(pcb, now)
        if new_burst:
            self.controller.observe(pcb)
            self._credit[pcb.pid] = 0.0

    def waited(self, pcb, now) -> float:
        stay = now - pcb.ready_since
        return stay + self._credit.get(pcb.pid, 0.0) if self.persistent_ageing else stay

    def priority(self, pcb, now) -> float:
        if self.overrun_c is None:
            left = estimated_remaining(pcb.estimate, pcb.burst_done)
        else:
            left = guarded_remaining(pcb.estimate, pcb.burst_done, self.limit_ratio,
                                     self.overrun_c)
            if pcb.burst_done > pcb.estimate * max(self.limit_ratio, 1.0):
                self.overruns += 1
        return priority_score(left, self.waited(pcb, now), self.beta)

    def select(self, ready, now):
        self.decisions += 1
        if self.decisions % self.controller.epoch == 0:
            self.controller.end_epoch(now)
            if self.overrun_c is not None:
                self.limit_ratio = self.controller.ratio_percentile(self.overrun_q)
        chosen = min(ready, key=lambda p: self.priority(p, now))
        if self.persistent_ageing:
            self._credit[chosen.pid] = self._credit.get(chosen.pid, 0.0) + now - chosen.ready_since
        return chosen

    def on_burst_complete(self, pcb, length, now):
        self.controller.observe_outcome(pcb.estimate, length)
        super().on_burst_complete(pcb, length, now)

    def time_slice(self, pcb, now):
        return self.controller.quantum if self.use_quantum else math.inf

    def stats(self):
        extra = {"guard_evals": self.overruns} if self.overrun_c is not None else {}
        return {**self.predictor.stats(), **self.controller.stats(), **extra}
