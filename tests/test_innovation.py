"""Tests for the post-Review 3 additions: noisy oracle, overrun guard,
persistent ageing credit and the W7 bait-and-switch workload."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scheduler.adaptive import AdaptiveScheduler, guarded_remaining
from scheduler.baselines import SJF, Oracle
from scheduler.configs import run_policy
from scheduler.engine import PCB, Simulator
from scheduler.metrics import summarize
from scheduler.predictor import EMAPredictor, NoisyOraclePredictor
from scheduler.quantum import QuantumController
from scheduler.workload import BAIT, PROFILES, ProcessSpec, generate_workload

RESULTS = Path(__file__).resolve().parent.parent / "results" / "main_results.csv"


def make_pcb(bursts, pid=0, estimate=0.0):
    p = PCB(ProcessSpec(pid, 0, "cpu", tuple(bursts), (1.0,) * (len(bursts) - 1),
                        ("cpu",) * len(bursts)))
    p.estimate, p.est_for = estimate, 0
    return p


# ------------------------------------------------------------ noisy oracle
def test_noisy_oracle_with_zero_noise_returns_the_true_burst():
    p = make_pcb([7.5, 3.0])
    assert NoisyOraclePredictor(0.0).predict(p) == 7.5


def test_noisy_oracle_is_deterministic_per_burst():
    p = make_pcb([10.0, 3.0], pid=4)
    a, b = NoisyOraclePredictor(0.5, seed=1), NoisyOraclePredictor(0.5, seed=1)
    assert a.predict(p) == b.predict(p)
    assert a.predict(p) != NoisyOraclePredictor(0.5, seed=2).predict(p)


def test_noisy_oracle_error_has_the_requested_spread():
    pred = NoisyOraclePredictor(0.5)
    logs = [np.log(pred.predict(make_pcb([10.0], pid=i)) / 10.0) for i in range(4000)]
    assert np.std(logs) == pytest.approx(0.5, abs=0.03)


def test_sjf_with_a_perfect_predictor_is_non_preemptive_true_sjf():
    # Single bursts, all at time 0: SJF with true lengths runs them shortest first.
    specs = [ProcessSpec(i, 0.0, "cpu", (b,), (), ("cpu",)) for i, b in enumerate([8, 2, 5])]
    result = Simulator(specs, SJF(NoisyOraclePredictor(0.0)), 0.0).run()
    assert [pid for _, _, pid in result.timeline] == [1, 2, 0]
    oracle = Simulator(specs, Oracle(), 0.0).run()
    assert result.timeline == oracle.timeline


# ----------------------------------------------------------- overrun guard
def test_guard_changes_nothing_before_the_threshold():
    assert guarded_remaining(10, 4, 2.0, 1.0) == 6
    assert guarded_remaining(10, 15, 2.0, 1.0) == 10   # outran the guess, below 2x: as before


def test_guard_demotes_a_burst_past_the_threshold():
    assert guarded_remaining(10, 25, 2.0, 1.0) == 25   # 25 > 10 * 2: time left = c * done
    assert guarded_remaining(10, 25, 2.0, 0.5) == 12.5
    assert guarded_remaining(10, 11, 0.5, 1.0) == 11   # the limit ratio is never below 1


def test_guard_never_makes_a_burst_look_shorter():
    assert guarded_remaining(10, 25, 2.0, 0.25) == 10  # 0.25 * 25 < 10: keep the estimate
    for done in (21, 50, 400):
        assert guarded_remaining(10, done, 2.0, 0.5) >= 10


def test_guard_lets_a_fresh_short_job_beat_an_overrunning_one():
    overrun = make_pcb([500.0], pid=1, estimate=2.0)
    overrun.burst_done = 60.0
    fresh = make_pcb([5.0], pid=2, estimate=5.0)
    plain = AdaptiveScheduler(EMAPredictor(), QuantumController(), beta=0.0)
    assert plain.select([overrun, fresh], now=0) is overrun     # still looks like 2 ms
    guarded = AdaptiveScheduler(EMAPredictor(), QuantumController(), beta=0.0, overrun_c=1.0)
    assert guarded.select([overrun, fresh], now=0) is fresh     # looks like 60 ms now


# ------------------------------------------------------ persistent ageing
def test_persistent_credit_survives_time_slices_and_resets_per_burst():
    sched = AdaptiveScheduler(EMAPredictor(), QuantumController(), beta=0.0,
                              persistent_ageing=True)
    p = make_pcb([30.0, 1.0], pid=3)
    p.est_for = -1
    sched.on_ready(p, now=0.0)            # burst 0 becomes ready
    sched._credit[3] = 25.0               # ... and waits 25 ms over several stays
    sched.on_ready(p, now=40.0)           # back from a time slice: same burst
    assert sched._credit[3] == 25.0
    p.burst_index = 1
    sched.on_ready(p, now=50.0)           # a new burst: credit starts again
    assert sched._credit[3] == 0.0
    # Waited = earlier stays in this burst + the current stay.
    pcb = make_pcb([5.0], pid=9)
    sched._credit[9] = 40.0
    pcb.ready_since = 100.0
    assert sched.waited(pcb, now=103.0) == pytest.approx(43.0)
    sched.persistent_ageing = False
    assert sched.waited(pcb, now=103.0) == pytest.approx(3.0)


def test_persistent_credit_accumulates_across_quantum_expiries():
    specs = [ProcessSpec(0, 0.0, "cpu", (25.0,), (), ("cpu",)),
             ProcessSpec(1, 0.0, "cpu", (25.0,), (), ("cpu",))]
    seen = []

    class Spy(AdaptiveScheduler):
        def select(self, ready, now):
            chosen = super().select(ready, now)
            seen.append((now, chosen.pid, self._credit[chosen.pid]))
            return chosen

    sched = Spy(EMAPredictor(), QuantumController(adaptive=False, q_init=10.0),
                beta=0.0, persistent_ageing=True)
    Simulator(specs, sched, 0.0).run()
    credit_1 = [c for _, pid, c in seen if pid == 1]
    # pid 1 waited 10 ms, then (after its own slice) another 10 ms, and so on.
    assert credit_1[0] == pytest.approx(10.0)
    assert credit_1[1] == pytest.approx(20.0)


# ------------------------------------------------------------- workload W7
def test_w7_is_reproducible_and_has_bait_processes():
    a, b = generate_workload("W7", 3), generate_workload("W7", 3)
    assert a == b
    bait = [p for p in a if p.kind == BAIT]
    assert bait
    for p in bait:
        long_bursts = [x for x in p.bursts if x > 100]
        assert len(long_bursts) == 2
        assert len(p.ios) == len(p.bursts) - 1


def test_main_profiles_still_exclude_w7():
    assert list(PROFILES) == ["W1", "W2", "W3", "W4", "W5", "W6"]


# --------------------------------------------- existing behaviour unchanged
@pytest.mark.skipif(not RESULTS.exists(), reason="main results not generated")
@pytest.mark.parametrize("policy", ["Adaptive-EMA", "SJF-EMA", "RR-5"])
def test_existing_configurations_reproduce_saved_results(policy):
    saved = pd.read_csv(RESULTS)
    row = saved[(saved.workload == "W4") & (saved.seed == 0) & (saved.policy == policy)].iloc[0]
    _, now = run_policy(generate_workload("W4", 0), policy)
    assert now["avg_wait"] == pytest.approx(row["avg_wait"], rel=1e-12)
    assert now["context_switches"] == row["context_switches"]


def test_safeguards_off_means_identical_schedule():
    specs = generate_workload("W4", 5, n_processes=60)
    plain = Simulator(specs, AdaptiveScheduler(EMAPredictor(), QuantumController(), 0.03), 0.1).run()
    off = AdaptiveScheduler(EMAPredictor(), QuantumController(), 0.03,
                            overrun_c=None, persistent_ageing=False)
    assert Simulator(specs, off, 0.1).run().timeline == plain.timeline
    assert summarize(plain)["avg_wait"] > 0
