import math

import pytest

from scheduler.adaptive import AdaptiveScheduler, priority_score
from scheduler.baselines import SJF, estimated_remaining
from scheduler.engine import PCB, Simulator
from scheduler.metrics import per_process
from scheduler.predictor import EMAPredictor
from scheduler.quantum import QuantumController, compute_quantum
from scheduler.workload import ProcessSpec, generate_workload


def test_ageing_priority_example():
    # beta 0.1, predicted burst 50, waited 400  ->  priority 10
    assert priority_score(50, 400, 0.1) == pytest.approx(10)


def test_quantum_percentile_uses_linear_interpolation():
    assert compute_quantum([2, 4, 6, 8, 10], 80, 1, 100) == pytest.approx(8.4)


def test_quantum_is_clamped():
    assert compute_quantum([0.1, 0.2, 0.3], 80, 1, 100) == 1
    assert compute_quantum([500, 600], 80, 1, 100) == 100


def test_quantum_accounts_for_prediction_error():
    # All predictions are 2 ms, but real bursts came out between 0.5x and 2x.
    plain = compute_quantum([2, 2, 2], 80, 1, 100)
    aware = compute_quantum([2, 2, 2], 80, 1, 100, ratios=[0.5, 1.0, 1.5, 2.0])
    assert plain == pytest.approx(2) and aware > plain


def test_estimated_remaining():
    assert estimated_remaining(10, 4) == 6
    assert estimated_remaining(10, 15) == 10   # outran the guess: fall back to the guess


def test_ageing_lets_a_long_waiting_process_go_first():
    def pcb(estimate, ready_since):
        p = PCB(ProcessSpec(0, 0, "cpu", (1.0,), (), ("cpu",)))
        p.estimate, p.est_for, p.ready_since = estimate, 0, ready_since
        return p

    old_long, new_short = pcb(50, 0), pcb(5, 590)
    sched = AdaptiveScheduler(EMAPredictor(), QuantumController(), beta=0.1)
    assert sched.select([new_short, old_long], now=600) is old_long   # 50-60 < 5-1
    sched.beta = 0.0
    assert sched.select([new_short, old_long], now=600) is new_short  # plain SJF


def test_beta_zero_without_quantum_is_exactly_sjf():
    """Stepwise integration check from the plan: with ageing and the quantum
    switched off, the adaptive scheduler must reproduce predicted-burst SJF."""
    specs = generate_workload("W4", seed=3, n_processes=80)
    sjf = Simulator(specs, SJF(EMAPredictor()), 0.1).run()
    adaptive = AdaptiveScheduler(EMAPredictor(), QuantumController(adaptive=False),
                                 beta=0.0, use_quantum=False)
    ours = Simulator(specs, adaptive, 0.1).run()
    assert sjf.timeline == ours.timeline
    assert per_process(sjf)["waiting"].tolist() == per_process(ours)["waiting"].tolist()


def test_quantum_controller_moves_towards_the_target():
    c = QuantumController(p=80, epoch=1, gamma=0.5, q_init=10, min_samples=1)
    for _ in range(5):
        p = PCB(ProcessSpec(0, 0, "cpu", (1.0,), (), ("cpu",)))
        p.estimate = 50.0
        c.observe(p)
    c.end_epoch(now=1.0)
    assert c.quantum == pytest.approx(0.5 * 50 + 0.5 * 10)
    assert not math.isnan(c.stats()["mean_quantum"])
