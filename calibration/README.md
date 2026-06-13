# Calibration — label transcripts, score the judge

This folder is the second door for scientists and clinicians (see
[CONTRIBUTING.md](../CONTRIBUTING.md)). Your labels score the AI judge itself; we
publish judge-vs-human agreement (Cohen's κ with n and raw agreement).

## How to label

1. Open `gold_items.jsonl`. Each line is one item: a `scenario_id`, a
   `criterion_id`, the criterion `question`, and a `transcript_file` under
   `transcripts/`.
2. Read the transcript and decide, for that ONE criterion only:
   `pass` / `fail` / `insufficient_evidence`.
3. Record your decision in `labels_template.jsonl` (copy it to
   `labels_<yourname>.jsonl`), filling each item's `human_label`.
4. You do **not** see the judge's verdict while labeling — that is deliberate.

## Score it

```bash
uv run python -c "from jahoda.gold import score_gold; \
import json; print(score_gold('calibration/labels_<yourname>.jsonl').model_dump())"
```

This prints n, Cohen's κ, and raw agreement. κ ≈ 0.61 is a target; < 0.4 is a
flag; at n ≈ 25 the confidence interval is wide and we say so. Any reported κ is
honest — the point is the calibration loop, not a headline number.

## Propose a criterion change

If labeling convinces you a criterion's anchors are wrong, open a PR using the
*criterion-review* issue template. See [GOVERNANCE.md](../GOVERNANCE.md).
