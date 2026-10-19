"""Adaptive CPU scheduling using predicted burst lengths.

A single-CPU discrete-event simulator, the classical scheduling policies, a
learned burst predictor, and an adaptive scheduler that uses the prediction to
order the ready queue and to size the time quantum.
"""

import os

# The simulator asks for one prediction at a time. Multi-threaded maths only
# adds overhead for a single row (3.7 ms vs 0.5 ms per prediction), so pin
# OpenMP to one thread. Must run before scikit-learn is imported.
os.environ.setdefault("OMP_NUM_THREADS", "1")
