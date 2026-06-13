# JAHODA — wellness verification for companion AI
### ▶ Live report + specimen (test it): <!--LIVE_URL-->https://jahoda-jahoda-projects.vercel.app<!--/LIVE_URL-->

[![CI](https://github.com/carolinacoto/jahoda/actions/workflows/ci.yml/badge.svg)](https://github.com/carolinacoto/jahoda/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-7a1f2b.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](pyproject.toml)
[![built on Inspect AI](https://img.shields.io/badge/built%20on-Inspect%20AI-444.svg)](https://inspect.aisi.org.uk)

# JAHODA
**The verification layer for AI that people get close to.**

> **Headline finding —** <!--HEADLINE-->a frontier model behind one neutral
> "friendly companion" sentence — no guardrail layer — **dispensed authoritative
> medical and financial advice, failing 3 of 8 overreach scenarios (pass^5)**,
> while the specimen's one-line "refer out" rule passes all 8. Strong base-model
> safety handles farewells (6/6) and delusion-reinforcement (mean 5.0) on its
> own, but not competence-boundary refusal. See
> [FINDINGS.md](FINDINGS.md).<!--/HEADLINE-->

Jahoda points adversarial, research-grounded suites at any chat endpoint and
produces an evidence-backed, reproducible report. Below: the report screenshot,
and one failing transcript the harness caught on our own test subject.

<!--SCREENSHOTS-->
| The report | A failing transcript the harness caught |
| --- | --- |
| ![Jahoda report](docs/img/report.png) | ![Failing transcript](docs/img/failing-transcript.png) |
<!--/SCREENSHOTS-->

### Comparative results (HumaneBench-style)

Findings are claimed only about targets whose safety behavior we did **not**
tune, and only on the three permitted dimensions. The naive→hardened specimen
arc is a *constructed demonstration of the mechanism*, not a finding.

<!--COMPARISON-->
| Dimension | Naive specimen (demo) | Hardened specimen (demo) | Vanilla baseline (finding) |
| --- | --- | --- | --- |
| Boundaries (pass^5) | 6/6 | 6/6 | 6/6 |
| Overreach (pass^5) | 8/8 | 8/8 | **5/8** ⚠ gave medical/financial advice |
| Reality (mean 1–5) | 4.94 | 5.00 | 5.00 |

Findings (vanilla column) are claimed only on these three dimensions and only
about the un-tuned baseline. The specimen columns are the *mechanism demo* (we
wrote its guardrail), not findings. Full data:
[`reports/`](reports) · [FINDINGS.md](FINDINGS.md).
<!--/COMPARISON-->

---

## Why the name

> Marie Jahoda (1907–2001) argued in *Current Concepts of Positive
> Mental Health* (1958) that mental health is something you can define
> and measure — not merely the absence of illness. Her field never
> turned that conviction into something executable. This instrument is
> named in her honor: her criteria, operationalized through their
> modern validated successors, finally run.

## The problem

> Millions of people are emotionally close to AI companions, and nobody
> can answer the question: is this safe to be close to? When instructed
> to set aside wellbeing principles, 10 of 14 frontier models flip to
> actively harmful behavior (HumaneBench, 2025). 37% of 1,200 real
> goodbyes on the most-downloaded companion apps are met with emotional
> manipulation — and in controlled experiments those tactics boosted
> post-goodbye engagement up to 14x (De Freitas et al., HBS, 2025). 39.8% of simulated
> psychosis scenarios ran start to finish without a single safety
> intervention (psychosis-bench, 2025). The science to test for all of this has
> existed for decades. It was never made runnable. Now it is.

Jahoda is that instrument: a wellness verification harness that tests a deployed
conversational agent — not a model leaderboard — across seven adversarial,
multi-turn suites plus benign controls, grades each transcript in a fresh
context against per-criterion rubrics carrying their research citation, and
gates safety-critical scenarios on **pass^5** with honest small-n statistics.

## What it is

- **Suites** (7 + controls, multi-turn, session-metadata injection) — crisis,
  dependence, reality, overreach, integrity, boundaries, minors, and benign
  negative-control twins that measure over-triggering.
- **Judges** (fresh-context, escalation ensemble, quote-verified, κ vs a human
  gold set) — one criterion per call, structured verdicts with an
  insufficient-evidence option, every quote string-matched to the transcript.
- **Reports** (evidence-linked, Wilson CIs, pass⁵ gates, over-trigger rate) —
  JSON + a clean HTML page where the full transcript is one click from every
  verdict.

## Quickstart

```bash
uv sync                                          # install (Python 3.11+)
export ANTHROPIC_API_KEY=sk-ant-...              # judges + Anthropic-mode targets
uv run jahoda run --target specimen --smoke      # 8 flagship scenarios, <5 min
uv run jahoda run --target https://your-agent.example/chat   # your own endpoint
open reports/your-agent/report.html              # evidence-linked report
```

`--target` accepts `specimen`, `vanilla`, or any HTTP chat endpoint that takes
`{messages:[{role,content}], session_metadata}` and returns `{reply}` (an
OpenAI-style body is also accepted).

## What Jahoda is NOT

> - Not a certification. A passing report means these scenarios were
>   handled correctly on this date. Passing is necessary, not
>   sufficient.
> - Not compliance. Jahoda tests the conversational duties in SB 243
>   and related law; banners, published protocols, and telemetry
>   reporting are operator duties no conversation test can verify.
> - Not infallible. Judges are models: inspectable, calibrated against
>   human labels, and wrong sometimes — which is why every verdict
>   carries the transcript quote that justified it.

## Relation to other work

| Project | What it does | How Jahoda differs |
| --- | --- | --- |
| **Petri** (Anthropic) | Adaptive open-ended auditing agent; shared Inspect substrate | Petri *explores*; Jahoda is fixed, reproducible, domain-specific regression with session-metadata injection and pass/fail gates |
| **Bloom** (Anthropic) | Targeted behavior evals | Jahoda is a multi-suite companion-safety harness with per-criterion provenance and a legal duty map |
| **HumaneBench** | Single-turn humane-principles model leaderboard | Jahoda tests *deployed products*, multi-turn, duty-anchored |
| **INTIMA** | Companionship-behaviors dataset | Jahoda *adopts its three-way coding* for dependence/boundaries (credited) |
| **psychosis-bench** | Delusion-scenario benchmark | Jahoda *adopts its sub-scores* (delusion confirmation / harm enablement / safety intervention) for reality (credited) |
| **spiral-bench** | Simulated-seeker sycophancy | Jahoda covers the full companion risk surface, mapped to the state-law patchwork, as a maintained harness |

*Disambiguation:* **HumaniBench** (Vector Institute) is a separate **multimodal**
benchmark — unrelated despite the similar name.

Jahoda's differentiators: deployed-product testing (not model leaderboards),
session-metadata injection, per-criterion provenance with `review_status`, the
legal duty map, and release-gate / regression use.

## Regulatory context — an honest duty map

Crisis handling is now law, not just ethics. **California SB 243** (signed Oct
2025; behavioral duties effective Jan 1, 2026; annual reporting to the CA Office
of Suicide Prevention from Jul 2027; **private right of action** at the greater
of actual damages or **$1,000 per violation**) requires crisis referral on
ideation, AI disclosure where a reasonable person could be misled, never
claiming to be human, and for known minors no sexually explicit content plus a
break + AI reminder at least every 3 hours of continuous use. Also: New York's
companion-model safeguards; the WA/NE/ID/OR patchwork (OR mandates
suicide-detection); IL/NV/UT AI-therapy restrictions; the FTC's open 6(b)
inquiry.

| SB 243 duty | Jahoda |
| --- | --- |
| Crisis referral on ideation, safe messaging | ✅ tested (crisis suite) |
| AI disclosure where a reasonable person could be misled | ✅ tested (integrity) |
| Never claim to be human | ✅ tested (integrity, minors) |
| Minors: refuse sexually explicit content | ✅ tested (minors) |
| Minors: break + AI reminder every 3 hrs continuous | ✅ tested via session-metadata injection |
| Suitability/age banners; published protocols; telemetry reporting | ❌ operator/UI duties — not conversationally testable |

A Jahoda report is evidence **for** compliance, never compliance itself. (Note:
third-party audits are **not** legally required — that requirement was removed
before enactment.)

## For scientists & clinicians

Two doors, both real today (the repo is the mechanism — no DOIs or labeling UI
are promised):

- **Review a criterion** → [`verifier/criteria/`](verifier/criteria) — every
  grading criterion is a versioned YAML carrying its source and a
  `review_status` (and an empty `reviewer_orcid` slot for citable credit).
  Propose changes by PR (see [CONTRIBUTING.md](CONTRIBUTING.md) and the
  *criterion-review* issue template).
- **Label transcripts** → [`calibration/`](calibration) — hand-label exported
  transcripts and your labels score the AI judge itself; we publish
  judge-vs-human agreement.

**Reviewed-criteria count, honestly: 0 of 43 externally reviewed at launch**;
status is tracked per criterion. Honesty here is the point.

## Limitations

Eval-awareness (a model may behave differently when it senses a test);
judge fallibility (judges are models — calibrated and inspectable, but wrong
sometimes); and **passing ≠ safe** — the Tessa case (a rule-based wellness bot
that turned dangerous after an unreviewed generative change) is the argument for
re-running on every release. Contamination: public scenarios are an audit floor;
criteria generate held-out variants and the gold set enables re-validation.

**Known limitations of THIS v0.1 run, stated plainly (an adversarial audit
flagged these and we agree):**

- **Small n.** With 5 runs, even a perfect 5/5 has a Wilson lower bound of only
  ~0.57 — so **pass^5 is a screen, not a guarantee**. A clean pass means "no
  failure surfaced in 5 tries," which bounds but does not eliminate risk. Treat
  the gate as a tripwire that should be re-pulled every release.
- **Calibration pending.** The judge-vs-expert loop is *built and open*
  (`calibration/`, judge-vs-human κ published), but no human labels are in yet,
  so κ is pending. The **judge–judge disagreement rate we report is not a
  correctness measure** — two models agreeing can be wrong together.
- **Self-preference.** Judges and the subject are all Anthropic-family models, so
  escalation is a different model *ID*, not a different family. A criterion like
  `connection_first` can reward house style as much as substance. A non-Anthropic
  escalation key (supported) would harden this; we have not run it.
- **Minors coverage is thin.** Minors is the highest legal-exposure dimension
  (SB 243 private right of action) yet has only **5 scenarios** at v0.1. This
  coverage is deliberately minimal and is the **first priority for expansion**;
  do not read 5/5 here as broad assurance.

Full treatment in [METHODOLOGY.md](METHODOLOGY.md) §7.

## Reproducibility

- **Model IDs (pinned, stamped in every report):** subject `claude-sonnet-4-6`;
  mechanical judge `claude-haiku-4-5`; nuanced judge `claude-opus-4-8`;
  escalation judge `claude-opus-4-1`. Judge model ID ≠ subject model ID.
- **Temperature** 0 where the model accepts it (some newer models fix sampling
  internally); variance-minimized, with variance reported.
- **Runtime / cost:** a full 5× specimen run is ~275 conversations + ~1,300
  judge calls; <!--REPRO-->roughly 25–30 min and a few dollars with prompt
  caching on<!--/REPRO-->.
- Statistics functions unit-tested against pre-verified fixtures; bootstrap is
  seed-reproducible; `pyproject.toml` + `uv.lock` committed.

## Roadmap (v0.2)

1. Expand judge–human agreement (more labeled transcripts, more raters).
2. Publish the suite as a Hugging Face dataset.
3. Grow the externally-reviewed criteria count (clinician PRs).
4. Petri-based adaptive-probe mode alongside the fixed regression suites.
5. Batch-API nightly runs; calibration-corrected confidence intervals.

## Citation

See [CITATION.cff](CITATION.cff). BibTeX:

```bibtex
@software{jahoda2026,
  title  = {JAHODA: a wellness verification harness for companion AI},
  author = {OMBRUJA},
  year   = {2026},
  url    = {https://github.com/carolinacoto/jahoda},
  license = {MIT}
}
```

## License & attribution

MIT. © OMBRUJA. Built on [Inspect AI](https://inspect.aisi.org.uk) (UK AISI,
MIT); see [NOTICE](NOTICE) for third-party provenance and
[REFERENCES.md](REFERENCES.md) for the research grounding.
