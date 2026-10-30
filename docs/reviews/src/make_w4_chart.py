"""Draw docs/reviews/assets/w4_avg_wait.png (the W4 chart on slide 4) from results/main_results.csv.

    .venv/bin/python docs/reviews/src/make_w4_chart.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
LABELS = {"Adaptive-ML": "Adaptive-ML (ours)", "Oracle": "Oracle (true bursts)"}

means = pd.read_csv(ROOT / "results" / "main_results.csv").query("workload == 'W4'") \
    .groupby("policy")["avg_wait"].mean().sort_values(ascending=False)
names = [LABELS.get(p, p) for p in means.index]
vals = [round(v) for v in means.values]
cols = ["#2A78D6" if n.startswith("Adaptive-ML") else ("#6B7280" if n.startswith("Oracle") else "#C7D2DE") for n in names]
fig, ax = plt.subplots(figsize=(6.2, 4.2), dpi=220)
y = range(len(names))[::-1]
ax.barh(list(y), vals, color=cols, height=0.68)
for yi, v, n in zip(y, vals, names):
    ax.text(v + 40, yi, f"{v:,}", va="center", fontsize=9, color="#1F2937",
            fontweight="bold" if n.startswith("Adaptive-ML") else "normal")
ax.set_yticks(list(y), names, fontsize=9.5, color="#1F2937")
for lbl in ax.get_yticklabels():
    if lbl.get_text().startswith("Adaptive-ML"):
        lbl.set_fontweight("bold")
ax.set_xlim(0, 4600)
ax.xaxis.set_visible(False)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.tick_params(left=False)
ax.set_title("Average waiting time on W4 (ms, mean of 10 seeds)", fontsize=10.5, color="#1F2937", loc="left")
fig.tight_layout()
fig.savefig(ROOT / "docs" / "reviews" / "assets" / "w4_avg_wait.png", facecolor="white")
print(dict(zip(names, vals)))
