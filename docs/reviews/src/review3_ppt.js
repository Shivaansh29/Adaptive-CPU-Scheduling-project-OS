// Builds docs/reviews/Review_3.pptx (11 slides).
// Run from the project root:  NODE_PATH=<folder with pptxgenjs>/node_modules node docs/reviews/src/review3_ppt.js
// Optional: OUT_PPTX=<path> writes somewhere else.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "../../..");
const IMG = (p) => path.join(ROOT, p);
const OUT = process.env.OUT_PPTX || path.join(ROOT, "docs/reviews/Review_3.pptx");

const THEME = {
  name: "Adaptive Scheduling",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F2937", lt1: "FFFFFF", dk2: "16324F", lt2: "EEF3F8",
    accent1: "2A78D6", accent2: "EB6834", accent3: "6B7280", accent4: "1BAF7A",
    accent5: "C7D2DE", accent6: "F2B134", hlink: "2A78D6", folHlink: "6B7280",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";   // 10 x 5.625 in
pres.title = "Adaptive CPU Scheduling - Review 3";
pres.author = "Shivaansh Aggarwal, Devansh Sharma";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 2.0, w: 8.8, h: 1.25,
      fontSize: 32, bold: true, color: C.background1, fontFace: THEME.headFontFace, valign: "top", align: "left", margin: 0 },
      text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HEX.lt1 },
  margin: [0.4, 0.5, 0.5, 0.5],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.28, w: 9.0, h: 0.65,
      fontSize: 26, bold: true, color: C.text2, fontFace: THEME.headFontFace, valign: "middle", align: "left", margin: 0 },
      text: "" } },
    { text: { text: "Adaptive CPU Scheduling  ·  Course Project Review 3",
      options: { x: 0.5, y: 5.2, w: 6, h: 0.3, fontSize: 10, color: C.accent3, margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: C.accent3, align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSING_DARK",
  background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.35, w: 9.0, h: 0.7,
      fontSize: 28, bold: true, color: C.background1, fontFace: THEME.headFontFace, valign: "middle", align: "left", margin: 0 },
      text: "" } },
  ],
});

// ---------------------------------------------------------------- helpers
const text = (slide, value, opts) => slide.addText(value, { isTextBox: true, margin: 0, color: C.text1, fontSize: 14, ...opts });
const card = (slide, x, y, w, h, name, fill = C.background2) =>
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill }, objectName: name });
const bullets = (items, size = 13) => items.map((t, i) => ({
  text: t, options: { bullet: { indent: 14 }, fontSize: size, color: C.text1, paraSpaceAfter: 6, breakLine: i < items.length - 1 },
}));
const stat = (slide, x, y, w, big, label, name, colour = C.accent1, h = 1.1) => {
  card(slide, x, y, w, h, name);
  text(slide, big, { x: x + 0.2, y: y + 0.08, w: w - 0.4, h: 0.5, fontSize: 26, bold: true, color: colour, fontFace: THEME.headFontFace });
  text(slide, label, { x: x + 0.2, y: y + 0.62, w: w - 0.4, h: h - 0.68, fontSize: 11, color: C.text1, valign: "top" });
};
const caption = (slide, value, x, y, w) => text(slide, value, { x, y, w, h: 0.25, fontSize: 10, italic: true, color: C.accent3 });
const head = (labels, size = 11) => labels.map((t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: size } }));

// ---------------------------------------------------------------- slides
pres.addSection({ title: "Introduction" });

// 1. Title
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Introduction" });
  card(s, 0.6, 0.45, 3.5, 1.15, "Logo panel", C.background1);
  s.addImage({ path: IMG("docs/reviews/assets/vit_logo.png"), x: 0.72, y: 0.53, w: 3.26, h: 1.0, objectName: "VIT logo", altText: "Vellore Institute of Technology logo" });
  text(s, "Operating System (BCSE303P)  ·  Course Project – Review 3", { x: 0.6, y: 1.65, w: 8.8, h: 0.3, fontSize: 13, color: C.accent5 });
  s.addText("Adaptive CPU Scheduling Using Predicted Burst Lengths", { placeholder: "title", bold: true, align: "left" });
  text(s, "Evaluation, robustness to prediction errors, comparison and conclusion", { x: 0.6, y: 3.3, w: 8.8, h: 0.35, fontSize: 15, color: C.accent5 });
  text(s, "Shivaansh Aggarwal (24BCE0883)   ·   Devansh Sharma (24BCE0717)", { x: 0.6, y: 4.35, w: 8.8, h: 0.3, fontSize: 14, color: C.background1, bold: true });
  text(s, "Slot L15+L16   ·   Faculty: Dr. Anisha M. Lal", { x: 0.6, y: 4.7, w: 8.8, h: 0.3, fontSize: 13, color: C.accent5 });
  s.addNotes("Shivaansh: Good morning ma'am. I'm Shivaansh and this is Devansh. Our scheduler predicts how long a program will run next and uses that to decide who runs and for how long. In this review we also asked what happens when the prediction is wrong.");
}

// 2. Problem and approach
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
  s.addText("The problem and our approach", { placeholder: "title", bold: true, align: "left" });
  card(s, 0.5, 1.1, 4.3, 3.85, "Problem card");
  text(s, "The problem", { x: 0.75, y: 1.25, w: 3.9, h: 0.35, fontSize: 17, bold: true, color: C.text2, fontFace: THEME.headFontFace });
  s.addText(bullets([
    "SJF is optimal but needs the next burst length, which the OS does not know",
    "Round Robin's quantum is fixed by hand and never revisited",
    "Prediction-based schedulers trust the prediction: a burst that outruns it keeps looking short",
    "With time slicing, such a burst returns after every quantum and is picked again",
  ], 12.5), { x: 0.75, y: 1.7, w: 3.9, h: 3.15, isTextBox: true, margin: 0, valign: "top" });

  const steps = [
    ["1", "Who runs next", "P = predicted time left − β × time waited. Lowest P runs; ageing (β = 0.03) prevents starvation."],
    ["2", "How long it runs", "Quantum = 80th percentile of predictions × recent error ratios, updated every 50 decisions (1–100 ms)."],
    ["3", "Overrun guard (new)", "Once a burst passes its prediction × median error ratio, time left = max(prediction, 0.25 × CPU used)."],
  ];
  steps.forEach(([n, title, body], i) => {
    const y = 1.1 + i * 1.3;
    card(s, 5.1, y, 4.4, 1.15, `Approach card ${n}`);
    s.addShape(pres.shapes.OVAL, { x: 5.28, y: y + 0.17, w: 0.42, h: 0.42, fill: { color: i === 2 ? C.accent2 : C.accent1 }, line: { color: i === 2 ? C.accent2 : C.accent1 }, objectName: `Step ${n} badge` });
    text(s, n, { x: 5.28, y: y + 0.17, w: 0.42, h: 0.42, align: "center", valign: "middle", bold: true, color: C.background1, fontSize: 15 });
    text(s, title, { x: 5.85, y: y + 0.12, w: 3.5, h: 0.32, bold: true, fontSize: 15, color: C.text2 });
    text(s, body, { x: 5.85, y: y + 0.46, w: 3.5, h: 0.64, fontSize: 11.5, valign: "top" });
  });
  s.addNotes("Shivaansh: SJF is optimal but needs the future, and Round Robin's quantum is fixed by hand. A scheduler that predicts bursts fixes that, but it trusts its prediction: a long burst predicted as short keeps looking short every time it comes back from a time slice. Devansh: so we use the prediction twice, to pick who runs with ageing, and to set the quantum from the 80% rule. And we added an overrun guard: once a burst clearly outruns its prediction, its estimate grows with the CPU time it has used.");
}

pres.addSection({ title: "Performance evaluation" });

// 3. Setup and method
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Performance evaluation" });
  s.addText("How we evaluated it", { placeholder: "title", bold: true, align: "left" });
  [["7", "workloads (W1–W6 + adversarial W7)"], ["14", "scheduler configurations"], ["10", "evaluation seeds, all runs paired"], ["53 / 53", "automated tests pass"]]
    .forEach(([big, label], i) => stat(s, 0.5 + i * 2.29, 1.1, 2.08, big, label, `Setup stat ${i + 1}`));
  text(s, "Seeds kept apart", { x: 0.5, y: 2.45, w: 4.3, h: 0.3, bold: true, fontSize: 15, color: C.text2 });
  s.addText(bullets(["Training the predictor: seeds 1000–1004", "Tuning β and the guard: seeds 100–102", "Evaluation: seeds 0–9 (never used for tuning)"], 12.5),
    { x: 0.5, y: 2.8, w: 4.3, h: 1.3, isTextBox: true, margin: 0, valign: "top" });
  text(s, "Statistics", { x: 5.1, y: 2.45, w: 4.4, h: 0.3, bold: true, fontSize: 15, color: C.text2 });
  s.addText(bullets(["Paired bootstrap 95% confidence intervals", "Exact Wilcoxon signed-rank test, Holm-corrected", "Significant only if Holm p < 0.05; losses reported too"], 12.5),
    { x: 5.1, y: 2.8, w: 4.4, h: 1.3, isTextBox: true, margin: 0, valign: "top" });
  card(s, 0.5, 4.2, 9.0, 0.75, "W7 note");
  text(s, "W7 is intentionally adversarial: 30% bait processes (many ~1 ms bursts, then one ~400 ms burst) that make up 76% of the CPU demand. The simulator reproduces the textbook answers exactly (FCFS 17, SJF 3, RR 5.67, SRTF 6.5 ms).",
    { x: 0.7, y: 4.23, w: 8.6, h: 0.69, fontSize: 12, valign: "middle" });
  s.addNotes("Shivaansh: We ran 7 workloads and 14 configurations on 10 evaluation seeds, so every scheduler sees exactly the same processes. Training, tuning and evaluation used separate seeds. Every claim is checked with paired tests and a Holm correction, and we report losses as well. W7 is a workload we designed to attack the scheduler: bait processes run tiny bursts and then a very long one.");
}

// 4. Main result
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Performance evaluation" });
  s.addText("Mixed workload: 27% less waiting than SJF", { placeholder: "title", bold: true, align: "left" });
  s.addImage({ path: IMG("docs/reviews/assets/w4_avg_wait.png"), x: 0.5, y: 1.05, w: 5.75, h: 3.9, objectName: "W4 average wait chart", altText: "Bar chart of average waiting time on the mixed workload W4 for all 11 schedulers" });
  stat(s, 6.5, 1.1, 3.0, "−27.4%", "avg wait vs SJF-EMA, 95% CI −32.4 to −23.7%, better on 10 of 10 seeds", "Stat avg wait");
  stat(s, 6.5, 2.45, 3.0, "54%", "of the gap to the oracle (SRTF with true bursts) closed", "Stat oracle gap");
  stat(s, 6.5, 3.8, 3.0, "−61%", "context switches vs RR-5, response 15 ms vs 23 ms", "Stat switches");
  s.addNotes("Shivaansh: On the mixed workload our scheduler waits 1,786 ms against 2,460 for SJF with exponential averaging, 27% less, better on all ten seeds and statistically significant. It closes 54% of the gap to the oracle and needs 61% fewer context switches than Round Robin with 5 ms.");
}

// 5. Across workloads
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Performance evaluation" });
  s.addText("Across the six standard workloads", { placeholder: "title", bold: true, align: "left" });
  const data = [
    ["W1 CPU-bound", "−1.9%", "−56% *", "7 / 10", "No"],
    ["W2 I/O-bound", "+13.8%", "+0.5%", "0 / 10", "Yes (loss)"],
    ["W3 Interactive", "+5.3%", "−27% *", "2 / 10", "No"],
    ["W4 Mixed", "−27.4%", "−23% *", "10 / 10", "Yes"],
    ["W5 Phase-changing", "−1.7%", "−53% *", "4 / 10", "No"],
    ["W6 Overload", "+2.6%", "−2%", "2 / 10", "No"],
  ].map((r) => r.map((t, j) => ({ text: t, options: {
    bold: r[0].startsWith("W4"), fill: { color: r[0].startsWith("W4") ? C.background2 : C.background1 },
    align: j === 0 ? "left" : "center", fontSize: 12, color: j === 4 && t.includes("loss") ? C.accent2 : C.text1 } })));
  s.addTable([head(["Workload", "Avg wait vs SJF-EMA", "Worst wait vs SJF-EMA", "Seeds better", "Avg significant?"], 12), ...data],
    { x: 0.5, y: 1.05, w: 9.0, colW: [2.2, 1.8, 1.9, 1.4, 1.7], rowH: 0.33, border: { type: "solid", pt: 0.75, color: HEX.accent5 }, valign: "middle", objectName: "Per-workload table" });
  caption(s, "* worst-case change significant after Holm correction (p < 0.05)", 0.5, 3.4, 9.0);
  card(s, 0.5, 3.75, 4.35, 1.2, "Why it works card");
  text(s, "Why it works", { x: 0.7, y: 3.84, w: 4.0, h: 0.3, bold: true, fontSize: 14, color: C.accent1 });
  text(s, "The quantum follows the workload (≈6 ms interactive, ≈97 ms CPU-bound, 3.4 ms I/O). Ageing halves the worst case. Prediction alone gains only 5%.", { x: 0.7, y: 4.15, w: 4.0, h: 0.75, fontSize: 11.5, valign: "top" });
  card(s, 5.15, 3.75, 4.35, 1.2, "Limits card");
  text(s, "Where it does not", { x: 5.35, y: 3.84, w: 4.0, h: 0.3, bold: true, fontSize: 14, color: C.accent2 });
  text(s, "All-I/O work is 13.8% worse (significant): tiny random bursts leave nothing to predict. Fairness index slightly below SJF-EMA on 5 of 6.", { x: 5.35, y: 4.15, w: 4.0, h: 0.75, fontSize: 11.5, valign: "top" });
  s.addNotes("Devansh: Across the six standard workloads, the clear win is the mixed workload. The worst case drops by about half on CPU-bound and phase-changing work, and that is significant. The quantum adapts to each workload, and prediction alone gives only 5%, so the gain comes from using it twice. Honestly, on all-I/O work we are 14% worse, and that loss is significant.");
}

pres.addSection({ title: "Robustness to prediction errors" });

// 6. Prediction quality
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Robustness to prediction errors" });
  s.addText("How much does prediction quality matter?", { placeholder: "title", bold: true, align: "left" });
  s.addImage({ path: IMG("figures/innovation/innov1_prediction_quality.png"), x: 0.5, y: 1.1, w: 6.1, h: 2.79, objectName: "Prediction quality sweep", altText: "Line charts of average waiting time against prediction error on W4 and W5" });
  caption(s, "Diagnostic only: the noisy oracle reads the true burst and adds error exp(σZ)", 0.5, 3.95, 6.1);
  stat(s, 6.85, 1.1, 2.65, "−28.4%", "W4: our mechanism vs SJF, both with perfect predictions (10/10)", "Stat mechanism", C.accent1, 1.15);
  stat(s, 6.85, 2.4, 2.65, "22.5%", "W4: further gain possible with perfect predictions", "Stat headroom", C.accent1, 1.15);
  stat(s, 6.85, 3.7, 2.65, "σ 1.25 → 1.86", "real errors cost more than random errors of the same size", "Stat real errors", C.accent2, 1.15);
  text(s, "On W5 the curve is flat (5,057 → 5,240 ms): there the time slicing, not the predictor, is the bottleneck.", { x: 0.5, y: 4.3, w: 6.1, h: 0.6, fontSize: 12 });
  s.addNotes("Devansh: To separate the predictor from the mechanism, we fed both our scheduler and plain SJF predictions with controlled error. With perfect predictions our mechanism still beats SJF by 28% on W4, so the mechanism matters. Perfect predictions would give another 22%. Real errors hurt more than random ones, because long bursts are systematically under-predicted. On W5 prediction quality barely matters.");
}

// 7. The weakness and the guard
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Robustness to prediction errors" });
  s.addText("The weakness: a long burst that looks short", { placeholder: "title", bold: true, align: "left" });
  const steps = [
    ["1", "Predicted 1.2 ms", "A bait process has run 15 tiny bursts, so the model expects another tiny one."],
    ["2", "Runs 40 ms, still looks like 1.2 ms", "Without the guard it returns after each quantum with a 1.2 ms estimate and is picked again."],
    ["3", "Guard: max(1.2, 0.25 × 40) = 10 ms", "A new interactive burst predicted at 5 ms now runs first; after 200 ms the bait burst looks like 50 ms."],
  ];
  steps.forEach(([n, title, body], i) => {
    const y = 1.1 + i * 1.3;
    card(s, 0.5, y, 5.4, 1.15, `Weakness step ${n}`);
    s.addShape(pres.shapes.OVAL, { x: 0.68, y: y + 0.17, w: 0.42, h: 0.42, fill: { color: i === 2 ? C.accent4 : C.accent2 }, line: { color: i === 2 ? C.accent4 : C.accent2 }, objectName: `Weakness badge ${n}` });
    text(s, n, { x: 0.68, y: y + 0.17, w: 0.42, h: 0.42, align: "center", valign: "middle", bold: true, color: C.background1, fontSize: 15 });
    text(s, title, { x: 1.25, y: y + 0.12, w: 4.5, h: 0.32, bold: true, fontSize: 14, color: C.text2 });
    text(s, body, { x: 1.25, y: y + 0.46, w: 4.5, h: 0.64, fontSize: 11.5, valign: "top" });
  });
  card(s, 6.2, 1.1, 3.3, 3.85, "W7 card");
  text(s, "W7 bait-and-switch", { x: 6.4, y: 1.25, w: 2.9, h: 0.35, bold: true, fontSize: 16, color: C.text2, fontFace: THEME.headFontFace });
  s.addText(bullets([
    "Intentionally adversarial",
    "50% interactive, 20% I/O-bound, 30% bait",
    "Bait: 10–20 bursts of ~1 ms, then one ~400 ms burst, twice",
    "Bait processes: 76% of the CPU demand",
    "Guard tuned on seeds 100–102, tested on 0–9",
  ], 12), { x: 6.4, y: 1.7, w: 2.95, h: 3.15, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Shivaansh: Here is the weakness. A bait process runs many tiny bursts, so the model predicts 1.2 ms, then it runs for hundreds. Without a guard it comes back after each quantum still looking like 1.2 ms and is picked again. The guard says: once you clearly outrun your prediction, your time left is a quarter of the CPU time you have used, never less than the prediction. W7 is our deliberately adversarial workload; the bait processes use 76% of the CPU.");
}

// 8. W7 results
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Robustness to prediction errors" });
  s.addText("Live demo: the guard on W7", { placeholder: "title", bold: true, align: "left" });
  s.addImage({ path: IMG("docs/terminal/11_demo_w7.png"), x: 0.5, y: 1.0, w: 7.6, h: 2.36, objectName: "W7 demo output", altText: "Terminal output of demo_innovation.py on the W7 workload" });
  caption(s, "Real Terminal output of  python demo_innovation.py  (W7, seed 0)", 0.5, 3.4, 7.6);
  text(s, "Below: 10-seed means, paired tests", { x: 8.3, y: 1.05, w: 1.2, h: 0.9, fontSize: 11, italic: true, color: C.accent3 });
  stat(s, 0.5, 3.75, 2.1, "−21.5%", "avg wait vs Adaptive-ML (10/10)", "Stat W7 avg", C.accent1, 1.2);
  stat(s, 2.8, 3.75, 2.1, "−92%", "interactive wait (1,399 → 112 ms)", "Stat W7 interactive", C.accent1, 1.2);
  stat(s, 5.1, 3.75, 2.1, "+9.3%", "MLFQ still has the lower avg wait", "Stat MLFQ", C.accent2, 1.2);
  stat(s, 7.4, 3.75, 2.1, "≈2×", "worst-case wait of RR-5 and MLFQ", "Stat worst case", C.accent2, 1.2);
  s.addNotes("Devansh: This is the live demo on W7. Without the guard our scheduler loses to Round Robin and MLFQ. With the guard, interactive processes wait 103 ms instead of 1,221 here. Over ten seeds the average wait drops 21.5% and interactive waiting 92%. But MLFQ still has a 9% lower average wait on W7, and our worst case is about twice theirs, so it is not a complete defence.");
}

// 9. Trade-offs and negative results
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Robustness to prediction errors" });
  s.addText("Trade-offs and a negative result", { placeholder: "title", bold: true, align: "left" });
  s.addImage({ path: IMG("figures/innovation/innov2_safeguards.png"), x: 0.5, y: 1.1, w: 6.1, h: 2.54, objectName: "Safeguards chart", altText: "Bar charts of the change in average and worst-case waiting time for each safeguard on W1 to W7" });
  caption(s, "Change vs Adaptive-ML (green: guard, purple: persistent ageing, gold: both); bars = 95% CI", 0.5, 3.7, 6.1);
  card(s, 6.85, 1.1, 2.65, 1.75, "Guard cost card");
  text(s, "Guard elsewhere", { x: 7.03, y: 1.2, w: 2.3, h: 0.3, bold: true, fontSize: 14, color: C.accent4 });
  text(s, "W1–W5 average: −1.8% to +0.1%, none significant. W4 worst case +5.6% (not significant after correction).", { x: 7.03, y: 1.52, w: 2.3, h: 1.28, fontSize: 11.5, valign: "top" });
  card(s, 6.85, 3.0, 2.65, 1.95, "Persistent ageing card");
  text(s, "Persistent ageing", { x: 7.03, y: 3.1, w: 2.3, h: 0.3, bold: true, fontSize: 14, color: C.accent2 });
  text(s, "Fixes a real mismatch (the reset discards 70% of W4 waiting) but avg wait +17.5% on W6, +51% on W7. Not retained.", { x: 7.03, y: 3.42, w: 2.3, h: 1.48, fontSize: 11.5, valign: "top" });
  text(s, "Recommended configuration: Adaptive-ML with the overrun guard.", { x: 0.5, y: 4.15, w: 6.1, h: 0.4, fontSize: 13, bold: true, color: C.text2 });
  s.addNotes("Shivaansh: A safeguard must be cheap when nothing is wrong. On the five standard workloads the guard changes the average by less than 2%, none significant. We also found that our ageing credit resets after every time slice. Making it persistent sounded right, but it raised average waits by 17% under overload and 51% on W7, because it rewards exactly the long bait bursts. So we did not keep it.");
}

pres.addSection({ title: "Comparison and conclusion" });

// 10. Comparison
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Comparison and conclusion" });
  s.addText("Comparison with existing schedulers", { placeholder: "title", bold: true, align: "left" });
  const data = [
    ["FCFS", "4,003", "19,407", "3,962", "3,630"],
    ["SJF-EMA", "2,460", "23,766", "3,977", "3,847"],
    ["SRTF-EMA", "1,729", "24,903", "6,902", "4,045"],
    ["RR-5", "2,180", "14,887", "15,328", "1,741"],
    ["MLFQ", "1,878", "15,016", "11,888", "1,495"],
    ["Adaptive-ML (ours)", "1,786", "18,388", "5,933", "2,083"],
    ["Adaptive-ML-G (ours + guard)", "1,786", "19,426", "5,938", "1,634"],
  ].map((r) => r.map((t, j) => ({ text: t, options: { bold: r[0].startsWith("Adaptive"), fontSize: 11, color: C.text1,
    align: j ? "right" : "left", fill: { color: r[0].startsWith("Adaptive") ? C.background2 : C.background1 } } })));
  s.addTable([head(["Scheduler", "W4 avg (ms)", "W4 worst (ms)", "W4 switches", "W7 avg (ms)"]), ...data],
    { x: 0.5, y: 1.05, w: 6.0, colW: [2.2, 0.95, 1.0, 0.95, 0.9], rowH: 0.34, border: { type: "solid", pt: 0.75, color: HEX.accent5 }, valign: "middle", objectName: "Comparison table" });
  caption(s, "Mean of 10 evaluation seeds.", 0.5, 4.05, 6.0);
  card(s, 6.75, 1.05, 2.75, 3.9, "Comparison notes");
  s.addText(bullets([
    "W4: lowest average wait except SRTF (3% better, not significant; 35% higher worst case)",
    "W4: MLFQ close on average but needs twice the switches",
    "W7: MLFQ has the lowest average; the guard beats RR-5 and gives interactive work the shortest waits",
    "Unlike dynamic-quantum papers, burst lengths are never assumed known",
  ], 11.5), { x: 6.9, y: 1.18, w: 2.5, h: 3.7, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Shivaansh: On the mixed workload we have the lowest average wait except SRTF, which is 3% better but not significantly, with a 35% higher worst case. MLFQ is close but needs twice the switches. On the adversarial W7, MLFQ has the lowest average, and with the guard we beat Round Robin and give interactive processes the shortest waits.");
}

// 11. Conclusion
{
  const s = pres.addSlide({ masterName: "CLOSING_DARK", sectionTitle: "Comparison and conclusion" });
  s.addText("Conclusion and future work", { placeholder: "title", bold: true, align: "left" });
  const col = (x, title, items, name) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.2, w: 4.35, h: 2.85, rectRadius: 0.08, fill: { color: C.background1, transparency: 90 }, line: { color: C.accent5, width: 0.75 }, objectName: name });
    text(s, title, { x: x + 0.25, y: 1.35, w: 3.9, h: 0.35, bold: true, fontSize: 17, color: C.background1, fontFace: THEME.headFontFace });
    s.addText(items.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, fontSize: 12.5, color: C.background1, paraSpaceAfter: 6, breakLine: i < items.length - 1 } })),
      { x: x + 0.25, y: 1.8, w: 3.9, h: 2.15, isTextBox: true, margin: 0, valign: "top" });
  };
  col(0.5, "Conclusion", [
    "Using the prediction twice gives 27% less waiting on mixed work",
    "The gain comes mainly from the mechanism, not the model",
    "The overrun guard closes a real weakness: −92% interactive wait on W7",
    "Not a complete defence; worse on all-I/O work; persistent ageing not kept",
  ], "Conclusion column");
  col(5.15, "Future work", [
    "Real program traces and other adversarial patterns",
    "A worst-case bound for the guard",
    "Load-aware ageing",
    "A small tree or lookup table inside xv6",
  ], "Future work column");
  text(s, "Thank you", { x: 0.5, y: 4.35, w: 9.0, h: 0.5, fontSize: 22, bold: true, color: C.background1, align: "center", fontFace: THEME.headFontFace });
  s.addNotes("Shivaansh: To conclude, using the prediction twice gives 27% less waiting on mixed workloads, mainly thanks to the mechanism. The guard fixes a real weakness of prediction-based scheduling, cutting interactive waiting on W7 by 92%, but it is not a complete defence, we lose on all-I/O work, and persistent ageing did not pay off. Next we would test on real traces and move it into xv6. Thank you, ma'am.");
}

// pptxgenjs writes Office's default colour scheme into the theme, so the scheme colours
// used above would show as Office blue and orange. Write THEME's colours and name instead.
async function writeThemeColours(file) {
  const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const part = "ppt/theme/theme1.xml";
  const slots = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];
  const scheme = `<a:clrScheme name="${THEME.name}">` +
    slots.map((k) => `<a:${k}><a:srgbClr val="${HEX[k]}"/></a:${k}>`).join("") + "</a:clrScheme>";
  const xml = (await zip.file(part).async("string"))
    .replace(/<a:clrScheme\b[\s\S]*?<\/a:clrScheme>/, () => scheme)
    .replace(/(<a:(?:theme|fontScheme)\b[^>]*?\bname=")[^"]*"/g, (_, head) => `${head}${THEME.name}"`);
  if (!xml.includes(scheme)) throw new Error("no colour scheme found in " + part);
  zip.file(part, xml);
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await writeThemeColours(OUT);
  console.log("wrote", OUT);
})();
