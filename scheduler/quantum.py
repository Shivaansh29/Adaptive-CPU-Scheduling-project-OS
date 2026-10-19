"""Adaptive time quantum (the main idea of the project).

Textbooks say that about 80% of CPU bursts should finish within one quantum.
Applying that rule needs the burst distribution, which a normal scheduler never
measures, so a person picks a quantum once and leaves it. This controller
applies the rule continuously, using live predictions:

    every `epoch` scheduling decisions:
        q_new = clamp(percentile(predicted bursts seen this epoch, p), q_min, q_max)
        q     = gamma * q_new + (1 - gamma) * q        (smoothing)

A prediction is an average, so predictions are much less spread out than real
bursts. (I/O-bound bursts average 2 ms and every prediction is close to 2 ms,
but 20% of the real bursts are longer than 3.2 ms.) Taking the percentile of
raw predictions therefore gives a quantum that is too small. So each
prediction is multiplied by the recently observed ratios actual / predicted,
taken from the feedback loop, and the percentile is taken over those values:
an estimate of what the upcoming bursts will really look like.

Class modulation: if the processes seen in the epoch are mostly interactive, p
is lowered (smaller quantum, quicker response). If they are mostly CPU-bound,
p is raised (bigger quantum, fewer switches).
"""
from __future__ import annotations

from collections import deque

import numpy as np


def compute_quantum(predictions, p: float, q_min: float, q_max: float, ratios=None) -> float:
    """Percentile uses NumPy's default linear interpolation."""
    values = np.asarray(predictions, dtype=float)
    if ratios is not None and len(ratios):
        values = np.outer(values, ratios).ravel()   # every prediction x every recent error ratio
    return float(np.clip(np.percentile(values, p), q_min, q_max))


class QuantumController:

    def __init__(self, p: float = 80, epoch: int = 50, gamma: float = 0.3,
                 q_min: float = 1.0, q_max: float = 100.0, q_init: float = 10.0,
                 adaptive: bool = True, classifier=None, class_shift: float = 10.0,
                 min_samples: int = 5, error_window: int = 200):
        self.p = p
        self.epoch = epoch
        self.gamma = gamma
        self.q_min, self.q_max = q_min, q_max
        self.adaptive = adaptive
        self.classifier = classifier
        self.class_shift = class_shift
        self.min_samples = min_samples
        self.quantum = q_init
        self.trace = [(0.0, q_init, q_init, p)]   # (time, quantum, target, percentile)
        self._preds: list[float] = []
        self._pcbs: dict = {}
        self._ratios: deque = deque(maxlen=error_window)

    def observe(self, pcb) -> None:
        """Record the predicted length of a burst that just became ready."""
        self._preds.append(pcb.estimate)
        self._pcbs[pcb.pid] = pcb

    def observe_outcome(self, predicted: float, actual: float) -> None:
        """Record how a finished burst compared with its prediction."""
        self._ratios.append(min(max(actual / predicted, 0.01), 100.0))

    def epoch_percentile(self) -> float:
        if self.classifier is None or not self._pcbs:
            return self.p
        labels = self.classifier.classify(list(self._pcbs.values()))
        frac_cpu = labels.count("cpu") / len(labels)
        frac_int = labels.count("interactive") / len(labels)
        return float(np.clip(self.p + self.class_shift * (frac_cpu - frac_int), 50, 95))

    def end_epoch(self, now: float) -> None:
        if not self.adaptive or len(self._preds) < self.min_samples:
            return   # not enough evidence yet; keep collecting
        p = self.epoch_percentile()
        target = compute_quantum(self._preds, p, self.q_min, self.q_max, self._ratios)
        self.quantum = self.gamma * target + (1 - self.gamma) * self.quantum
        self.trace.append((now, self.quantum, target, p))
        self._preds = []
        self._pcbs = {}

    def stats(self) -> dict:
        return {"mean_quantum": float(np.mean([q for _, q, _, _ in self.trace]))}
