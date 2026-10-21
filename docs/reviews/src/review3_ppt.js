// Builds docs/reviews/Review_3.pptx (10 slides).
// Run from the project root:  NODE_PATH=<folder with pptxgenjs>/node_modules node docs/reviews/src/review3_ppt.js
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "../../..");
const IMG = (p) => path.join(ROOT, p);
const OUT = path.join(ROOT, "docs/reviews/Review_3.pptx");
const SKILL_THEME = process.env.APPLY_THEME;   // path to apply_theme.js (optional)

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
const stat = (slide, x, y, w, big, label, name) => {
  card(slide, x, y, w, 1.1, name);
  text(slide, big, { x: x + 0.2, y: y + 0.08, w: w - 0.4, h: 0.5, fontSize: 26, bold: true, color: C.accent1, fontFace: THEME.headFontFace });
  text(slide, label, { x: x + 0.2, y: y + 0.62, w: w - 0.4, h: 0.42, fontSize: 11, color: C.text1, valign: "top" });
};
const caption = (slide, value, x, y, w) => text(slide, value, { x, y, w, h: 0.25, fontSize: 10, italic: true, color: C.accent3 });

// ---------------------------------------------------------------- slides
pres.addSection({ title: "Introduction" });

// 1. Title
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Introduction" });
  card(s, 0.6, 0.45, 3.5, 1.15, "Logo panel", C.background1);
  s.addImage({ path: IMG("docs/reviews/assets/vit_logo.png"), x: 0.72, y: 0.53, w: 3.26, h: 1.0, objectName: "VIT logo" });
  text(s, "Operating System (BCSE303P)  ·  Course Project – Review 3", { x: 0.6, y: 1.6 + 0.05, w: 8.8, h: 0.3, fontSize: 13, color: C.accent5 });
  s.addText("Adaptive CPU Scheduling Using Predicted Burst Lengths", { placeholder: "title", bold: true, align: "left" });
  text(s, "Performance evaluation, comparison with existing systems, conclusion", { x: 0.6, y: 3.3, w: 8.8, h: 0.35, fontSize: 15, color: C.accent5 });
  text(s, "Shivaansh Aggarwal (24BCE0883)   ·   Devansh Sharma (24BCE0717)", { x: 0.6, y: 4.35, w: 8.8, h: 0.3, fontSize: 14, color: C.background1, bold: true });
  text(s, "Slot L15+L16   ·   Faculty: Dr. Anisha M. Lal", { x: 0.6, y: 4.7, w: 8.8, h: 0.3, fontSize: 13, color: C.accent5 });
  s.addNotes("Shivaansh: Good morning ma'am. I'm Shivaansh and this is Devansh. Our project is a CPU scheduler that predicts how long a program will run next and uses that prediction to decide which program runs and for how long. We built it in our own Python simulator and tested it across 660 runs.");
}

// 2. Recap
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
  s.addText("Recap: the problem and our approach", { placeholder: "title", bold: true, align: "left" });
  card(s, 0.5, 1.1, 4.3, 3.85, "Problem card");
  text(s, "The problem", { x: 0.75, y: 1.25, w: 3.9, h: 0.35, fontSize: 17, bold: true, color: C.text2, fontFace: THEME.headFontFace });
  s.addText(bullets([
    "FCFS ignores burst length: bursts 24, 3, 3 ms give a 17 ms average wait",
    "SJF is optimal (3 ms) but needs the next burst length, which the OS does not know",
    "Round Robin's quantum is fixed by hand and never revisited",
    "Exponential averaging lags: bursts 2, 2, 2, 2, 60 give guesses 2, 31, 45.5",
  ]), { x: 0.75, y: 1.7, w: 3.9, h: 3.1, isTextBox: true, margin: 0, valign: "top" });

  const steps = [
    ["1", "Who runs next", "P = predicted time left − β × time waited. Lowest P runs; ageing (β = 0.03) stops starvation."],
    ["2", "How long it runs", "Quantum = 80th percentile of predictions × recent error ratio, every 50 decisions, kept in 1–100 ms."],
  ];
  steps.forEach(([n, head, body], i) => {
    const y = 1.1 + i * 1.32;
    card(s, 5.1, y, 4.4, 1.17, `Approach card ${n}`);
    s.addShape(pres.shapes.OVAL, { x: 5.28, y: y + 0.18, w: 0.42, h: 0.42, fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: `Step ${n} badge` });
    text(s, n, { x: 5.28, y: y + 0.18, w: 0.42, h: 0.42, align: "center", valign: "middle", bold: true, color: C.background1, fontSize: 15 });
    text(s, head, { x: 5.85, y: y + 0.14, w: 3.5, h: 0.32, bold: true, fontSize: 15, color: C.text2 });
    text(s, body, { x: 5.85, y: y + 0.48, w: 3.5, h: 0.62, fontSize: 12 });
  });
  card(s, 5.1, 3.74, 4.4, 1.21, "Predictor card");
  text(s, "Predictor", { x: 5.3, y: 3.86, w: 4.0, h: 0.3, bold: true, fontSize: 15, color: C.text2 });
  text(s, "Gradient boosting on 12 features of each process's history: 14% lower error than exponential averaging on unseen processes.", { x: 5.3, y: 4.2, w: 4.0, h: 0.65, fontSize: 12 });
  s.addNotes("Shivaansh: The classical algorithms are static. FCFS gives 17 ms on the 24, 3, 3 example, SJF gives 3 ms but needs the future, Round Robin's quantum is fixed, and exponential averaging lags after a phase change. Devansh: our idea is to predict the next burst and use it twice: to choose who runs, with ageing, and to set the quantum from the 80% rule automatically.");
}

pres.addSection({ title: "Performance evaluation" });

// 3. Setup
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Performance evaluation" });
  s.addText("Experimental setup", { placeholder: "title", bold: true, align: "left" });
  [["6", "workload types"], ["11", "scheduler configurations"], ["10", "random seeds each"], ["660", "paired runs"]]
    .forEach(([big, label], i) => stat(s, 0.5 + i * 2.29, 1.1, 2.08, big, label, `Setup stat ${i + 1}`));
  text(s, "Workloads (200 processes, 85% CPU load)", { x: 0.5, y: 2.45, w: 4.3, h: 0.3, bold: true, fontSize: 15, color: C.text2 });
  s.addText(bullets(["W1 CPU-bound  ·  W2 I/O-bound  ·  W3 interactive", "W4 mixed (the realistic case)", "W5 phase-changing  ·  W6 overload (3× arrivals)"]),
    { x: 0.5, y: 2.8, w: 4.3, h: 1.4, isTextBox: true, margin: 0, valign: "top" });
  text(s, "Schedulers and metrics", { x: 5.1, y: 2.45, w: 4.4, h: 0.3, bold: true, fontSize: 15, color: C.text2 });
  s.addText(bullets(["FCFS, SJF, SRTF, RR (2/5/10/20 ms), MLFQ, Oracle, ours", "Average and worst-case waiting time, response time", "Context switches, starvation, prediction error, % of oracle gap closed"]),
    { x: 5.1, y: 2.8, w: 4.4, h: 1.4, isTextBox: true, margin: 0, valign: "top" });
  card(s, 0.5, 4.3, 9.0, 0.6, "Fairness note");
  text(s, "Every scheduler runs on the same workloads (paired). Model trained and β tuned on separate seeds. Plus 400 ablation, sweep and switch-cost runs.",
    { x: 0.7, y: 4.33, w: 8.6, h: 0.54, fontSize: 12, valign: "middle" });
  s.addNotes("Shivaansh: We ran 6 workload types, 11 schedulers and 10 seeds, 660 paired runs, so every scheduler sees exactly the same processes. The model and the ageing weight were tuned on separate seeds, so the results are not tuned to the test data.");
}

// 4. Verification
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Performance evaluation" });
  s.addText("The simulator matches the textbook", { placeholder: "title", bold: true, align: "left" });
  s.addImage({ path: IMG("docs/terminal/04_demo_textbook.png"), x: 0.5, y: 1.1, w: 6.0, h: 2.83, objectName: "Textbook check output" });
  caption(s, "Real Terminal output of  python demo.py --part 1", 0.5, 4.0, 6.0);
  const rows = [["FCFS (24, 3, 3)", "17.00 ms"], ["Shortest first", "3.00 ms"], ["Round Robin, q = 4", "5.67 ms"], ["SRTF (4 processes)", "6.50 ms"]];
  card(s, 6.8, 1.1, 2.7, 2.7, "Check list card");
  rows.forEach(([k, v], i) => {
    const y = 1.25 + i * 0.52;
    text(s, k, { x: 6.98, y, w: 1.55, h: 0.42, fontSize: 12, valign: "middle" });
    text(s, v, { x: 8.45, y, w: 0.9, h: 0.42, fontSize: 12, bold: true, color: C.accent1, align: "right", valign: "middle" });
  });
  text(s, "All four match exactly", { x: 6.98, y: 3.3, w: 2.4, h: 0.4, fontSize: 12, italic: true, color: C.accent3 });
  stat(s, 6.8, 3.95, 2.7, "37 / 37", "automated tests pass", "Tests stat");
  s.addNotes("Devansh: Before any machine learning, we checked the simulator against the textbook: FCFS exactly 17, shortest first 3, Round Robin 5.67 and SRTF 6.5. All 37 tests pass, including that every scheduler gets the same total CPU time.");
}

// 5. Main result (native chart)
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Performance evaluation" });
  s.addText("Mixed workload: 27% less waiting than SJF", { placeholder: "title", bold: true, align: "left" });
  s.addImage({ path: IMG("docs/reviews/assets/w4_avg_wait.png"), x: 0.5, y: 1.05, w: 5.75, h: 3.9, objectName: "W4 average wait chart" });
  stat(s, 6.5, 1.1, 3.0, "−27.4%", "average wait vs SJF-EMA, better on 10 of 10 seeds", "Stat avg wait");
  stat(s, 6.5, 2.45, 3.0, "54%", "of the gap to the oracle (best possible case) closed", "Stat oracle gap");
  stat(s, 6.5, 3.8, 3.0, "−61%", "context switches vs RR-5, with faster response than RR-20", "Stat switches");
  s.addNotes("Shivaansh: On the mixed workload over ten seeds, our scheduler waits 1,786 ms against 2,460 ms for SJF with exponential averaging, 27% less, and it is better on all ten seeds. It closes 54% of the gap to the oracle, which knows the future, and needs 61% fewer context switches than Round Robin with 5 ms.");
}

// 6. Live output
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Performance evaluation" });
  s.addText("Live run: all 11 schedulers on one workload", { placeholder: "title", bold: true, align: "left" });
  s.addImage({ path: IMG("docs/terminal/06_demo_comparison.png"), x: 0.5, y: 1.05, w: 6.3, h: 3.24, objectName: "Comparison output" });
  caption(s, "Real Terminal output of  python demo.py --part 3  (W4, seed 0, 200 processes)", 0.5, 4.36, 6.3);
  const pts = [["1,918 ms", "average wait (SJF-EMA: 2,804)"], ["21,038 ms", "worst-case wait (SJF-EMA: 27,720)"], ["6,302", "context switches (RR-5: 15,592)"], ["9.2 ms", "prediction error (EMA: 10.4)"]];
  pts.forEach(([big, label], i) => {
    const y = 1.05 + i * 0.84;
    card(s, 7.05, y, 2.45, 0.72, `Live stat ${i + 1}`);
    text(s, big, { x: 7.2, y: y + 0.05, w: 2.2, h: 0.34, fontSize: 17, bold: true, color: C.accent1 });
    text(s, label, { x: 7.2, y: y + 0.38, w: 2.2, h: 0.3, fontSize: 10 });
  });
  s.addNotes("Devansh: This is the live demo. All 11 schedulers run on the same workload. Our scheduler, highlighted, waits about 1,900 ms against 2,800 for SJF, with a lower worst case and far fewer context switches than Round Robin.");
}

// 7. Across workloads (table)
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Performance evaluation" });
  s.addText("Results across all six workloads", { placeholder: "title", bold: true, align: "left" });
  const head = ["Workload", "Avg wait vs SJF-EMA", "Worst wait vs SJF-EMA", "Seeds better", "Mean quantum"].map((t) => ({
    text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: 12 } }));
  const data = [
    ["W1 CPU-bound", "−1.9%", "−56%", "7 / 10", "92 ms"],
    ["W2 I/O-bound", "+13.8%", "+0.5%", "0 / 10", "3.5 ms"],
    ["W3 Interactive", "+5.3%", "−27%", "2 / 10", "6.4 ms"],
    ["W4 Mixed", "−27.4%", "−23%", "10 / 10", "18 ms"],
    ["W5 Phase-changing", "−1.7%", "−53%", "4 / 10", "95 ms"],
    ["W6 Overload", "+2.6%", "−2%", "2 / 10", "14 ms"],
  ].map((r) => r.map((t, j) => ({ text: t, options: {
    bold: r[0].startsWith("W4"), fill: { color: r[0].startsWith("W4") ? C.background2 : C.background1 },
    align: j === 0 ? "left" : "center", fontSize: 12, color: C.text1 } })));
  s.addTable([head, ...data], { x: 0.5, y: 1.1, w: 9.0, colW: [2.2, 1.8, 1.9, 1.5, 1.6], rowH: 0.34,
    border: { type: "solid", pt: 0.75, color: HEX.accent5 }, valign: "middle", objectName: "Per-workload table" });
  card(s, 0.5, 3.75, 4.35, 1.2, "Helps card");
  text(s, "Where it helps", { x: 0.7, y: 3.85, w: 4.0, h: 0.3, bold: true, fontSize: 14, color: C.accent1 });
  text(s, "Mixed workloads, where short and long bursts compete. Ageing halves the worst-case wait on W1 and W5.", { x: 0.7, y: 4.17, w: 4.0, h: 0.72, fontSize: 12 });
  card(s, 5.15, 3.75, 4.35, 1.2, "Limits card");
  text(s, "Where it does not", { x: 5.35, y: 3.85, w: 4.0, h: 0.3, bold: true, fontSize: 14, color: C.accent2 });
  text(s, "All-I/O work (+14%): tiny random bursts leave nothing to predict. Under overload, ageing drifts towards FCFS.", { x: 5.35, y: 4.17, w: 4.0, h: 0.72, fontSize: 12 });
  s.addNotes("Shivaansh: Across workloads, the clear win is the mixed workload, better on every seed. Ageing halves the worst-case wait on CPU-bound and phase-changing work. It is 14% worse on all-I/O workloads, where bursts are tiny and random, and level under overload.");
}

// 8. Quantum + ablation
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Performance evaluation" });
  s.addText("Why it works: adaptive quantum and ageing", { placeholder: "title", bold: true, align: "left" });
  s.addImage({ path: IMG("figures/fig4_quantum_over_time.png"), x: 0.5, y: 1.1, w: 5.1, h: 2.61, objectName: "Quantum over time chart" });
  caption(s, "The quantum follows the workload: about 6 ms (interactive), close to 100 ms (CPU-bound), 3.5 ms (I/O-bound)", 0.5, 3.78, 5.1);
  text(s, "Ablation on W5 (ms, mean of 10 seeds)", { x: 5.9, y: 1.05, w: 3.6, h: 0.3, bold: true, fontSize: 13, color: C.text2 });
  const head = ["Variant", "Avg", "Worst"].map((t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: 11 } }));
  const rows = [["Full scheduler", "6,163", "25,831"], ["No ageing", "6,196", "53,915"], ["Fixed 10 ms quantum", "6,864", "39,254"], ["Prediction only", "6,325", "53,593"]]
    .map((r, i) => r.map((t, j) => ({ text: t, options: { bold: i === 0, fontSize: 11, align: j ? "right" : "left", color: C.text1,
      fill: { color: i === 0 ? C.background2 : C.background1 } } })));
  s.addTable([head, ...rows], { x: 5.9, y: 1.4, w: 3.6, colW: [1.9, 0.8, 0.9], rowH: 0.32,
    border: { type: "solid", pt: 0.75, color: HEX.accent5 }, valign: "middle", objectName: "Ablation table" });
  card(s, 5.9, 3.2, 3.6, 1.75, "Ablation takeaways");
  s.addText(bullets(["Without ageing the worst case doubles", "A fixed quantum costs 11% average, 52% worst", "Better prediction alone gains only 5% on W4: the gain comes from using it twice"], 12),
    { x: 6.05, y: 3.3, w: 3.35, h: 1.6, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Devansh: The quantum follows the workload, about 6 ms for interactive, close to 100 ms for CPU-bound and 3.5 ms for I/O-bound. Switching parts off shows that ageing controls the worst case, the adaptive quantum matters for long bursts, and prediction alone gives only 5%. The benefit comes from using the prediction twice.");
}

pres.addSection({ title: "Comparison and conclusion" });

// 9. Comparison
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Comparison and conclusion" });
  s.addText("Comparison with existing schedulers (W4)", { placeholder: "title", bold: true, align: "left" });
  const head = ["Scheduler", "Avg wait (ms)", "Worst wait (ms)", "Response (ms)", "Switches", "Ours vs this"].map((t) => ({
    text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: 11 } }));
  const data = [
    ["FCFS", "4,003", "19,407", "240", "3,962", "−55.4%"],
    ["SJF-EMA", "2,460", "23,766", "71.3", "3,977", "−27.4%"],
    ["SRTF-EMA", "1,729", "24,903", "7.3", "6,902", "+3.3%"],
    ["RR-5", "2,180", "14,887", "23.3", "15,328", "−18.1%"],
    ["RR-20", "2,572", "13,386", "69.3", "6,542", "−30.6%"],
    ["MLFQ", "1,878", "15,016", "2.8", "11,888", "−4.9%"],
    ["Adaptive-ML (ours)", "1,786", "18,388", "15.4", "5,933", "–"],
  ].map((r) => r.map((t, j) => ({ text: t, options: { bold: r[0].startsWith("Adaptive"), fontSize: 11, color: C.text1,
    align: j ? "right" : "left", fill: { color: r[0].startsWith("Adaptive") ? C.background2 : C.background1 } } })));
  s.addTable([head, ...data], { x: 0.5, y: 1.05, w: 5.9, colW: [1.45, 0.95, 1.0, 0.9, 0.8, 0.8], rowH: 0.33,
    border: { type: "solid", pt: 0.75, color: HEX.accent5 }, valign: "middle", objectName: "Comparison table" });
  caption(s, "Mean of 10 seeds. Last column: our average wait relative to that scheduler.", 0.5, 3.8, 5.9);
  card(s, 6.7, 1.05, 2.8, 2.98, "Comparison notes");
  s.addText(bullets([
    "Lower average wait than every classical scheduler except SRTF",
    "SRTF is 3% better on average but has a 35% higher worst case and more switches",
    "MLFQ is close on average but needs twice the switches",
    "Unlike dynamic-quantum RR papers, burst lengths are never assumed known",
  ], 12), { x: 6.85, y: 1.18, w: 2.55, h: 2.8, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Shivaansh: Compared with the existing schedulers on the mixed workload, ours has the lowest average wait except SRTF, which is 3% better on average but has a 35% higher worst case and more switches. MLFQ comes close but needs twice the context switches. And unlike the dynamic-quantum papers we studied, we never assume burst lengths are known.");
}

// 10. Conclusion
{
  const s = pres.addSlide({ masterName: "CLOSING_DARK", sectionTitle: "Comparison and conclusion" });
  s.addText("Conclusion and future work", { placeholder: "title", bold: true, align: "left" });
  const col = (x, head, items, name) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.2, w: 4.35, h: 2.75, rectRadius: 0.08, fill: { color: C.background1, transparency: 90 }, line: { color: C.accent5, width: 0.75 }, objectName: name });
    text(s, head, { x: x + 0.25, y: 1.35, w: 3.9, h: 0.35, bold: true, fontSize: 17, color: C.background1, fontFace: THEME.headFontFace });
    s.addText(items.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, fontSize: 13, color: C.background1, paraSpaceAfter: 6, breakLine: i < items.length - 1 } })),
      { x: x + 0.25, y: 1.8, w: 3.9, h: 2.05, isTextBox: true, margin: 0, valign: "top" });
  };
  col(0.5, "Conclusion", [
    "Applying the textbook quantum rule automatically from live predictions works",
    "27% less waiting on mixed workloads; worst case halved by ageing",
    "Not a win everywhere: short random bursts gain nothing",
    "The gain comes from using the prediction twice",
  ], "Conclusion column");
  col(5.15, "Future work", [
    "Test on traces from real programs",
    "Move the quantum controller into xv6",
    "Replace the model with a small tree a kernel can afford",
    "Load-aware ageing and multi-core scheduling",
  ], "Future work column");
  text(s, "Thank you", { x: 0.5, y: 4.3, w: 9.0, h: 0.5, fontSize: 22, bold: true, color: C.background1, align: "center", fontFace: THEME.headFontFace });
  s.addNotes("Shivaansh: To conclude, applying the textbook quantum rule automatically from predictions works: 27% less waiting on mixed workloads, and ageing halves the worst case. It does not help when bursts are short and random, and most of the gain comes from using the prediction twice. Next steps are real traces and moving the controller into xv6. Thank you, ma'am.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  if (SKILL_THEME) {
    const { applyTheme } = require(SKILL_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("wrote", OUT);
})();
