"""Burst-length predictors and the process-type classifier.

EMAPredictor is the classical exponential average used by real systems.
MLPredictor wraps a scikit-learn regressor trained by train_models.py. Both log
their own error and latency so every run can report prediction accuracy.
"""
from __future__ import annotations

import math
import time
from collections import deque
from pathlib import Path

import joblib
import numpy as np
from sklearn.base import clone

from .features import EMA_ALPHA, EMA_TAU0, ema_estimate, features_for

MIN_PREDICTION = 0.1   # ms. Predictions are clamped so they are always positive.


class BurstPredictor:
    """Base class: times every prediction and logs every error."""
    name = "base"

    def __init__(self):
        self._n = 0
        self._abs_err = 0.0
        self._sq_err = 0.0
        self._calls = 0
        self._seconds = 0.0

    def predict(self, pcb) -> float:
        start = time.perf_counter()
        value = self._predict(pcb)
        self._seconds += time.perf_counter() - start
        self._calls += 1
        return max(MIN_PREDICTION, value)

    def observe(self, pcb, actual: float) -> None:
        """Fast feedback loop: called when a burst finishes, with its real length.

        `pcb.estimate` holds the prediction that was made for this burst.
        """
        err = actual - pcb.estimate
        self._n += 1
        self._abs_err += abs(err)
        self._sq_err += err * err
        self._learn(pcb, actual)

    def stats(self) -> dict:
        n = max(self._n, 1)
        return {
            "pred_mae": self._abs_err / n,
            "pred_rmse": math.sqrt(self._sq_err / n),
            "pred_latency_us": 1e6 * self._seconds / max(self._calls, 1),
        }

    def _predict(self, pcb) -> float:
        raise NotImplementedError

    def _learn(self, pcb, actual: float) -> None:
        pass


class EMAPredictor(BurstPredictor):
    name = "EMA"

    def __init__(self, alpha: float = EMA_ALPHA, tau0: float = EMA_TAU0):
        super().__init__()
        self.alpha, self.tau0 = alpha, tau0

    def _predict(self, pcb) -> float:
        return ema_estimate(pcb.history, self.alpha, self.tau0)


class MLPredictor(BurstPredictor):
    """Learned predictor with an optional online refit (the slow feedback loop).

    Every completed burst becomes a new training example in a rolling buffer.
    After `refit_every` new examples the model is refit on the offline training
    data plus the buffer.
    """
    name = "ML"

    def __init__(self, bundle: dict, online: bool = True,
                 refit_every: int = 2000, buffer_size: int = 4000):
        super().__init__()
        self.model = bundle["model"]
        self.log_target = bundle["log_target"]
        self.base_X, self.base_y = bundle["train_X"], bundle["train_y"]
        self.online = online
        self.refit_every = refit_every
        self.buf_X: deque = deque(maxlen=buffer_size)
        self.buf_y: deque = deque(maxlen=buffer_size)
        self._new = 0
        self.refits = 0

    def _predict(self, pcb) -> float:
        x = features_for(pcb)
        pcb.features = x
        y = float(self.model.predict(np.asarray([x]))[0])
        return math.expm1(y) if self.log_target else y

    def _learn(self, pcb, actual: float) -> None:
        if not self.online or pcb.features is None:
            return
        self.buf_X.append(pcb.features)
        self.buf_y.append(actual)
        self._new += 1
        if self._new >= self.refit_every:
            self._refit()

    def _refit(self) -> None:
        X = np.vstack([self.base_X, np.asarray(self.buf_X)])
        y = np.concatenate([self.base_y, np.asarray(self.buf_y)])
        if self.log_target:
            y = np.log1p(y)
        self.model = clone(self.model).fit(X, y)   # a new object; the shared bundle is untouched
        self._new = 0
        self.refits += 1

    def stats(self) -> dict:
        return {**super().stats(), "refits": self.refits}


class ProcessClassifier:
    """Labels processes as cpu, io or interactive from their history."""

    def __init__(self, bundle: dict):
        self.model = bundle["model"]

    def classify(self, pcbs) -> list[str]:
        if not pcbs:
            return []
        return list(self.model.predict(np.asarray([features_for(p) for p in pcbs])))


def load_bundle(path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Train the models first:  python train_models.py")
    return joblib.load(path)
