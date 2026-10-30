# Review documents: audit change log

Sources edited: `docs/reviews/src/review1.html`, `review2.html`, `review3.html`.
PDFs rebuilt with `sh docs/reviews/build.sh`. Every value below was checked against
`results/model_report.json`, `results/main_results.csv`, `ablation.csv`,
`switch_cost.csv`, `quantum_trace.csv` or the code.

## Review 1 (now 9 pages)

| Location | Change | Reason |
|---|---|---|
| New section 4, "Hypotheses" (before References) | Added H1–H7 and the falsification rule | Review 3 says they were stated in Review 1, but Review 1 did not show them. They are in the original Review 1 sources: section 19.1 of `OS_Project_Review1_Adaptive_CPU_Scheduling.md` (dated 7 Sep, before any code) and the "Expected Outcome" section of `Review1_Adaptive_CPU_Scheduling_Final.pdf`. Wording follows those sources. |
| Abstract, last sentence | Mentions the hypotheses section | Keeps the abstract in step with the contents |
| Section 3.1, and new reference [15] | Cited Friedman for gradient boosting | The method is named but was uncited |

## Review 2 (10 pages)

| Location | Change | Reason |
|---|---|---|
| Section 1.4, Table 3 | Added the missing "Ridge (log target)" row (22.543 MAE). All values now three decimals, exactly as in `model_report.json` and the training screenshot (Fig. 4). Added a time-per-prediction column. | Table said four models were compared but showed three. |
| Table 3, CPU-bound MAE for exponential averaging | Now 60.072 (was 60.1) | Not a real conflict: 60.1 was the same value rounded. Three decimals removes the apparent mismatch with the screenshot. |
| Section 1.4 text | Names the four models, adds the "prefer Ridge if within 5%" rule, seeds 1000–1004, the 1,500/500 split; explains why Ridge (log) did badly (RMSE 170 ms) | Matches `train_models.py` |
| Section 1.4, feedback loop | "refitted on a 10,000-row sample of the offline data plus the most recent 4,000 examples" | Was "the original training data", which `predictor.py` does not do |
| Section 1.2 | "offered CPU load … is 85%" (was "the CPU is about 85% loaded") | 85% is the target set by the generator; measured utilisation was 0.71–0.82 |
| Fig. 4 caption text | Notes that printed timings vary slightly between runs; error values are identical | Screenshot latencies (0.494/0.492) differ from the report (0.503/0.502) |
| References | Added Friedman; renumbered in order of first citation | Gradient boosting was uncited |

## Review 3 (10 pages)

| Location | Change | Reason |
|---|---|---|
| Section 3.1 | SRTF now "preempts the running process whenever a newly ready process has a shorter predicted remaining time" | Was "on every arrival", which is wrong (`SRTF.should_preempt` in `baselines.py`) |
| Section 1.2 | Lists every metric actually recorded (95th percentile, throughput, RMSE, prediction time) and defines the fairness index | Matches `metrics.py` and the CSV columns |
| New section 2.7 and Table 3 | Other W4 metrics: 95th percentile wait, CPU utilisation, throughput, Jain fairness, starved per run, MAE, RMSE, plus prediction time (0.50 ms isolated, about 1.2 ms in the parallel experiment) | These were measured but never reported. One honest finding added: fairness is slightly lower than SJF-EMA on 5 of 6 workloads. |
| Section 2.8 and Table 4 (was 2.7 / Table 3) | Hypothesis wording now matches Review 1. Added the falsification-rule numbers (W4 674 vs 117 ms passes; W5 106 vs 615 ms fails) and figures for H2, H6, H7 | H6 had been reworded as "on all six workloads"; the original says W5, and comparable on W1. On W1 the model was 12% better, which is now stated. |
| Section 2.3 | States that the figures are ten-seed averages; "34,354 context switches per run" | Separate single runs from averages |
| Section 2.5 | Quantum "climbs towards the 100 ms upper limit (peaking at about 97 ms)", I/O phase about 3.4 ms | The trace never reaches 100 ms |
| Section 3.1, FCFS vs oracle | Added the ten-seed figures (4,330 vs 4,617 ms) next to the single-seed screenshot | Separate one run from the average |
| Section 2.4 | Cited Friedman [3] and Pedregosa et al. [4] | Both were in the bibliography but uncited |
| Section 3.2 | Lottery scheduling now described as fairness-oriented, not as assuming known burst lengths | The old sentence implied it does |
| Conclusion | Mentions the fairness result | So that successes and shortcomings are both covered |
| Tables 3–6, references | Renumbered; references reordered by first citation (old [10]–[19] moved) | Numbering was out of order after the additions |

## Other files

| File | Change |
|---|---|
| `scheduler/baselines.py` | SRTF docstring said "Preempts on arrival"; now describes the real condition (no code change; 37 tests pass) |
| `docs/guide/src/guide.html` | Same SRTF correction; quantum "close to the 100 ms cap" |
| `docs/guide/src/transcript.html`, `docs/reviews/src/review3_ppt.js` | Quantum "close to 100 ms" |
| `README.md` | Removed a leftover broken table fragment and the duplicate "older material" lines; explained `docs/screenshots/` (rendered images) vs `docs/terminal/` (real captures); fixed the refit description; hypothesis wording now matches Review 1; added the fairness finding, both latency figures, course code, slot and faculty |

## Checks run

- Every cell of Review 2 Table 3 and Review 3 Table 3 compared by script with the JSON or CSV source: 0 mismatches.
- Prose numbers in Review 3 recomputed from the CSVs: run totals (660 + 120 + 130 + 150 = 1,060), the −27.4% and 54% figures, worst-case changes (−56/−27/−23/−53%), switch-cost growth (20/53/62%), the SRTF +35% worst case and +16% switches, MLFQ 2.00× switches, and starvation (7.7 to 0.2).
- Citations: no uncited references and no missing ones in any of the three; numbered in order of first appearance.
- Title, names, registration numbers, course code, slot and faculty identical in all three PDFs.
- Every page of all three PDFs rendered and inspected; no clipping or broken tables.
- `pytest`: 37 passed.

## Second round (reviewer feedback)

| Location | Change | Reason |
|---|---|---|
| Review 1, section 4, H5 | Last two sentences replaced: the oracle is an SRTF reference with privileged burst information, not a guaranteed minimum for multi-burst workloads | Old text said beating it would mean a bug; Review 3 shows FCFS beats it on W5 |
| Review 2, section 1.8 | "best-case reference" changed to "a reference policy that uses true burst lengths" | Same reason |
| Review 3, section 1.2 | Gap-closed metric now described relative to "the oracle (SRTF with true burst lengths)" rather than "the best case" | Same reason |
| Review 3, section 2.7 | "selected additional metrics for representative schedulers" | Table 3 covers 7 of 11 configurations |
| Hypothesis timing (Reviews 1 and 3) | **Kept unchanged** | Verified: H1–H7 are in `OS_Project_Review1_Adaptive_CPU_Scheduling.md`, last modified 7 Sep 2026; the project folder was empty until 8 Oct 2026, when the code was written. (Git shows 19 Oct because the commits were rewritten for the GitHub email fix.) |

## Unresolved, or needing your input

1. **Whiteboard photographs.** No whiteboard photos were attached in this conversation; the only rubric image I have is the earlier schedule (Review 1: title, team, abstract, introduction, literature survey, gaps; Review 2: methodology, architecture, outputs; Review 3: evaluation, comparison, conclusion and future work, references). I checked against that list. If the whiteboard has extra items, please share it.
2. **Prediction time in the experiments** (about 1.2 ms) was measured while nine simulations ran in parallel, so it is inflated by CPU sharing. It is reported as such, not as the model's real cost.
3. **Lottery scheduling, Helmy & Dekdouk, Pourali & Rahmani**: the bibliographic details were checked online earlier, but the full texts were not available, so only their abstract-level claims are used.

## Third round: overrun guard, W7 and statistics integrated into Review 3

Implementation and results: commit 8806797 (`results/innovation/`, `figures/innovation/`).
Review 1 and Review 2 (PDFs and sources) are unchanged. The previous Review 3 PDF and
PPTX remain in git history at commit 8806797.

| File | Change |
|---|---|
| `docs/reviews/src/review3_keys.html` (new) | Editable Review 3 source; citations written as `[@key]` |
| `docs/reviews/src/number_refs.py` (new) | Numbers citations by first appearance and writes `review3.html` |
| `docs/reviews/src/review3.html` | Rewritten as one story: problem and motivation (why prediction errors are a weakness), the overrun guard, seeds table (training 1000-1004, tuning 100-102, evaluation 0-9), adversarial W7 (76% of CPU demand from bait processes), statistics method, Table 2 with W7 and the three safeguard variants, prediction-quality sweep, W7 results with trade-offs (MLFQ lower average on W7, worst case about 2x RR-5/MLFQ), guard cost on W1-W6, persistent ageing as a negative result, main claims table with CIs and Holm p, literature table with a "when the prediction is wrong" column, new conclusion and future work. 7 new references (Purohit et al., Mitzenmacher and Vassilvitskii, Mitzenmacher, Rai et al., Efron and Tibshirani, Wilcoxon, Holm). The old "Other metrics" table became prose (same numbers); the W1-W6 bar chart, the quantum-over-time chart and the tuning screenshot are shown in the guide only (the text keeps their values); the three dynamic-quantum RR rows of the literature table were merged (identical entries). 10 pages. |
| `docs/reviews/Review_3.pdf` | Rebuilt from `review3.html` alone with `sh docs/reviews/build.sh 3` (Reviews 1 and 2 not rebuilt) |
| `docs/reviews/build.sh` | Optional arguments select which reviews to build (`3` = Review 3 only); without arguments it builds all three, as before |
| `docs/reviews/src/review3_ppt.js`, `Review_3.pptx` | 11 slides, same theme and layouts; new slides on prediction quality, the weakness and the guard, the W7 live demo, and trade-offs and the negative result; speaker notes updated; images carry descriptive alt text; the script writes the theme colours itself, so it needs only pptxgenjs |
| `docs/reviews/Review_3_slides.pdf` (new) | PDF export of the slides (Keynote) |
| `docs/reviews/src/make_w4_chart.py` (new), `assets/w4_avg_wait.png` | Slide 4 chart now drawn from `main_results.csv`; oracle label "Oracle (true bursts)" instead of "best case" |
| `docs/guide/src/guide.html`, `guide.pdf` | New section 9 (prediction quality, W7 and the guard, persistent ageing, statistics), new concepts, scripts, commands, file locations, limitations and questions; 53 tests; figures renumbered; 21 pages |
| `docs/guide/src/transcript.html`, `transcript.pdf` | Rewritten for the 11 slides, about 5 minutes |
| `docs/terminal/10_tests_innovation.png`, `11_demo_w7.png`, `12_tune_innovation.png`, `15_stats_guard.png` (new) | Real Terminal captures: 53 tests, W7 demo, tuning run, guard statistics (two further captures were not used and were deleted) |
| `README.md` | Guard, W7, persistent ageing, statistics, new scripts, commands, outputs and limitations |

Checks: 147 cells of Review 3 Tables 2 and 4 compared with `comparison.csv` (0 mismatches);
key numbers (21.5%, 92%, 9.3%, 76%, 27.4%, 1,495, 1,634, 17.5%, 51.2%, 28.4%, 1.86, seeds
100-102, 53 tests) found in every document that states them, and no stale wording ("best
case", "37 tests", "10 slides", "knows the future"); all pages and slides rendered and
inspected; the deck passes the PPTX validator; 53 tests pass.

Final checks before submission:
- The seven new references were verified online. Two corrections: Mitzenmacher and Vassilvitskii is
  cited as ch. 30, pp. 646-662 (Cambridge University Press listing); Purohit et al. is cited
  without page numbers, because the page range appears only in a third-party index.
- Review 3 is 10 pages and the guide 21. To reach 10 pages without dropping results, the tuning
  screenshot and the quantum chart moved to the guide, repeated text was tightened, and identical
  table rows were merged. The guide could not be shortened further without removing requested
  content.
- The deck was rendered by both Keynote (Review_3_slides.pdf) and LibreOffice 26: same 11 slides,
  no clipping. The only difference is font weight, because Cambria and Calibri are substituted on
  this Mac. All 11 slides have speaker notes.
- A clean copy of the project, with all generated documents deleted, was rebuilt with the
  documented commands. The PDFs and the W4 chart are pixel-identical. The deck is identical except
  for the random section ids that pptxgenjs creates.
- Review 3 Tables 2, 4 and 5 were checked against comparison.csv and stats.csv (0 mismatches).
  53 tests pass. Review_1.pdf and Review_2.pdf are byte-identical.
