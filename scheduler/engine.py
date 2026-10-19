"""Discrete-event simulation of a single CPU.

The engine owns the clock, the event queue and the process control blocks
(PCBs). It never decides who runs next. Every decision is delegated to a
Policy object, so all schedulers see identical arrivals, bursts, I/O times
and context-switch costs, and differ only in their decisions.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

from .workload import ProcessSpec

EPS = 1e-9

# Event kinds. Events at the same instant are handled in this order, so a
# finishing slice releases the CPU before newly ready processes are considered.
SLICE_END, IO_DONE, ARRIVAL = 0, 1, 2
EVENT_NAMES = {SLICE_END: "SLICE_END", IO_DONE: "IO_DONE", ARRIVAL: "ARRIVAL"}


@dataclass(eq=False, slots=True)
class PCB:
    """Process control block: the run-time state of one process."""
    spec: ProcessSpec
    burst_index: int = 0       # which CPU burst the process is on
    remaining: float = 0.0     # TRUE remaining time of the current burst.
                               # Only the engine and the oracle may read this.
    burst_done: float = 0.0    # CPU time already received in the current burst
    history: list = field(default_factory=list)     # lengths of completed bursts
    io_history: list = field(default_factory=list)  # lengths of completed I/O waits
    ready_since: float = 0.0   # when the process last entered the ready queue
    first_run: float | None = None
    finish: float | None = None
    # Scratch space owned by the policies.
    estimate: float = 0.0      # predicted length of the current burst
    est_for: int = -1          # burst index that `estimate` was made for
    level: int = 0             # MLFQ queue level
    features: list | None = None   # feature vector behind the last prediction

    @property
    def pid(self) -> int:
        return self.spec.pid

    @property
    def arrival(self) -> float:
        return self.spec.arrival

    @property
    def kind(self) -> str:
        return self.spec.kind


class Policy:
    """Interface every scheduling policy implements. The engine calls the hooks."""
    name = "policy"
    preemptive = False   # may a newly ready process interrupt the running one?

    def on_ready(self, pcb: PCB, now: float) -> None:
        """`pcb` has just entered the ready queue."""

    def select(self, ready: list[PCB], now: float) -> PCB:
        """Pick the next process to run from the ready queue."""
        raise NotImplementedError

    def time_slice(self, pcb: PCB, now: float) -> float:
        """How long `pcb` may run before it is preempted (inf = until it blocks)."""
        return math.inf

    def should_preempt(self, running: PCB, ran: float, newcomer: PCB, now: float) -> bool:
        """Called for preemptive policies when `newcomer` becomes ready."""
        return False

    def on_quantum_expired(self, pcb: PCB, ran: float, now: float) -> None:
        pass

    def on_preempt(self, pcb: PCB, ran: float, now: float) -> None:
        pass

    def on_burst_complete(self, pcb: PCB, length: float, now: float) -> None:
        pass

    def stats(self) -> dict:
        """Extra numbers to report for this run (prediction error and so on)."""
        return {}


@dataclass
class SimResult:
    policy: str
    processes: list
    context_switches: int
    busy_time: float      # total CPU time spent running processes
    switch_time: float    # total CPU time spent on context switches
    end_time: float
    timeline: list        # (start, end, pid) for every slice that ran
    events: list | None   # (time, event name, pid) if recording was on
    policy_obj: Policy | None = None


class Simulator:
    """Runs one workload under one policy."""

    def __init__(self, specs: list[ProcessSpec], policy: Policy,
                 switch_cost: float = 0.1, record_events: bool = False):
        self.pcbs = [PCB(s) for s in specs]
        self.policy = policy
        self.switch_cost = switch_cost
        self.now = 0.0
        self.ready: list[PCB] = []
        self.running: PCB | None = None
        self.context_switches = 0
        self.busy_time = 0.0
        self.timeline: list = []
        self.events: list | None = [] if record_events else None
        self._heap: list = []
        self._seq = 0              # tie-breaker so the heap never compares PCBs
        self._token = 0            # bumping it cancels a pending SLICE_END
        self._run_start = 0.0      # when the running process got the CPU
        self._last_run: PCB | None = None

    # ------------------------------------------------------------------ events
    def _push(self, time: float, kind: int, pcb: PCB, token: int = 0) -> None:
        heapq.heappush(self._heap, (time, kind, self._seq, pcb, token))
        self._seq += 1

    def run(self) -> SimResult:
        for pcb in self.pcbs:
            self._push(pcb.arrival, ARRIVAL, pcb)

        while self._heap:
            self.now = self._heap[0][0]
            # Handle every event at this instant before making a decision, so
            # that processes arriving together are all considered.
            while self._heap and self._heap[0][0] == self.now:
                _, kind, _, pcb, token = heapq.heappop(self._heap)
                if kind == SLICE_END and token != self._token:
                    continue  # the slice was cut short by a preemption
                if self.events is not None:
                    self.events.append((self.now, EVENT_NAMES[kind], pcb.pid))
                if kind == SLICE_END:
                    self._stop_running(preempted=False)
                elif kind == IO_DONE:
                    pcb.io_history.append(pcb.spec.ios[pcb.burst_index - 1])
                    self._start_burst(pcb)
                else:
                    self._start_burst(pcb)
            if self.running is None and self.ready:
                self._dispatch()

        unfinished = [p.pid for p in self.pcbs if p.finish is None]
        assert not unfinished, f"processes never finished: {unfinished[:5]}"
        return SimResult(
            policy=self.policy.name,
            processes=self.pcbs,
            context_switches=self.context_switches,
            busy_time=self.busy_time,
            switch_time=self.context_switches * self.switch_cost,
            end_time=max(p.finish for p in self.pcbs),
            timeline=self.timeline,
            events=self.events,
            policy_obj=self.policy,
        )

    # ------------------------------------------------------------- transitions
    def _start_burst(self, pcb: PCB) -> None:
        pcb.remaining = pcb.spec.bursts[pcb.burst_index]
        pcb.burst_done = 0.0
        self._make_ready(pcb)

    def _make_ready(self, pcb: PCB) -> None:
        pcb.ready_since = self.now
        self.ready.append(pcb)
        self.policy.on_ready(pcb, self.now)
        running = self.running
        if running is not None and self.policy.preemptive:
            ran = max(0.0, self.now - self._run_start)
            if self.policy.should_preempt(running, ran, pcb, self.now):
                self._stop_running(preempted=True)

    def _dispatch(self) -> None:
        pcb = self.policy.select(self.ready, self.now)
        self.ready.remove(pcb)
        cost = 0.0
        if pcb is not self._last_run:      # a different process: pay for the switch
            cost = self.switch_cost
            self.context_switches += 1
        self._last_run = pcb
        quantum = self.policy.time_slice(pcb, self.now)
        length = min(max(quantum, EPS), pcb.remaining)
        self.running = pcb
        self._run_start = self.now + cost
        self._token += 1
        self._push(self._run_start + length, SLICE_END, pcb, self._token)

    def _stop_running(self, preempted: bool) -> None:
        pcb = self.running
        ran = max(0.0, self.now - self._run_start)   # 0 if stopped during the switch
        pcb.remaining -= ran
        pcb.burst_done += ran
        self.busy_time += ran
        if ran > 0:
            if pcb.first_run is None:
                pcb.first_run = self._run_start
            self.timeline.append((self._run_start, self.now, pcb.pid))
        self.running = None
        self._token += 1

        if pcb.remaining <= EPS:
            self._complete_burst(pcb)
        elif preempted:
            self.policy.on_preempt(pcb, ran, self.now)
            self._make_ready(pcb)
        else:
            self.policy.on_quantum_expired(pcb, ran, self.now)
            self._make_ready(pcb)

    def _complete_burst(self, pcb: PCB) -> None:
        length = pcb.spec.bursts[pcb.burst_index]
        pcb.history.append(length)
        pcb.remaining = 0.0
        self.policy.on_burst_complete(pcb, length, self.now)
        pcb.burst_index += 1
        if pcb.burst_index < len(pcb.spec.bursts):
            self._push(self.now + pcb.spec.ios[pcb.burst_index - 1], IO_DONE, pcb)
        else:
            pcb.finish = self.now
