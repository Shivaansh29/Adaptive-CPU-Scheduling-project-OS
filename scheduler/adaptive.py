"""The proposed adaptive scheduler.

The predicted burst length is used twice:

1. Ordering the ready queue. Each ready process gets
       P = predicted time left in its burst - beta * time it has waited in the queue
   and the lowest P runs next. With beta = 0 this is exactly SJF on predicted
   bursts. The ageing term stops long processes from starving.

2. Sizing the time quantum, through the QuantumController.
"""
from __future__ import annotations

import math

from .baselines import PredictivePolicy, estimated_remaining
from .quantum import QuantumController


def priority_score(predicted_left: float, waited: float, beta: float) -> float:
    return predicted_left - beta * waited


class AdaptiveScheduler(PredictivePolicy):

    def __init__(self, predictor, controller: QuantumController, beta: float = 0.1,
                 use_quantum: bool = True, name: str | None = None):
        super().__init__(predictor)
        self.controller = controller
        self.beta = beta
        self.use_quantum = use_quantum   # False = run each burst to completion
        self.name = name or f"Adaptive-{predictor.name}"
        self.decisions = 0

    def on_ready(self, pcb, now):
        new_burst = pcb.est_for != pcb.burst_index
        super().on_ready(pcb, now)
        if new_burst:
            self.controller.observe(pcb)

    def priority(self, pcb, now) -> float:
        left = estimated_remaining(pcb.estimate, pcb.burst_done)
        return priority_score(left, now - pcb.ready_since, self.beta)

    def select(self, ready, now):
        self.decisions += 1
        if self.decisions % self.controller.epoch == 0:
            self.controller.end_epoch(now)
        return min(ready, key=lambda p: self.priority(p, now))

    def on_burst_complete(self, pcb, length, now):
        self.controller.observe_outcome(pcb.estimate, length)
        super().on_burst_complete(pcb, length, now)

    def time_slice(self, pcb, now):
        return self.controller.quantum if self.use_quantum else math.inf

    def stats(self):
        return {**self.predictor.stats(), **self.controller.stats()}
