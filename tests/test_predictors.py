import pytest

from scheduler.engine import PCB
from scheduler.features import FEATURE_NAMES, ema_estimate, extract_features
from scheduler.predictor import MIN_PREDICTION, BurstPredictor, EMAPredictor
from scheduler.workload import ProcessSpec


def test_ema_textbook_values():
    # alpha 0.5, tau0 10, bursts 6, 4, 6  ->  8, 6, 6
    assert ema_estimate([6], tau0=10) == pytest.approx(8)
    assert ema_estimate([6, 4], tau0=10) == pytest.approx(6)
    assert ema_estimate([6, 4, 6], tau0=10) == pytest.approx(6)


def test_ema_lags_after_a_phase_change():
    bursts = [2, 2, 2, 2, 60, 60, 60]
    guesses = [ema_estimate(bursts[:k], tau0=2) for k in range(5, 8)]
    assert guesses == pytest.approx([31, 45.5, 52.75])


def test_features_never_use_future_bursts():
    # Same past, different future: the features for burst 3 must be identical.
    a = ProcessSpec(1, 0, "phase", (2, 3, 4, 100, 100), (30, 30, 30, 5), ("io",) * 5)
    b = ProcessSpec(2, 0, "phase", (2, 3, 4, 1, 1), (30, 30, 30, 9), ("io",) * 5)
    assert extract_features(a.bursts[:3], a.ios[:3]) == extract_features(b.bursts[:3], b.ios[:3])


def test_feature_vector_layout():
    x = extract_features([1.0, 3.0], [10.0])
    assert len(x) == len(FEATURE_NAMES) == 12
    named = dict(zip(FEATURE_NAMES, x))
    assert named["last_1"] == 3.0 and named["last_2"] == 1.0 and named["last_3"] == 0.0
    assert named["mean_burst"] == 2.0 and named["std_burst"] == 1.0
    assert named["last_change"] == 2.0 and named["bursts_done"] == 2.0


def test_negative_predictions_are_clamped():
    class Broken(BurstPredictor):
        def _predict(self, pcb):
            return -5.0

    pcb = PCB(ProcessSpec(1, 0, "cpu", (1.0,), (), ("cpu",)))
    assert Broken().predict(pcb) == MIN_PREDICTION


def test_prediction_error_is_logged():
    predictor = EMAPredictor(tau0=10)
    pcb = PCB(ProcessSpec(1, 0, "cpu", (4.0,), (), ("cpu",)))
    pcb.estimate = predictor.predict(pcb)
    predictor.observe(pcb, 4.0)
    assert predictor.stats()["pred_mae"] == pytest.approx(6.0)
