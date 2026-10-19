"""The scheduler configurations compared in the experiments, built by name."""
from __future__ import annotations

import time
from functools import lru_cache
from pathlib import Path

from . import metrics
from .adaptive import AdaptiveScheduler
from .baselines import FCFS, MLFQ, SJF, SRTF, Oracle, RoundRobin
from .engine import Simulator
from .predictor import EMAPredictor, MLPredictor, ProcessClassifier, load_bundle
from .quantum import QuantumController

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"

# The 11 configurations of the main experiment.
MAIN_CONFIGS = [
    "FCFS", "SJF-EMA", "SRTF-EMA", "RR-2", "RR-5", "RR-10", "RR-20",
    "MLFQ", "Oracle", "Adaptive-EMA", "Adaptive-ML",
]

DESCRIPTIONS = {
    "FCFS": "First-Come-First-Served",
    "SJF-EMA": "Shortest-Job-First, bursts guessed by exponential averaging (alpha 0.5)",
    "SRTF-EMA": "Shortest-Remaining-Time-First, same guess, preemptive",
    "RR-2": "Round Robin, 2 ms quantum",
    "RR-5": "Round Robin, 5 ms quantum",
    "RR-10": "Round Robin, 10 ms quantum",
    "RR-20": "Round Robin, 20 ms quantum",
    "MLFQ": "Multilevel feedback queue, 3 levels (4/8/16 ms), boost every 200 ms",
    "Oracle": "Best possible case: SRTF that knows the true burst lengths",
    "Adaptive-EMA": "Our scheduler, but with exponential averaging as the predictor",
    "Adaptive-ML": "Our scheduler: learned predictor + ageing + adaptive quantum",
}

# beta (ageing weight) was chosen by tune_beta.py on tuning seeds 100-102,
# which the main experiment never uses. Everything else is the Review 1 plan.
ADAPTIVE_DEFAULTS = dict(
    beta=0.03, p=80, epoch=50, gamma=0.3, q_min=1.0, q_max=100.0, q_init=10.0,
    adaptive_quantum=True, class_mod=True, use_quantum=True, online=True,
)

# Ablation study: switch off one part of Adaptive-ML at a time.
ABLATIONS = {
    "Full": {},
    "No ageing": {"beta": 0.0},
    "Fixed quantum": {"adaptive_quantum": False},
    "No class modulation": {"class_mod": False},
    "No online refit": {"online": False},
    "Prediction only": {"beta": 0.0, "use_quantum": False},
}


@lru_cache(maxsize=1)
def load_models():
    return (load_bundle(MODEL_DIR / "burst_model.joblib"),
            load_bundle(MODEL_DIR / "class_model.joblib"))


def make_policy(name: str, **overrides):
    if name == "FCFS":
        return FCFS()
    if name == "SJF-EMA":
        return SJF(EMAPredictor())
    if name == "SRTF-EMA":
        return SRTF(EMAPredictor())
    if name.startswith("RR-"):
        return RoundRobin(float(name[3:]))
    if name == "MLFQ":
        return MLFQ()
    if name == "Oracle":
        return Oracle()
    if name in ("Adaptive-EMA", "Adaptive-ML"):
        cfg = {**ADAPTIVE_DEFAULTS, **overrides}
        burst_bundle, class_bundle = load_models()
        if name == "Adaptive-ML":
            predictor = MLPredictor(burst_bundle, online=cfg["online"])
        else:
            predictor = EMAPredictor()
        classifier = ProcessClassifier(class_bundle) if cfg["class_mod"] else None
        controller = QuantumController(
            p=cfg["p"], epoch=cfg["epoch"], gamma=cfg["gamma"], q_min=cfg["q_min"],
            q_max=cfg["q_max"], q_init=cfg["q_init"], adaptive=cfg["adaptive_quantum"],
            classifier=classifier)
        return AdaptiveScheduler(predictor, controller, beta=cfg["beta"],
                                 use_quantum=cfg["use_quantum"], name=name)
    raise ValueError(f"unknown policy {name!r}")


def run_policy(specs, name: str, switch_cost: float = 0.1, record_events: bool = False,
               **overrides):
    """Simulate one workload under one policy. Returns (SimResult, summary row)."""
    policy = make_policy(name, **overrides)
    start = time.perf_counter()
    result = Simulator(specs, policy, switch_cost, record_events).run()
    row = metrics.summarize(result)
    row.update(policy.stats())
    row["wall_s"] = time.perf_counter() - start
    return result, row
