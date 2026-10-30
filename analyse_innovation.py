"""Tables, paired statistics and figures for the post-Review 3 additions.

    python analyse_innovation.py

Reads results/main_results.csv (read only) and results/innovation/*.csv.
Writes results/innovation/REPORT.md, results/innovation/stats.csv and
figures/innovation/*.png. Nothing in results/ or figures/ outside the
innovation folders is touched.

Statistics. All comparisons are paired by seed (every configuration ran on the
same workload instances). For each comparison:
  * change      = 100 * (mean(new) / mean(reference) - 1), in percent
  * 95% CI      = percentile bootstrap of that change, resampling seeds (10,000 draws)
  * p (Wilcoxon) = exact two-sided Wilcoxon signed-rank test on the per-seed pairs
  * p (Holm)    = Holm-corrected within the stated family of comparisons
  * wins        = seeds on which the new configuration has the lower value
With 10 seeds the smallest possible exact Wilcoxon p-value is 2/1024 = 0.002,
so families are kept small enough (at most 14 tests) for Holm to be able to
reach 0.05.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import wilcoxon  # noqa: E402

import analyse  # noqa: E402  (shared colours, plot style and table helpers)
from analyse import BLUE, BLUE_LIGHT, GRAY, GRAY_DARK, INK_SOFT, ORANGE, TEAL, md_table, ms  # noqa: E402
from scheduler.configs import DESCRIPTIONS, GUARD, INNOVATION_CONFIGS, PERSISTENT_BETA  # noqa: E402
from scheduler.workload import ALL_PROFILES, BAIT, generate_workload  # noqa: E402

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"
OUT = RES / "innovation"
FIG = ROOT / "figures" / "innovation"
OURS = "Adaptive-ML"
N_BOOT = 10_000
NEW_COLOURS = {"Adaptive-ML-G": TEAL, "Adaptive-ML-A": "#9b6bd6", "Adaptive-ML-GA": "#d6a21e"}


# ------------------------------------------------------------- statistics
def paired(ref, new, rng):
    ref, new = np.asarray(ref, float), np.asarray(new, float)
    change = 100 * (new.mean() / ref.mean() - 1)
    idx = rng.integers(0, len(ref), size=(N_BOOT, len(ref)))
    boot = 100 * (new[idx].mean(axis=1) / ref[idx].mean(axis=1) - 1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    diff = new - ref
    p = 1.0 if np.all(diff == 0) else float(wilcoxon(new, ref, method="exact").pvalue)
    return {"ref_mean": ref.mean(), "new_mean": new.mean(), "change_pct": change,
            "ci_lo": lo, "ci_hi": hi, "p_wilcoxon": p,
            "wins": int(np.sum(new < ref)), "n": len(ref)}


def holm(pvals):
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(p) - rank) * p[i])
        adj[i] = min(running, 1.0)
    return adj


def compare_family(df, family, pairs, metrics_, workloads, rng):
    """pairs: list of (reference policy, new policy)."""
    rows = []
    for ref, new in pairs:
        for metric in metrics_:
            for w in workloads:
                t = df[df.workload == w].pivot(index="seed", columns="policy", values=metric)
                if ref not in t or new not in t:
                    continue
                rows.append({"family": family, "workload": w, "metric": metric,
                             "reference": ref, "new": new, **paired(t[ref], t[new], rng)})
    out = pd.DataFrame(rows)
    if len(out):
        out["p_holm"] = holm(out["p_wilcoxon"])
    return out


def stats_rows(st):
    return [[r.workload, r.metric, r.reference, r.new, ms(r.ref_mean), ms(r.new_mean),
             f"{r.change_pct:+.1f}%", f"[{r.ci_lo:+.1f}, {r.ci_hi:+.1f}]",
             f"{r.p_wilcoxon:.3f}", f"{r.p_holm:.3f}", f"{r.wins}/{r.n}"] for r in st.itertuples()]


STATS_HEADER = ["Workload", "Metric", "Reference", "New", "Ref. mean", "New mean", "Change",
                "95% CI", "p (Wilcoxon)", "p (Holm)", "Wins"]


# ------------------------------------------------------------------ figures
def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def equivalent_sigma(curve, value):
    """sigma at which the noisy-oracle curve reaches `value` (linear interpolation)."""
    s, v = curve.index.values, curve.values
    if value <= v[0]:
        return 0.0
    for i in range(1, len(s)):
        if v[i] >= value:
            return s[i - 1] + (value - v[i - 1]) * (s[i] - s[i - 1]) / (v[i] - v[i - 1])
    return np.inf


def fmt_sigma(s):
    return "> 2 (worse than the whole sweep)" if np.isinf(s) else f"{s:.2f}"


def fig_noise(noise):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, w in zip(axes, ("W4", "W5")):
        d = noise[noise.workload == w]
        sweep = d[d.sigma.notna()]
        for family, colour, label in (("Adaptive-Noisy", BLUE, "Our scheduler, noisy oracle"),
                                      ("SJF-Noisy", ORANGE, "SJF, noisy oracle")):
            g = sweep[sweep.policy == family].groupby("sigma")["avg_wait"]
            m, s = g.mean(), g.std()
            ax.plot(m.index, m.values, "o-", color=colour, label=label, lw=2, ms=4)
            ax.fill_between(m.index, m - 1.96 * s / np.sqrt(g.count()),
                            m + 1.96 * s / np.sqrt(g.count()), color=colour, alpha=0.15, lw=0,
                            label=f"{label}: 95% interval for the 10-seed mean")
        refs = d[d.sigma.isna()].groupby("policy")[["avg_wait", "pred_log_sd"]].mean()
        for name, colour, style in (("Oracle", GRAY_DARK, ":"), ("RR-5", GRAY, "--"),
                                    ("FCFS", GRAY, ":")):
            ax.axhline(refs.loc[name, "avg_wait"], color=colour, ls=style, lw=1.2)
            ax.text(2.02, refs.loc[name, "avg_wait"], name, va="center", fontsize=8, color=INK_SOFT)
        for name, colour, marker in (("Adaptive-ML", BLUE, "*"), ("Adaptive-EMA", BLUE_LIGHT, "s"),
                                     ("SJF-EMA", ORANGE, "D")):
            ax.plot(refs.loc[name, "pred_log_sd"], refs.loc[name, "avg_wait"], marker,
                    color=colour, ms=11 if marker == "*" else 7, mec="black", mew=0.6,
                    label=f"{name} (real predictor, at its measured error)")
        ax.set_title(f"{w} · {ALL_PROFILES[w].description.split(' (')[0]}")
        ax.set_xlabel("prediction error σ (sd of log(actual / predicted))")
        ax.set_ylabel("average waiting time (ms)")
        ax.set_xlim(-0.05, 2.25)
    axes[0].legend(fontsize=7.5, loc="upper left")
    fig.suptitle("Prediction-quality sweep (diagnostic: the noisy oracle reads the true burst)",
                 fontsize=11, fontweight="bold")
    save(fig, "innov1_prediction_quality.png")


def fig_safeguards(st):
    d = st[st.family.str.startswith("Safeguard")]
    workloads = list(ALL_PROFILES)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=False)
    width = 0.26
    for ax, metric, title in zip(axes, ("avg_wait", "max_wait"),
                                 ("Average waiting time", "Worst-case waiting time")):
        for k, name in enumerate(INNOVATION_CONFIGS):
            x = np.arange(len(workloads)) + (k - 1) * width
            r = d[(d.new == name) & (d.metric == metric)].set_index("workload").reindex(workloads)
            ax.bar(x, r.change_pct, width, color=NEW_COLOURS[name], label=name)
            ax.errorbar(x, r.change_pct, yerr=[r.change_pct - r.ci_lo, r.ci_hi - r.change_pct],
                        fmt="none", ecolor="black", elinewidth=0.8, capsize=2)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(np.arange(len(workloads)), workloads)
        ax.set_title(f"{title}: change vs Adaptive-ML")
        ax.set_ylabel("change (%), below 0 is better")
    axes[0].legend(fontsize=8)
    fig.suptitle("Safeguards vs the original Adaptive-ML (10 seeds, bars = 95% bootstrap CI)",
                 fontsize=11, fontweight="bold")
    save(fig, "innov2_safeguards.png")


def fig_w7(comp):
    d = comp[comp.workload == "W7"]
    order = ["FCFS", "SJF-EMA", "SRTF-EMA", "RR-5", "MLFQ", "Oracle", "Adaptive-ML",
             "Adaptive-ML-G", "Adaptive-ML-A", "Adaptive-ML-GA"]
    m = d.groupby("policy")[["wait_interactive", "wait_io", "wait_bait"]].mean().reindex(order)
    fig, ax = plt.subplots(figsize=(11, 4))
    x = np.arange(len(order))
    for k, (col, colour, label) in enumerate((("wait_interactive", BLUE, "interactive (honest)"),
                                              ("wait_io", TEAL, "I/O-bound (honest)"),
                                              ("wait_bait", ORANGE, "bait processes"))):
        ax.bar(x + (k - 1) * 0.27, m[col], 0.27, color=colour, label=label)
    ax.set_xticks(x, order, rotation=25, ha="right")
    ax.set_ylabel("average waiting time (ms)")
    ax.set_title("W7 bait-and-switch: who pays for the long bursts? (10-seed means)")
    ax.legend(fontsize=8)
    save(fig, "innov3_w7_by_kind.png")


# ------------------------------------------------------------------- report
def main():
    rng = np.random.default_rng(0)
    main_res = pd.read_csv(RES / "main_results.csv")
    noise = pd.read_csv(OUT / "noise_sweep.csv")
    comp = pd.read_csv(OUT / "comparison.csv")
    tuning = pd.read_csv(OUT / "tuning.csv")
    reset = pd.read_csv(OUT / "ageing_reset_diagnostic.csv")
    w16 = [f"W{i}" for i in range(1, 7)]
    w17 = list(ALL_PROFILES)

    # Check: re-running the original configurations reproduces main_results.csv.
    merged = comp.merge(main_res, on=["workload", "seed", "policy"], suffixes=("", "_saved"))
    repro_err = float(np.max(np.abs(merged.avg_wait - merged.avg_wait_saved) / merged.avg_wait_saved))

    fams = [
        compare_family(main_res, "F1 original headline (Adaptive-ML vs SJF-EMA)",
                       [("SJF-EMA", OURS)], ["avg_wait", "max_wait"], w16, rng),
    ]
    for base in ("SRTF-EMA", "RR-5", "MLFQ", "Adaptive-EMA"):
        fams.append(compare_family(main_res, f"F2 Adaptive-ML vs {base}", [(base, OURS)],
                                   ["avg_wait"], w16, rng))
    for name in INNOVATION_CONFIGS:
        fams.append(compare_family(comp, f"Safeguard {name} vs Adaptive-ML", [(OURS, name)],
                                   ["avg_wait", "max_wait"], w17, rng))
    w7_rows = []
    for name in INNOVATION_CONFIGS + ["SJF-EMA", "RR-5", "MLFQ"]:
        w7_rows.append(compare_family(comp, "W7 honest processes", [(OURS, name)],
                                      ["wait_interactive", "resp_interactive"], ["W7"], rng))
    w7 = pd.concat(w7_rows)
    w7["p_holm"] = holm(w7["p_wilcoxon"])
    fams.append(w7)
    w7_rows = [compare_family(comp, "W7 Adaptive-ML-G vs baselines", [(b, "Adaptive-ML-G")],
                              ["avg_wait", "wait_interactive", "max_wait"], ["W7"], rng)
               for b in ("SJF-EMA", "RR-5", "MLFQ")]
    w7 = pd.concat(w7_rows)
    w7["p_holm"] = holm(w7["p_wilcoxon"])
    fams.append(w7)
    # Noise sweep: our full mechanism vs plain SJF, both with perfect predictions,
    # and how far the real ML predictor is from perfect predictions.
    nz = noise.copy()
    nz.loc[nz.sigma.notna(), "policy"] = nz.policy + "-" + nz.sigma.map("{:g}".format)
    fams.append(compare_family(nz, "F3 prediction quality", [
        ("SJF-Noisy-0", OURS), ("Adaptive-Noisy-0", OURS), ("SJF-Noisy-0", "Adaptive-Noisy-0")],
        ["avg_wait"], ["W4", "W5"], rng))
    st = pd.concat(fams, ignore_index=True)
    st.to_csv(OUT / "stats.csv", index=False)

    fig_noise(noise)
    fig_safeguards(st)
    fig_w7(comp)

    # ------------------------------------------------------------ tables
    L = ["# Post-Review 3 additions: results", "",
         "Generated by `analyse_innovation.py`. Original results in `results/*.csv` are unchanged; "
         "this report uses `results/innovation/`.", "",
         f"Reproduction check: re-running the 11 original configurations on W1–W6 inside the new "
         f"experiment gives the saved `main_results.csv` values to a relative error of {repro_err:.1e}.", ""]

    # Phase 1
    L += ["## 1. Prediction-quality sweep (diagnostic)", "",
          "`NoisyOraclePredictor`: prediction = true burst × exp(σZ). It reads the true burst, so it "
          "is a measuring device, not a scheduler. Same quantum, ageing and classifier as Adaptive-ML.", ""]
    for w in ("W4", "W5"):
        d = noise[noise.workload == w]
        sw = d[d.sigma.notna()].pivot_table(index="sigma", columns="policy", values="avg_wait")
        refs = d[d.sigma.isna()].groupby("policy")[["avg_wait", "max_wait", "pred_log_sd"]].mean()
        L += [f"**{w}** average wait (ms), 10-seed means", "",
              md_table(["σ", "Adaptive (noisy oracle)", "SJF (noisy oracle)"],
                       [[f"{s:g}", ms(r["Adaptive-Noisy"]), ms(r["SJF-Noisy"])] for s, r in sw.iterrows()]), "",
              md_table(["Real configuration", "Avg wait", "Worst wait", "Measured σ (log error sd)",
                        "Equivalent σ on our curve"],
                       [[n, ms(refs.loc[n, "avg_wait"]), ms(refs.loc[n, "max_wait"]),
                         "–" if np.isnan(refs.loc[n, "pred_log_sd"]) else f"{refs.loc[n, 'pred_log_sd']:.2f}",
                         (fmt_sigma(equivalent_sigma(sw['Adaptive-Noisy'], refs.loc[n, 'avg_wait']))
                          if n.startswith("Adaptive") else "–")]
                        for n in ("Adaptive-ML", "Adaptive-EMA", "SJF-EMA", "RR-5", "FCFS", "Oracle")]), ""]

    # Tuning
    tab = tuning.groupby(["group", "setting", "workload"])["score"].mean().unstack()
    tab["mean"] = tab.mean(axis=1)
    L += ["## 2. Tuning (seeds 100–102 only)", "",
          "Score = (avg wait / SJF avg wait + worst wait / SJF worst wait) / 2, averaged over W1–W7. "
          f"Chosen: guard {GUARD}, persistent-ageing beta {PERSISTENT_BETA}. "
          "Adaptive-ML-GA combines both choices without further tuning.", "",
          md_table(["Group", "Setting"] + list(tab.columns),
                   [[g, s] + [f"{v:.3f}" for v in r] for (g, s), r in tab.iterrows()]), ""]

    # Ageing diagnostic
    rd = reset.groupby("workload").mean(numeric_only=True)
    L += ["## 3. Waiting-credit reset diagnostic (Adaptive-ML, tuning seeds)", "",
          "Share of ready-queue waiting spent in earlier stays of a time-sliced burst, which the "
          "original ageing term no longer counts once the burst is sliced again.", "",
          md_table(["Workload", "Bursts sliced", "Wait discarded (all)", "Wait discarded (10 worst)",
                    "Most stays in one burst"],
                   [[w, f"{r.sliced_share:.0%}", f"{r.reset_wait_share_all:.0%}",
                     f"{r.reset_wait_share_worst10:.0%}", f"{r.max_stays_one_burst:.0f}"]
                    for w, r in rd.iterrows()]), ""]

    # Comparison
    show = ["FCFS", "SJF-EMA", "SRTF-EMA", "RR-5", "MLFQ", "Oracle", "Adaptive-EMA", OURS] + INNOVATION_CONFIGS
    for metric, label in (("avg_wait", "Average waiting time (ms)"), ("max_wait", "Worst-case waiting time (ms)"),
                          ("starved", "Starved processes per run"), ("context_switches", "Context switches")):
        m = comp.groupby(["workload", "policy"])[metric].mean().unstack().reindex(columns=show)
        L += [f"## 4. {label}, W1–W7, 10-seed means", "",
              md_table(["Workload"] + show, [[w] + [ms(v) for v in r] for w, r in m.iterrows()]), ""]

    d7 = comp[comp.workload == "W7"].groupby("policy").mean(numeric_only=True).reindex(show)
    L += ["## 5. W7 bait-and-switch, by process kind (ms, 10-seed means)", "",
          md_table(["Policy", "Wait interactive", "Resp. interactive", "Wait I/O", "Wait bait",
                    "Worst wait bait", "Avg wait all"],
                   [[p, ms(r.wait_interactive), ms(r.resp_interactive), ms(r.wait_io), ms(r.wait_bait),
                     ms(r.maxwait_bait), ms(r.avg_wait)] for p, r in d7.iterrows()]), ""]

    L += ["## 6. Paired statistics (all comparisons, favourable or not)", "",
          "Change = new vs reference. Negative is better for every metric here. Holm correction "
          "is applied within each family. In this project a difference is called significant "
          "only when p (Holm) < 0.05. A result with unadjusted p < 0.05 that does not survive the "
          "correction is described as not significant after correction (for example the guard's "
          "W1 average wait and W4 worst-case wait, both unadjusted p = 0.027).", ""]
    for fam, g in st.groupby("family", sort=False):
        L += [f"### {fam}", "", md_table(STATS_HEADER, stats_rows(g)), ""]

    bait_share = []
    for seed in sorted(comp.seed.unique()):
        specs = generate_workload("W7", int(seed))
        bait_share.append(sum(p.total_cpu for p in specs if p.kind == BAIT)
                          / sum(p.total_cpu for p in specs))
    L += ["## 7. Notes on method", "",
          "* **Guard formula corrected after the first tuning round.** The first version took the "
          "time left of an overrunning burst as c × (CPU time used). With c < 1 that can make the "
          "burst look shorter than its own estimate, the opposite of the intended behaviour. The "
          "guard now uses max(estimate, c × CPU time used) and was re-tuned. The first round is "
          "kept in `tuning_round1.csv`; only the corrected version was run on evaluation seeds.",
          "* **W7 was part of the tuning set.** The guard and persistent-ageing parameters were "
          "chosen on seeds 100–102 of W1–W7, so the guard was not tuned blind to the attack type. "
          "The evaluation seeds 0–9 were never used for tuning.",
          "* **c = 0.25 is the smallest non-zero value tested.** With the corrected formula "
          "c = 0 is exactly the original Adaptive-ML, whose tuning score (0.937) is worse than "
          "c = 0.25 (0.899). Values between 0 and 0.25 were not tested.",
          f"* **Bait processes dominate W7's CPU demand.** They are 30% of the processes but "
          f"{np.mean(bait_share):.0%} of the total CPU demand on average "
          f"({min(bait_share):.0%}–{max(bait_share):.0%} across seeds 0–9).",
          "* **Noisy oracle.** Its errors are random around the true value, whereas a real "
          "predictor's errors are systematic, so the measured σ of a real predictor is only an "
          "approximate position on the σ axis. The 'equivalent σ' column gives the σ at which the "
          "noisy-oracle curve reaches the real predictor's waiting time.",
          "* **Figure 1 shading** is the 95% interval for the 10-seed mean (mean ± 1.96 sd / √10). "
          "It shows variation between workload instances; the paired tests in section 6 are the "
          "basis for every comparison.", ""]
    L += ["## Configurations", "",
          md_table(["Name", "Description"], [[n, DESCRIPTIONS[n]] for n in INNOVATION_CONFIGS]), ""]
    (OUT / "REPORT.md").write_text("\n".join(L))
    print(f"Wrote {OUT / 'REPORT.md'}, {OUT / 'stats.csv'} and figures in {FIG}")


if __name__ == "__main__":
    main()
