"""Turn the raw results into tables, hypothesis verdicts and figures.

    python analyse.py

Reads results/*.csv (written by run_experiments.py). Writes results/REPORT.md,
results/summary_means.csv and figures/*.png.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scheduler.configs import ABLATIONS, ADAPTIVE_DEFAULTS, DESCRIPTIONS, MAIN_CONFIGS  # noqa: E402
from scheduler.workload import PROFILES, SHIFT_KINDS, SHIFT_SEGMENT_MS  # noqa: E402

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"
FIG = ROOT / "figures"
OURS, SJF, SRTF, ORACLE = "Adaptive-ML", "SJF-EMA", "SRTF-EMA", "Oracle"

# Colours: our scheduler is always blue, the main baseline always orange,
# everything else muted so the comparison stands out.
BLUE, BLUE_LIGHT, ORANGE, TEAL = "#2a78d6", "#86b6ef", "#eb6834", "#1baf7a"
GRAY, GRAY_DARK, INK, INK_SOFT, GRID = "#c9c7c0", "#6f6d66", "#0b0b0b", "#52514e", "#e8e7e2"
POLICY_COLOURS = {OURS: BLUE, "Adaptive-EMA": BLUE_LIGHT, SJF: ORANGE, ORACLE: GRAY_DARK}

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.edgecolor": GRID, "axes.labelcolor": INK_SOFT, "text.color": INK,
    "xtick.color": INK_SOFT, "ytick.color": INK_SOFT,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "legend.frameon": False,
})


# ------------------------------------------------------------------ helpers
def md_table(header, rows) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def ms(x) -> str:
    return f"{x:,.0f}" if abs(x) >= 100 else f"{x:,.1f}"


def pct(x) -> str:
    return f"{x:+.1f}%"


def per_seed(df, workload, metric):
    """seed x policy table of one metric on one workload."""
    return df[df.workload == workload].pivot(index="seed", columns="policy", values=metric)


def verdict(flags) -> str:
    flags = list(flags)
    if all(flags):
        return "**Supported**"
    return "**Partly supported**" if any(flags) else "**Not supported**"


def save(fig, name):
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def title_for(w):
    return f"{w} · {PROFILES[w].description.split(' (')[0]}"


# ------------------------------------------------------------------ figures
def fig_avg_wait(means, stds):
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.6), sharey=True)
    y = np.arange(len(MAIN_CONFIGS))[::-1]
    for ax, w in zip(axes.flat, PROFILES):
        vals = [means.loc[(w, p), "avg_wait"] for p in MAIN_CONFIGS]
        errs = [stds.loc[(w, p), "avg_wait"] for p in MAIN_CONFIGS]
        cols = [POLICY_COLOURS.get(p, GRAY) for p in MAIN_CONFIGS]
        ax.barh(y, vals, height=0.72, color=cols, xerr=errs,
                error_kw={"elinewidth": 0.8, "ecolor": INK_SOFT, "capsize": 0})
        for p in (SJF, OURS):
            i = MAIN_CONFIGS.index(p)
            ax.text(vals[i] + errs[i] + max(vals) * 0.02, y[i], ms(vals[i]), va="center",
                    fontsize=8.5, color=INK)
        ax.set_title(title_for(w), loc="left")
        ax.set_xlim(0, max(v + e for v, e in zip(vals, errs)) * 1.22)
        ax.grid(axis="y", visible=False)
        ax.set_yticks(y, MAIN_CONFIGS)
    for ax in axes[1]:
        ax.set_xlabel("average waiting time per process (ms)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (BLUE, BLUE_LIGHT, ORANGE, GRAY_DARK, GRAY)]
    fig.legend(handles, ["Adaptive-ML (ours)", "Adaptive-EMA (ours, classical predictor)",
                         "SJF-EMA (main baseline)", "Oracle (best possible case)", "other baselines"],
               loc="upper center", ncol=5, bbox_to_anchor=(0.5, 1.03), fontsize=9)
    fig.suptitle("Average waiting time, mean of 10 seeds (bars) ± 1 standard deviation (lines)",
                 y=1.07, fontsize=12, fontweight="bold")
    fig.tight_layout()
    save(fig, "fig1_avg_wait.png")


def fig_switch_vs_response(means, workload="W4"):
    fig, ax = plt.subplots(figsize=(8, 5.2))
    rr = ["RR-2", "RR-5", "RR-10", "RR-20"]
    ax.plot([means.loc[(workload, p), "context_switches"] for p in rr],
            [means.loc[(workload, p), "avg_response"] for p in rr],
            color=GRAY, lw=2, zorder=1)
    offsets = {OURS: (9, 5), "Adaptive-EMA": (9, -13), SJF: (-8, 6), "RR-20": (8, 2)}
    for p in MAIN_CONFIGS:
        x, yv = means.loc[(workload, p), "context_switches"], means.loc[(workload, p), "avg_response"]
        colour = POLICY_COLOURS.get(p, GRAY_DARK if p in rr else GRAY)
        size = 120 if p == OURS else 60
        ax.scatter(x, yv, s=size, color=colour, edgecolor="white", linewidth=1.5, zorder=3)
        dx, dy = offsets.get(p, (7, 4))
        ax.annotate(p, (x, yv), xytext=(dx, dy), textcoords="offset points", fontsize=9,
                    ha="right" if dx < 0 else "left",
                    color=INK if p in (OURS, SJF) else INK_SOFT,
                    fontweight="bold" if p == OURS else "normal")
    ax.set_yscale("log")
    ax.set_yticks([2, 5, 10, 20, 50, 100, 200], ["2", "5", "10", "20", "50", "100", "200"])
    ax.set_xlabel("context switches per run (fewer is better)")
    ax.set_ylabel("average response time, ms (log scale, lower is better)")
    ax.set_title(f"{title_for(workload)}: the Round Robin trade-off (grey line) and where we land",
                 loc="left")
    save(fig, "fig2_switches_vs_response.png")


def fig_worst_wait(means):
    ws = list(PROFILES)
    x = np.arange(len(ws))
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for offset, p, colour in ((-0.19, SRTF, TEAL), (0.19, OURS, BLUE)):
        ratio = [means.loc[(w, p), "max_wait"] / means.loc[(w, SJF), "max_wait"] for w in ws]
        bars = ax.bar(x + offset, ratio, width=0.36, color=colour, label=p)
        for b, r in zip(bars, ratio):
            ax.text(b.get_x() + b.get_width() / 2, r + 0.02, f"{r:.2f}", ha="center",
                    fontsize=8.5, color=INK)
    ax.axhline(1.0, color=ORANGE, lw=2, ls="--", label="SJF-EMA (= 1.0)")
    ax.set_xticks(x, ws)
    ax.set_ylabel("worst-case wait ÷ SJF-EMA's worst-case wait")
    ax.set_title("Worst-case waiting time relative to SJF-EMA (below 1 = better)", loc="left")
    ax.legend(loc="upper right")
    ax.grid(axis="x", visible=False)
    save(fig, "fig3_worst_case_wait.png")


def fig_quantum_trace(trace):
    t = trace[trace.policy == OURS]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    seg = SHIFT_SEGMENT_MS / 1000
    names = {"interactive": "interactive processes arrive", "cpu": "CPU-bound processes arrive",
             "io": "I/O-bound processes arrive"}
    for i, kind in enumerate(SHIFT_KINDS):
        if i % 2 == 0:
            ax.axvspan(i * seg, (i + 1) * seg, color="#f4f3ef", zorder=0)
        ax.text((i + 0.5) * seg, 160, names[kind], ha="center", fontsize=9, color=INK_SOFT)
    for q in (2, 5, 10, 20):
        ax.axhline(q, color=GRAY, lw=1, ls=":", zorder=1)
        ax.text(t.time_ms.max() / 1000 * 1.005, q, f"RR-{q}", va="center", fontsize=8.5,
                color=INK_SOFT)
    ax.plot(t.time_ms / 1000, t.quantum, color=BLUE, lw=2, zorder=3,
            label="Adaptive-ML time quantum")
    ax.set_yscale("log")
    ax.set_ylim(1, 220)
    ax.set_yticks([1, 2, 5, 10, 20, 50, 100], ["1", "2", "5", "10", "20", "50", "100"])
    ax.set_xlabel("simulated time (s)")
    ax.set_ylabel("time quantum (ms, log scale)")
    ax.set_title("The quantum follows the workload; fixed Round Robin quanta (dotted) cannot",
                 loc="left")
    ax.grid(axis="x", visible=False)
    save(fig, "fig4_quantum_over_time.png")


def fig_prediction_example(pred):
    # Pick the process where the classical estimate lags the most.
    lag = pred.assign(err=(pred.actual - pred.ema).abs()).groupby("pid").err.mean()
    p = pred[pred.pid == lag.idxmax()]
    change = int(np.argmax(np.diff(p.actual.values) > 20)) + 1
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(p.burst, p.actual, color=GRAY, width=0.7, label="actual burst")
    ax.plot(p.burst, p.ema, color=ORANGE, lw=2, marker="o", ms=5, label="exponential averaging")
    ax.plot(p.burst, p.ml, color=BLUE, lw=2, marker="o", ms=5, label="learned model (ours)")
    ax.axvline(change - 0.5, color=INK_SOFT, lw=1, ls=":")
    ax.text(change - 0.4, p.actual.max() * 1.02, "process switches from I/O-bound to CPU-bound",
            fontsize=9, color=INK_SOFT)
    ax.set_xlabel("burst number")
    ax.set_ylabel("burst length (ms)")
    ax.set_title("One phase-changing process: predictions made before each burst", loc="left")
    ax.legend(loc="upper left")
    ax.grid(axis="x", visible=False)
    save(fig, "fig5_prediction_example.png")


def fig_ablation(abl, means):
    variants = list(ABLATIONS)
    fig, axes = plt.subplots(2, 2, figsize=(12, 6.4), sharey=True)
    y = np.arange(len(variants))[::-1]
    for row, w in enumerate(("W4", "W5")):
        m = abl[abl.workload == w].groupby("variant")[["avg_wait", "max_wait"]].mean()
        for col, (metric, label) in enumerate((("avg_wait", "average wait (ms)"),
                                               ("max_wait", "worst-case wait (ms)"))):
            ax = axes[row, col]
            vals = [m.loc[v, metric] for v in variants]
            ax.barh(y, vals, height=0.7, color=[BLUE if v == "Full" else GRAY for v in variants])
            for yi, v, name in zip(y, vals, variants):
                ax.text(v - max(vals) * 0.015, yi, ms(v), va="center", ha="right", fontsize=8.5,
                        color="white" if name == "Full" else INK)
            ref = means.loc[(w, SJF), metric]
            ax.axvline(ref, color=ORANGE, lw=2, ls="--", zorder=0.8)   # behind the bars
            ax.text(ref, len(variants) - 0.35, " SJF-EMA", color=INK_SOFT, fontsize=8.5)
            ax.set_yticks(y, variants)
            ax.set_xlim(0, max(max(vals), ref) * 1.18)
            ax.set_title(f"{title_for(w)}: {label}", loc="left")
            ax.grid(axis="y", visible=False)
    fig.suptitle("Ablation: switch off one part of Adaptive-ML at a time (mean of 10 seeds)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    save(fig, "fig6_ablation.png")


def fig_sweeps(sweeps):
    params = [("beta", "ageing weight β"), ("p", "percentile p"), ("epoch", "epoch length E (decisions)")]
    fig, axes = plt.subplots(2, 3, figsize=(13, 6.4))
    for col, (param, label) in enumerate(params):
        g = sweeps[sweeps.param == param].groupby("value")[["avg_wait", "max_wait"]]
        mean, std = g.mean(), g.std()
        xs = np.arange(len(mean))
        for row, metric in enumerate(("avg_wait", "max_wait")):
            ax = axes[row, col]
            ax.errorbar(xs, mean[metric], yerr=std[metric], color=BLUE, lw=2, marker="o",
                        ms=6, elinewidth=0.8, ecolor=INK_SOFT)
            default = ADAPTIVE_DEFAULTS[param]
            if default in mean.index:
                i = list(mean.index).index(default)
                ax.scatter(xs[i], mean[metric].iloc[i], s=140, facecolor="none",
                           edgecolor=INK, lw=1.5, zorder=4)
            ax.set_xticks(xs, [f"{v:g}" for v in mean.index])
            ax.set_xlabel(label)
            ax.set_ylabel("average wait (ms)" if metric == "avg_wait" else "worst-case wait (ms)")
            ax.grid(axis="x", visible=False)
    fig.suptitle("Parameter sweeps on W4 (mean ± 1 sd over 10 seeds; circled = default)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    save(fig, "fig7_parameter_sweeps.png")


def fig_prediction_error(means):
    ws = list(PROFILES)
    ema = [means.loc[(w, "Adaptive-EMA"), "pred_mae"] for w in ws]
    ml = [means.loc[(w, OURS), "pred_mae"] for w in ws]
    cut = [100 * (1 - m / e) for m, e in zip(ml, ema)]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    bars = ax.bar(ws, cut, width=0.6, color=BLUE)
    for b, c, e, m in zip(bars, cut, ema, ml):
        ax.text(b.get_x() + b.get_width() / 2, c + 0.6, f"{c:.0f}%", ha="center", fontsize=10,
                fontweight="bold")
        ax.text(b.get_x() + b.get_width() / 2, -2.2, f"{e:.1f} → {m:.1f} ms", ha="center",
                fontsize=8.5, color=INK_SOFT)
    ax.axhline(0, color=INK_SOFT, lw=1)
    ax.set_ylim(-4, max(cut) * 1.25)
    ax.set_ylabel("reduction in prediction error (MAE), %")
    ax.set_title("How much the learned model cuts prediction error vs exponential averaging",
                 loc="left")
    ax.grid(axis="x", visible=False)
    save(fig, "fig8_prediction_error.png")


# ------------------------------------------------------------------- report
def main():
    main_df = pd.read_csv(RES / "main_results.csv")
    abl = pd.read_csv(RES / "ablation.csv")
    info = json.loads((RES / "run_info.json").read_text())
    model = json.loads((RES / "model_report.json").read_text())
    sweeps = pd.read_csv(RES / "sweeps.csv") if (RES / "sweeps.csv").exists() else None
    switch = pd.read_csv(RES / "switch_cost.csv") if (RES / "switch_cost.csv").exists() else None
    tuning = pd.read_csv(RES / "beta_tuning.csv") if (RES / "beta_tuning.csv").exists() else None

    grouped = main_df.groupby(["workload", "policy"])
    means, stds = grouped.mean(numeric_only=True), grouped.std(numeric_only=True)
    means.drop(columns="seed").to_csv(RES / "summary_means.csv")
    n_seeds = main_df.seed.nunique()
    W = list(PROFILES)
    out = []

    out.append("# Results report\n")
    out.append(f"Generated by `analyse.py` from {len(main_df)} main runs "
               f"({len(W)} workloads × {len(MAIN_CONFIGS)} schedulers × {n_seeds} seeds, "
               f"{info['processes_per_run']} processes per run), {len(abl)} ablation runs"
               + (f", {len(sweeps)} sweep runs and {len(switch)} switch-cost runs" if sweeps is not None else "")
               + ". Every scheduler sees the same workload instances, so comparisons are paired by seed. "
               "All times are in milliseconds. Context-switch cost is 0.1 ms unless stated.\n")

    # Headline
    gap = {w: 100 * (means.loc[(w, SJF), "avg_wait"] - means.loc[(w, OURS), "avg_wait"])
           / (means.loc[(w, SJF), "avg_wait"] - means.loc[(w, ORACLE), "avg_wait"]) for w in W}
    w4 = lambda p, m: means.loc[("W4", p), m]  # noqa: E731
    out.append("## Headline (W4, mixed workload)\n")
    out.append(f"- Average waiting time: **{ms(w4(OURS, 'avg_wait'))} ms** for Adaptive-ML vs "
               f"{ms(w4(SJF, 'avg_wait'))} ms for SJF with exponential averaging "
               f"(**{pct(100 * (w4(OURS, 'avg_wait') / w4(SJF, 'avg_wait') - 1))}**), "
               f"and {ms(w4(ORACLE, 'avg_wait'))} ms for the oracle.")
    out.append(f"- That closes **{gap['W4']:.0f}%** of the gap between SJF-EMA and the oracle.")
    out.append(f"- Worst-case wait: {ms(w4(OURS, 'max_wait'))} ms vs {ms(w4(SJF, 'max_wait'))} ms for SJF-EMA "
               f"({pct(100 * (w4(OURS, 'max_wait') / w4(SJF, 'max_wait') - 1))}).")
    out.append(f"- Context switches: {w4(OURS, 'context_switches'):,.0f} vs {w4('RR-5', 'context_switches'):,.0f} "
               f"for RR-5 ({pct(100 * (w4(OURS, 'context_switches') / w4('RR-5', 'context_switches') - 1))}), "
               f"with average response time {ms(w4(OURS, 'avg_response'))} ms "
               f"(RR-5: {ms(w4('RR-5', 'avg_response'))}, RR-20: {ms(w4('RR-20', 'avg_response'))}).\n")

    # Table: average wait
    out.append("## 1. Average waiting time (mean ± sd over seeds)\n")
    rows = [[f"{p}"] + [f"{ms(means.loc[(w, p), 'avg_wait'])} ± {ms(stds.loc[(w, p), 'avg_wait'])}"
                         for w in W] for p in MAIN_CONFIGS]
    out.append(md_table(["Scheduler"] + W, rows))
    out.append("\nWorkloads: " + "; ".join(f"**{w}** {PROFILES[w].description}" for w in W) + ".\n")
    out.append("![Average waiting time](../figures/fig1_avg_wait.png)\n")

    # Table: ours vs SJF per workload
    out.append("## 2. Adaptive-ML against the main baseline (SJF-EMA), per workload\n")
    rows = []
    for w in W:
        s = per_seed(main_df, w, "avg_wait")
        d = s[SJF] - s[OURS]
        rows.append([w, pct(100 * (means.loc[(w, OURS), "avg_wait"] / means.loc[(w, SJF), "avg_wait"] - 1)),
                     f"{(d > 0).sum()}/{len(d)}", f"{gap[w]:.0f}%",
                     pct(100 * (means.loc[(w, OURS), "max_wait"] / means.loc[(w, SJF), "max_wait"] - 1)),
                     pct(100 * (means.loc[(w, OURS), "context_switches"] / means.loc[(w, SJF), "context_switches"] - 1)),
                     f"{means.loc[(w, OURS), 'mean_quantum']:.1f}"])
    out.append(md_table(["Workload", "Avg wait change", "Seeds where better", "Oracle gap closed",
                         "Worst wait change", "Switches change", "Mean quantum (ms)"], rows))
    out.append("\nNegative change = Adaptive-ML is lower (better). Oracle gap closed = "
               "(SJF − ours) / (SJF − oracle). A negative value means Adaptive-ML was worse than SJF-EMA.\n")

    # Full metrics on W4
    out.append("## 3. All metrics on W4 (mean over seeds)\n")
    cols = [("avg_wait", "Avg wait"), ("max_wait", "Worst wait"), ("avg_turnaround", "Turnaround"),
            ("avg_response", "Response"), ("context_switches", "Switches"), ("cpu_util", "CPU util"),
            ("throughput", "Throughput /s"), ("fairness", "Jain fairness"), ("starved", "Starved"),
            ("pred_mae", "Pred. MAE")]
    rows = []
    for p in MAIN_CONFIGS:
        r = means.loc[("W4", p)]
        cells = []
        for c, _ in cols:
            v = r[c]
            if pd.isna(v):
                cells.append("–")
            elif c in ("cpu_util", "fairness"):
                cells.append(f"{v:.3f}")
            elif c in ("throughput", "starved", "pred_mae"):
                cells.append(f"{v:.2f}")
            else:
                cells.append(ms(v))
        rows.append([p] + cells)
    out.append(md_table(["Scheduler"] + [n for _, n in cols], rows))
    out.append("\nStarved = processes whose waiting time exceeded 5× the cross-scheduler mean wait for "
               "that workload instance. Jain fairness is computed on each process's progress rate "
               "((CPU + I/O time) / turnaround). (Service received ÷ demanded, as first planned, is "
               "always 1 here because every process eventually finishes.)\n")
    out.append("![Switches vs response](../figures/fig2_switches_vs_response.png)\n")

    # Hypotheses
    out.append("## 4. Hypotheses (stated in Review 1, before any experiment)\n")
    hyp = []

    # H1
    details = []
    flags = []
    for w in ("W4", "W5", "W6"):
        s = per_seed(main_df, w, "avg_wait")
        d = s[SJF] - s[OURS]
        ok = d.mean() > d.std(ddof=1)
        flags.append(ok)
        details.append(f"{w}: {pct(-100 * d.mean() / s[SJF].mean())}, mean improvement "
                       f"{ms(d.mean())} vs sd {ms(d.std(ddof=1))} → {'passes' if ok else 'fails'}")
    imp = {w: 100 * (1 - means.loc[(w, OURS), 'avg_wait'] / means.loc[(w, SJF), 'avg_wait']) for w in ("W4", "W5", "W6")}
    largest = max(imp, key=imp.get)
    hyp.append(["H1", "Lower average wait than SJF-EMA on W4, W5, W6 (largest on W5). "
                "Rule: mean paired improvement > 1 sd across seeds.", verdict(flags),
                "; ".join(details) + f". Largest improvement on {largest}"
                + (", as predicted." if largest == "W5" else ", not on W5 as predicted.")])

    # H2
    holds = []
    for w in W:
        sw, rr5 = means.loc[(w, OURS), "context_switches"], means.loc[(w, "RR-5"), "context_switches"]
        holds.append((w, sw < 0.5 * rr5 and means.loc[(w, OURS), "avg_response"] < means.loc[(w, "RR-20"), "avg_response"]))
    w4_ok = dict(holds)["W4"]
    hyp.append(["H2", "Far fewer context switches than small-quantum RR, without response time "
                "collapsing. Rule: < half of RR-5's switches and lower response time than RR-20.",
                "**Supported**" if w4_ok else "**Not supported**",
                f"Holds on W4: {'yes' if w4_ok else 'no'}. Holds on: "
                + (", ".join(w for w, ok in holds if ok) or "none") + "."])

    # H3
    flags, det = [], []
    for w in W:
        ok = (means.loc[(w, OURS), "max_wait"] < means.loc[(w, SJF), "max_wait"]
              and means.loc[(w, OURS), "max_wait"] < means.loc[(w, SRTF), "max_wait"])
        flags.append(ok)
        det.append(f"{w} {'✓' if ok else '✗'}")
    hyp.append(["H3", "Lower worst-case wait than SJF-EMA and SRTF-EMA (thanks to ageing).",
                verdict(flags), ", ".join(det) + "."])

    # H4
    flags, det = [], []
    for w in ("W1", "W2"):
        diff = 100 * (means.loc[(w, OURS), "avg_wait"] / means.loc[(w, SJF), "avg_wait"] - 1)
        flags.append(abs(diff) <= 10)
        det.append(f"{w}: {pct(diff)}")
    hyp.append(["H4", "About equal to SJF-EMA on uniform workloads W1, W2 (within ±10%).",
                verdict(flags), ", ".join(det) + "."])

    # H5
    s_all = main_df.pivot_table(index=["workload", "seed"], columns="policy", values="avg_wait")
    beat = (s_all[OURS] < s_all[ORACLE]).sum()
    others = [p for p in MAIN_CONFIGS if p != ORACLE and (means.xs(p, level="policy")["avg_wait"]
              < means.xs(ORACLE, level="policy")["avg_wait"]).any()]
    where = {p: [w for w in W if means.loc[(w, p), "avg_wait"] < means.loc[(w, ORACLE), "avg_wait"]] for p in others}
    hyp.append(["H5", "Never beats the oracle on average wait.",
                "**Supported**" if beat == 0 else "**Not supported**",
                f"Adaptive-ML beat the oracle in {beat} of {len(s_all)} workload instances. "
                + ("Note: on average, " + "; ".join(f"{p} beat it on {', '.join(ws)}" for p, ws in where.items())
                   + ". The oracle is SRTF on true *burst* lengths: optimal for single-burst jobs, but not a "
                   "bound when processes have many bursts (see notes)." if where else "")])

    # H6
    flags, det = [], []
    for w in W:
        e, m = means.loc[(w, "Adaptive-EMA"), "pred_mae"], means.loc[(w, OURS), "pred_mae"]
        flags.append(m < e)
        det.append(f"{w} {e:.1f}→{m:.1f}")
    w5_ok = means.loc[("W5", OURS), "pred_mae"] < means.loc[("W5", "Adaptive-EMA"), "pred_mae"]
    hyp.append(["H6", "Lower prediction MAE than exponential averaging on W5.",
                "**Supported**" if w5_ok else "**Not supported**",
                "MAE in ms, EMA→ML: " + ", ".join(det) + f" (lower on {sum(flags)}/6 workloads)."])

    # H7
    flags, det = [], []
    for w in ("W4", "W5"):
        a = abl[abl.workload == w].groupby("variant")[["avg_wait", "max_wait", "starved"]].mean()
        lower_avg = a.loc["No ageing", "avg_wait"] < a.loc["Full", "avg_wait"]
        higher_max = a.loc["No ageing", "max_wait"] > a.loc["Full", "max_wait"]
        flags.append(lower_avg and higher_max)
        det.append(f"{w}: avg {ms(a.loc['Full', 'avg_wait'])}→{ms(a.loc['No ageing', 'avg_wait'])}, "
                   f"worst {ms(a.loc['Full', 'max_wait'])}→{ms(a.loc['No ageing', 'max_wait'])}, "
                   f"starved {a.loc['Full', 'starved']:.1f}→{a.loc['No ageing', 'starved']:.1f}")
    hyp.append(["H7", "Removing ageing slightly lowers the average but raises worst-case wait and starvation.",
                verdict(flags), "; ".join(det) + " (Full→No ageing)."])

    out.append(md_table(["#", "Hypothesis", "Verdict", "Evidence"], hyp))
    out.append("\n![Worst-case wait](../figures/fig3_worst_case_wait.png)\n")

    # Prediction
    out.append("## 5. Prediction accuracy\n")
    out.append(f"Offline training: {model['dataset']['processes']} processes "
               f"({model['dataset']['bursts']:,} bursts) from seeds never used in the experiments, "
               f"split **by process** ({model['dataset']['train_processes']} train / "
               f"{model['dataset']['test_processes']} test).\n")
    rows = [[n, f"{r['mae']:.2f}", f"{r['rmse']:.2f}", f"{r['mae_cpu']:.1f}", f"{r['mae_io']:.2f}",
             f"{r['mae_interactive']:.2f}", f"{r['mae_phase']:.1f}", f"{r['latency_ms']:.3f}"]
            for n, r in model["regressors"].items()]
    out.append(md_table(["Model", "MAE", "RMSE", "MAE cpu", "MAE io", "MAE interactive",
                         "MAE phase", "Latency (ms)"], rows))
    out.append(f"\nChosen: **{model['chosen_regressor']}** (rule: lowest MAE within a 1 ms latency budget; "
               f"Ridge preferred if within 5%). Beats exponential averaging on held-out data: "
               f"**{'yes' if model['beats_ema'] else 'no'}**. Classifier: "
               + ", ".join(f"{n} macro-F1 {r['macro_f1']:.3f}" for n, r in model["classifiers"].items())
               + f"; chosen **{model['chosen_classifier']}**.\n")
    out.append("![Prediction error](../figures/fig8_prediction_error.png)\n")
    out.append("![Prediction example](../figures/fig5_prediction_example.png)\n")
    out.append("![Quantum over time](../figures/fig4_quantum_over_time.png)\n")

    # Ablation
    out.append("## 6. Ablation (Adaptive-ML with one part switched off)\n")
    a = abl.groupby(["workload", "variant"])[["avg_wait", "max_wait", "avg_response",
                                               "context_switches", "starved"]].mean()
    rows = []
    for w in ("W4", "W5"):
        for v in ABLATIONS:
            r = a.loc[(w, v)]
            rows.append([w, v, ms(r.avg_wait), ms(r.max_wait), ms(r.avg_response),
                         f"{r.context_switches:,.0f}", f"{r.starved:.1f}"])
        rows.append([w, "*SJF-EMA (reference)*", ms(means.loc[(w, SJF), "avg_wait"]),
                     ms(means.loc[(w, SJF), "max_wait"]), ms(means.loc[(w, SJF), "avg_response"]),
                     f"{means.loc[(w, SJF), 'context_switches']:,.0f}", f"{means.loc[(w, SJF), 'starved']:.1f}"])
    out.append(md_table(["Workload", "Variant", "Avg wait", "Worst wait", "Response", "Switches",
                         "Starved"], rows))
    out.append("\n*Prediction only* = ML-predicted SJF (no ageing, no quantum). Comparing it with "
               "SJF-EMA isolates the value of the better prediction alone.\n")
    out.append("![Ablation](../figures/fig6_ablation.png)\n")

    # Sweeps
    if sweeps is not None:
        out.append("## 7. Parameter sweeps on W4\n")
        rows = []
        for param in ("beta", "p", "epoch"):
            g = sweeps[sweeps.param == param].groupby("value")[["avg_wait", "max_wait", "context_switches"]].mean()
            for v, r in g.iterrows():
                mark = " (default)" if v == ADAPTIVE_DEFAULTS[param] else ""
                rows.append([param, f"{v:g}{mark}", ms(r.avg_wait), ms(r.max_wait), f"{r.context_switches:,.0f}"])
        out.append(md_table(["Parameter", "Value", "Avg wait", "Worst wait", "Switches"], rows))
        out.append("\n![Sweeps](../figures/fig7_parameter_sweeps.png)\n")
        out.append("### Context-switch cost sensitivity (W4)\n")
        s = switch.groupby(["policy", "switch_cost"]).avg_wait.mean().unstack()
        rows = [[p] + [ms(s.loc[p, c]) for c in s.columns] for p in s.index]
        out.append(md_table(["Scheduler"] + [f"avg wait @ {c:g} ms switch" for c in s.columns], rows) + "\n")

    if tuning is not None:
        out.append("## 8. How β was chosen\n")
        out.append("β had no default in the plan. It was chosen by `tune_beta.py` on seeds "
                   f"{sorted(int(x) for x in tuning.seed.unique())}, which the experiments above never use. "
                   "Score per workload = (avg wait ÷ SJF avg wait + worst wait ÷ SJF worst wait) / 2; "
                   "lowest mean score wins.\n")
        t = tuning.groupby(["beta", "workload"]).score.mean().unstack()
        t["mean"] = t.mean(axis=1)
        rows = [[f"{b:g}"] + [f"{v:.3f}" for v in r] for b, r in t.iterrows()]
        out.append(md_table(["β"] + list(t.columns), rows))
        out.append(f"\nChosen β = **{t['mean'].idxmin():g}**.\n")

    out.append("## Scheduler configurations\n")
    out.append(md_table(["Name", "Description"], [[p, DESCRIPTIONS[p]] for p in MAIN_CONFIGS]))
    out.append("")
    (RES / "REPORT.md").write_text("\n".join(out))

    fig_avg_wait(means, stds)
    fig_switch_vs_response(means)
    fig_worst_wait(means)
    fig_quantum_trace(pd.read_csv(RES / "quantum_trace.csv"))
    fig_prediction_example(pd.read_csv(RES / "prediction_trace.csv"))
    fig_ablation(abl, means)
    if sweeps is not None:
        fig_sweeps(sweeps)
    fig_prediction_error(means)

    print("\n".join(out[:8]))
    print("\nHypotheses:")
    for h in hyp:
        print(f"  {h[0]}: {h[2].strip('*')}")
    print(f"\nWrote results/REPORT.md, results/summary_means.csv and {len(list(FIG.glob('*.png')))} "
          "figures in figures/")


if __name__ == "__main__":
    main()
