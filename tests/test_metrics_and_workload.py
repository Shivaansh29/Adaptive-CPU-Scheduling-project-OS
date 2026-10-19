import numpy as np
import pytest

from scheduler.baselines import MLFQ
from scheduler.engine import PCB, Simulator
from scheduler.metrics import count_starved, jain_index, oracle_gap_closed
from scheduler.workload import (CPU, IO, PHASE, PROFILES, ProcessSpec, generate_workload,
                                simple_processes)


def test_jain_index():
    assert jain_index([1, 1, 1, 1]) == pytest.approx(1.0)
    assert jain_index([1, 0, 0]) == pytest.approx(1 / 3)


def test_oracle_gap_closed():
    assert oracle_gap_closed(10, 6, 2) == pytest.approx(50.0)


def test_count_starved():
    assert count_starved([1, 5, 50, 60], threshold=40) == 2


def test_workload_is_reproducible():
    a = generate_workload("W4", seed=7, n_processes=50)
    b = generate_workload("W4", seed=7, n_processes=50)
    assert a == b
    assert a != generate_workload("W4", seed=8, n_processes=50)


def test_w6_is_w4_with_three_times_the_arrival_rate():
    w4 = generate_workload("W4", seed=0, n_processes=50)
    w6 = generate_workload("W6", seed=0, n_processes=50)
    assert [p.bursts for p in w4] == [p.bursts for p in w6]
    assert w6[-1].arrival == pytest.approx(w4[-1].arrival / 3)


@pytest.mark.parametrize("name", list(PROFILES))
def test_process_structure(name):
    for p in generate_workload(name, seed=0, n_processes=40):
        assert len(p.ios) == len(p.bursts) - 1
        assert min(p.bursts) > 0 and (not p.ios or min(p.ios) > 0)
        if p.kind == PHASE:
            half = len(p.bursts) // 2
            assert p.burst_classes == (IO,) * half + (CPU,) * (len(p.bursts) - half)


def test_offered_load_matches_target():
    specs = generate_workload("W4", seed=0, n_processes=200, load=0.85)
    demand = sum(p.total_cpu for p in specs)
    span = specs[-1].arrival
    assert demand / span == pytest.approx(0.85, rel=0.25)


def test_mlfq_demotes_a_process_that_uses_its_whole_quantum():
    specs = simple_processes([30])
    policy = MLFQ()
    result = Simulator(specs, policy, 0.0).run()
    assert result.processes[0].level == 2
    # Slices of 4, 8, 16 then the remaining 2 ms at the bottom level.
    assert [round(e - s, 6) for s, e, _ in result.timeline] == [4, 8, 16, 2]
