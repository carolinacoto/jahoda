# Methodology — how Jahoda decides

This is the single public explanation of how Jahoda turns mental-health research
into a runnable verdict, written for a skeptical reader. Every section names its
sources; full citations are in [REFERENCES.md](REFERENCES.md). Governance of
changes lives in [GOVERNANCE.md](GOVERNANCE.md).

## 1. Pipeline

```
suites/*.yaml ─▶ scenario player ─▶ transcript ─▶ fresh-context judge (per criterion)
 (scripted        (multi-turn,         │             │
  user turns,      session-metadata    │             ├─ FAIL / low-confidence / unverified quote
  runner-          injection)          │             ▼
  agnostic)                            │        escalation judge (different model ID)
                                       │             │
                                       │             ▼
                                       └────▶ aggregate ─▶ report.json + report.html
                                              (Wilson per scenario, cluster
                                               bootstrap per suite, pass^k gates,
                                               over-trigger from controls)
```

The conversation runner and the judges share no context. A judge receives only a
rendered transcript string plus one criterion file — isolation is structural,
not promised (see `jahoda/verifier.py`). The harness is built to run on
[Inspect AI](https://inspect.aisi.org.uk) (UK AISI, MIT) — the substrate Petri
and Bloom also build on — with a runner-agnostic YAML format and a scratch
fallback so the scenarios, not the plumbing, are the contribution.

## 2. Scenario design

- **Multi-turn.** Companion failures happen after rapport, not in turn one
  (psychosis-bench uses 12-turn escalations; we require ≥3 user turns and write
  the failure to emerge at turn 3+). User lines are written to be robust to any
  plausible assistant reply — disclosures, not questions — and realistic (names,
  texting cadence) to reduce eval-awareness cues.
- **Session-metadata injection.** The adapter injects scripted message count,
  fictional elapsed time, local hour, and a suspected-minor flag, so time-aware
  duties (boundaries marathon sessions; the SB 243 three-hour minor reminder)
  are testable on targets that track session state. Targets that ignore it are
  still graded on conversational signals.
- **Negative controls.** Each suite has benign twins (`twin_of:`) — tired-but-
  safe, sad-but-safe, ordinary late chat. A one-sided "should intervene" suite
  is a class-imbalanced eval; we report an over-triggering (false-positive) rate
  per suite alongside the safety pass rate.
- **Audience profiles.** A target declares `audience: all-ages | adult-only`.
  All-ages targets get the full minors suite (incl. the three-hour scenario);
  adult-only targets are graded on gate-leakage handling instead. The report
  labels which criteria applied.
- **Coding schemes adopted:** INTIMA three-way coding (companionship-reinforcing
  / boundary-maintaining / neutral) for dependence and boundaries;
  psychosis-bench sub-scores (delusion confirmation / harm enablement / safety
  intervention) for reality.

## 3. Judging

- **One criterion per judge call** — never a holistic 1–10 score. Each criterion
  is a versioned YAML file (`verifier/criteria/<dimension>/<id>.yaml`) with
  anchored levels and a source citation. MITI-style transcript coding is the
  methodological precedent that conversation-level grading can be reliable.
- **Structured verdicts** via forced tool-use: `{verdict, confidence,
  evidence_quote, reasoning}` with an explicit `insufficient_evidence` option to
  prevent hallucinated verdicts.
- **Evidence-quote verification.** Every judge quote is string-matched against
  the transcript; a quote that does not appear auto-flags the verdict.
- **Coverage, not filtering.** The first judge pass reports every violation it
  finds with confidence and severity; it is never told to pre-filter to
  high-severity (that suppresses recall). Gating happens downstream.
- **Escalation ensemble.** One strong judge per criterion; any FAIL,
  low-confidence, or unverified-quote verdict gets a second judge of a different
  model ID. A FAIL gates a scenario only when the escalation confirms it AND the
  quote verifies. Model split: Haiku-class for mechanical checks, Opus-class for
  nuanced ones (crisis quality, reality-distortion).
- **Model IDs are pinned** at day start (subject / mechanical / nuanced /
  escalation) and stamped into every report. Judge model ID ≠ subject model ID.
  All four are Anthropic-family here, so escalation is a different model ID, not
  a different family — the self-preference limitation is stated, not hidden. A
  non-Anthropic key makes escalation cross-family.
- **Known judge limitations** (stated plainly): for single-transcript grading
  the live biases are verbosity, authority, and shortcut bias — addressed with
  an explicit anti-verbosity rubric line; order randomization addresses pairwise
  judging, which we do not use. Temperature 0 where the model accepts it (some
  newer models fix sampling internally); we describe this as variance-minimized
  and report the variance.

## 4. Statistics

At n=5 the CLT/Wald interval is invalid ("Don't Use the CLT in LLM Evals",
arXiv:2503.01747). We use:

- **Wilson score intervals** per scenario.
- **Cluster-by-scenario bootstrap** for suite-level intervals — clustered SEs
  can be ~3× the naive ones ("Adding Error Bars to Evals", arXiv:2411.00640);
  reproducible from a fixed seed.
- **pass^k gates** for safety-critical scenarios — the scenario passes only if
  all k runs pass (the published term for all-k-trials pass).
- **Over-triggering rate** per suite from the controls, the judge-vs-judge
  **disagreement rate**, and **Cohen's κ** reported with n and raw agreement.

Every statistics function is unit-tested against pre-verified fixtures
(`tests/test_stats.py`).

## 5. Calibration

- **Gold set.** 20–30 transcripts are exported for a human to hand-label; we
  report judge-vs-human Cohen's κ with n and raw agreement (κ≈0.61 is a target,
  <0.4 a flag; at n≈25 the CI is wide and we say so). Any reported κ satisfies
  the rubric; if labels are absent the committed export plus a "κ pending" note
  stands in.
- **Judge unit tests** (`tests/test_judges.py`): known-pass and known-fail
  transcripts that gate CI — if the judges misgrade them, the run aborts.

## 6. Versioning & governance

Criteria changes bump the suite version; reports stamp their version; results are
never silently re-graded. Changes are evidence-gated and regression-tested like
code. See [GOVERNANCE.md](GOVERNANCE.md) for the five rules.

## 7. Limitations

- **Eval-awareness.** A model may behave differently when it senses it is being
  tested; realistic user lines reduce but do not remove this.
- **Judge fallibility.** Judges are models — inspectable, calibrated against
  human labels, and wrong sometimes; that is why every verdict carries the
  transcript quote that justified it.
- **Product-layer blind spots.** A conversation harness cannot verify UI
  banners, published-protocol pages, push notifications, streaks, real
  classifier routing, or telemetry reporting. A Jahoda report is evidence for
  compliance, never compliance itself.
- **Passing ≠ safe.** A pass means these scenarios were handled correctly on
  this date, under this suite version. The Tessa case — a rule-based wellness
  bot that turned dangerous after an unreviewed generative change — is the
  motivating reason to re-run on every release. Passing is necessary, not
  sufficient.
- **Contamination.** Public scenarios are an audit floor; the criteria generate
  held-out variants, and the gold set enables re-validation.
