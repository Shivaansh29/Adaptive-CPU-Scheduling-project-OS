"""The simulator must reproduce hand-computed textbook answers (Silberschatz, Ch. 5)."""
import pytest

from scheduler.baselines import FCFS, MLFQ, SJF, SRTF, Oracle, RoundRobin
from scheduler.engine import Simulator
from scheduler.metrics import per_process
from scheduler.predictor import EMAPredictor
from scheduler.workload import ProcessSpec, generate_workload, simple_processes


def avg_wait(specs, policy, switch_cost=0.0):
    result = Simulator(specs, policy, switch_cost).run()
    return per_process(result)["waiting"].mean(), result


def test_fcfs_convoy_example_gives_17():
    w, _ = avg_wait(simple_processes([24, 3, 3]), FCFS())
    assert w == pytest.approx(17.0)


def test_shortest_first_order_gives_3():
    w, _ = avg_wait(simple_processes([3, 3, 24]), FCFS())
    assert w == pytest.approx(3.0)


def test_oracle_on_convoy_example_gives_3():
    w, _ = avg_wait(simple_processes([24, 3, 3]), Oracle())
    assert w == pytest.approx(3.0)


def test_round_robin_q4_example():
    # P1 0-4, P2 4-7, P3 7-10, P1 10-30  ->  waits 6, 4, 7
    w, result = avg_wait(simple_processes([24, 3, 3]), RoundRobin(4))
    assert w == pytest.approx(17 / 3)
    assert result.context_switches == 4   # P1, P2, P3, P1 (P1 then keeps the CPU)


def test_srtf_with_true_bursts_example_gives_6_5():
    specs = simple_processes([8, 4, 9, 5], arrivals=[0, 1, 2, 3])
    w, _ = avg_wait(specs, Oracle())
    assert w == pytest.approx(6.5)


def test_context_switch_cost_is_charged():
    # Each dispatch costs 1 ms: P1 runs 1-25, P2 26-29, P3 30-33.
    w, result = avg_wait(simple_processes([24, 3, 3]), FCFS(), switch_cost=1.0)
    assert w == pytest.approx((1 + 26 + 30) / 3)
    assert result.switch_time == pytest.approx(3.0)


def test_io_is_not_counted_as_waiting():
    # P1: 4 ms CPU, 10 ms I/O, 4 ms CPU. P2: 6 ms CPU, runs while P1 is in I/O.
    specs = [ProcessSpec(1, 0.0, "cpu", (4.0, 4.0), (10.0,), ("cpu", "cpu")),
             ProcessSpec(2, 0.0, "cpu", (6.0,), (), ("cpu",))]
    result = Simulator(specs, FCFS(), 0.0).run()
    m = per_process(result)
    assert list(m["waiting"]) == pytest.approx([0.0, 4.0])
    assert result.processes[0].finish == pytest.approx(18.0)


def all_baselines():
    return [FCFS(), SJF(EMAPredictor()), SRTF(EMAPredictor()), RoundRobin(2),
            RoundRobin(20), MLFQ(), Oracle()]


@pytest.mark.parametrize("profile", ["W4", "W5"])
def test_cpu_service_is_identical_across_policies(profile):
    specs = generate_workload(profile, seed=0, n_processes=60)
    demand = sum(s.total_cpu for s in specs)
    for policy in all_baselines():
        result = Simulator(specs, policy, 0.1).run()
        assert result.busy_time == pytest.approx(demand, rel=1e-9), policy.name
        assert all(p.finish is not None for p in result.processes)
        assert min(per_process(result)["waiting"]) >= -1e-6


def test_event_times_are_monotonic_and_slices_do_not_overlap():
    specs = generate_workload("W4", seed=1, n_processes=60)
    for policy in all_baselines():
        result = Simulator(specs, policy, 0.1, record_events=True).run()
        times = [t for t, _, _ in result.events]
        assert times == sorted(times), policy.name
        for (s1, e1, _), (s2, e2, _) in zip(result.timeline, result.timeline[1:]):
            assert s1 < e1 <= s2 + 1e-9, policy.name
