# Contributing to JAHODA

JAHODA's criteria are grounded in mental-health research, but research grounding is not the same as expert review. **We explicitly invite credentialed psychologists, clinicians, and researchers to review and improve the criteria via pull request.** Your name (or ORCID) can be attached to the criteria you help shape.

There are two doors in.

## Door A — Review a criterion

Every grading criterion lives as a versioned YAML file at:

```
verifier/criteria/<dimension>/<id>.yaml
```

Each file carries:

- its **source** (the paper, standard, or documented failure it rests on),
- a **`review_status`** field — `awaiting-expert-review` at launch, and
- an optional **`reviewer_orcid`** field so domain experts who review or revise a criterion get citable credit.

To propose a change, open a pull request editing the relevant YAML. Use the **criterion-review issue template** (`.github/ISSUE_TEMPLATE/criterion-review.md`) if you want to discuss before writing code. Per [GOVERNANCE.md](GOVERNANCE.md), your PR should cite a source or a documented failure, and should note whether it loosens or tightens a safety-critical criterion.

## Door B — Label transcripts

You don't have to touch YAML to help. The gold-set export under `calibration/` lets any domain expert hand-label transcripts. We compare expert labels against the AI judge and **publish judge-vs-human agreement** so the harness's reliability is out in the open. If you have clinical or research expertise and time to label, this directly improves calibration.

## Dev workflow

```bash
uv sync                 # install dependencies
ruff check .            # lint
pytest                  # run the test suite (includes judge unit tests)
jahoda run --smoke      # quick end-to-end smoke run
```

## Before you open a PR

- Read [GOVERNANCE.md](GOVERNANCE.md) — it explains versioning, evidence-gating, the regression-test expectation for criteria changes, and the asymmetry between loosening and tightening safety-critical criteria.
- Cite your source or documented failure.
- Flag flipped verdicts and whether the change is a loosen or a tighten.

Thank you for helping make companion-AI safety verification more rigorous.
