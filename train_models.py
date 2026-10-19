"""Train and compare the burst predictor and the process classifier.

    python train_models.py

Training processes come from seeds (1000+) that the experiments never use.
The train/test split is by process, not by row, so no process has bursts in
both sets. The learned regressor is compared with exponential averaging on the
same held-out bursts. If it does not beat it, the script says so.
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")   # see scheduler/__init__.py

import json
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import f1_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from scheduler.features import FEATURE_NAMES, build_dataset
from scheduler.workload import CPU, INTERACTIVE, IO, PHASE, make_process

ROOT = Path(__file__).resolve().parent
TRAIN_SEEDS = range(1000, 1005)
PER_KIND = 100                 # processes of each kind per seed
LATENCY_BUDGET_MS = 1.0        # a prediction must take less than this
RIDGE_TOLERANCE = 0.05         # prefer Ridge if its MAE is within 5% of the best
ONLINE_BASE_ROWS = 10_000      # offline rows kept for the online refit
KINDS = (CPU, IO, INTERACTIVE, PHASE)


def training_processes():
    specs = []
    for seed in TRAIN_SEEDS:
        rng = np.random.default_rng([seed, 7])
        for kind in KINDS:
            specs += [make_process(rng, len(specs), kind) for _ in range(PER_KIND)]
    return specs


def latency_ms(model, X, repeats: int = 300) -> float:
    rows = X[:repeats]
    start = time.perf_counter()
    for i in range(repeats):
        model.predict(rows[i:i + 1])
    return 1000 * (time.perf_counter() - start) / repeats


def regressors():
    def ridge():
        return make_pipeline(StandardScaler(), Ridge(alpha=1.0))

    def boosting():
        return HistGradientBoostingRegressor(max_iter=200, early_stopping=False, random_state=0)

    return {
        "Ridge": (ridge, False),
        "Ridge (log target)": (ridge, True),
        "Gradient boosting": (boosting, False),
        "Gradient boosting (log target)": (boosting, True),
    }


def score(pred, y, kinds):
    row = {"mae": mean_absolute_error(y, pred),
           "rmse": float(np.sqrt(mean_squared_error(y, pred)))}
    for k in KINDS:
        mask = kinds == k
        row[f"mae_{k}"] = mean_absolute_error(y[mask], pred[mask])
    return row


def print_table(title, rows, cols):
    print(f"\n{title}")
    print(f"  {'model':32s}" + "".join(f"{c:>16s}" for c in cols))
    for name, r in rows.items():
        print(f"  {name:32s}" + "".join(f"{r[c]:16.3f}" for c in cols))


def main():
    specs = training_processes()
    X, y, labels, groups, kinds = build_dataset(specs)
    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=0)
                  .split(X, y, groups))
    print(f"Dataset: {len(specs)} processes, {len(y)} bursts, {len(FEATURE_NAMES)} features")
    print(f"Split by process: {len(set(groups[tr]))} train / {len(set(groups[te]))} test processes")

    # ---------------------------------------------------------------- regressor
    results = {"Exponential averaging": {**score(X[te, FEATURE_NAMES.index("ema_estimate")],
                                                 y[te], kinds[te]), "latency_ms": 0.0}}
    fitted = {}
    for name, (make, log_target) in regressors().items():
        model = make().fit(X[tr], np.log1p(y[tr]) if log_target else y[tr])
        pred = model.predict(X[te])
        pred = np.expm1(pred) if log_target else pred
        results[name] = {**score(np.maximum(pred, 0.1), y[te], kinds[te]),
                         "latency_ms": latency_ms(model, X[te])}
        fitted[name] = (make, log_target)

    cols = ["mae", "rmse", "mae_cpu", "mae_io", "mae_interactive", "mae_phase", "latency_ms"]
    print_table("Burst predictor, held-out processes (ms):", results, cols)

    allowed = [n for n in fitted if results[n]["latency_ms"] <= LATENCY_BUDGET_MS]
    best = min(allowed, key=lambda n: results[n]["mae"])
    best_ridge = min((n for n in allowed if n.startswith("Ridge")), key=lambda n: results[n]["mae"])
    chosen = best
    if results[best_ridge]["mae"] <= results[best]["mae"] * (1 + RIDGE_TOLERANCE):
        chosen = best_ridge
    ema_mae = results["Exponential averaging"]["mae"]
    beats_ema = results[chosen]["mae"] < ema_mae
    print(f"\nChosen regressor: {chosen}  (MAE {results[chosen]['mae']:.2f} ms vs "
          f"exponential averaging {ema_mae:.2f} ms, "
          f"{100 * (1 - results[chosen]['mae'] / ema_mae):.1f}% lower)")
    if not beats_ema:
        print("WARNING: the learned model does NOT beat exponential averaging. "
              "Report this as a finding; Adaptive-EMA is the honest choice.")

    # Refit the chosen model on all the data for use in the simulator.
    make, log_target = fitted[chosen]
    final = make().fit(X, np.log1p(y) if log_target else y)
    keep = np.random.default_rng(0).choice(len(y), size=min(ONLINE_BASE_ROWS, len(y)),
                                           replace=False)
    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump({"model": final, "name": chosen, "log_target": log_target,
                 "features": FEATURE_NAMES, "train_X": X[keep], "train_y": y[keep]},
                ROOT / "models" / "burst_model.joblib")

    # --------------------------------------------------------------- classifier
    classifiers = {
        "Logistic regression": lambda: make_pipeline(StandardScaler(),
                                                     LogisticRegression(max_iter=2000)),
        "Random forest": lambda: RandomForestClassifier(n_estimators=100, max_depth=12,
                                                        random_state=0),
    }
    cls_results = {}
    for name, make_cls in classifiers.items():
        model = make_cls().fit(X[tr], labels[tr])
        cls_results[name] = {
            "macro_f1": f1_score(labels[te], model.predict(X[te]), average="macro"),
            "latency_ms": latency_ms(model, X[te], repeats=100),
        }
    print_table("Process classifier, held-out processes:", cls_results, ["macro_f1", "latency_ms"])
    best_cls = max(cls_results, key=lambda n: cls_results[n]["macro_f1"])
    if cls_results["Logistic regression"]["macro_f1"] >= cls_results[best_cls]["macro_f1"] - 0.02:
        best_cls = "Logistic regression"   # simpler and faster when nearly as good
    print(f"\nChosen classifier: {best_cls}")
    joblib.dump({"model": classifiers[best_cls]().fit(X, labels), "name": best_cls},
                ROOT / "models" / "class_model.joblib")

    report = {"dataset": {"processes": len(specs), "bursts": int(len(y)),
                          "train_processes": int(len(set(groups[tr]))),
                          "test_processes": int(len(set(groups[te])))},
              "regressors": results, "chosen_regressor": chosen,
              "beats_ema": bool(beats_ema), "classifiers": cls_results,
              "chosen_classifier": best_cls}
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "model_report.json").write_text(json.dumps(report, indent=2))
    print("\nSaved models/burst_model.joblib, models/class_model.joblib, results/model_report.json")


if __name__ == "__main__":
    main()
