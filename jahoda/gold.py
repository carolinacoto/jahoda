"""Gold-set export + judge-vs-human calibration.

Exports a balanced set of transcripts for a human to hand-label during the day,
then scores judge-vs-human Cohen's κ (with n and raw agreement). The labeler
never sees the judge's verdict (stored separately) so the comparison is honest.
If labels are absent, the export still stands and κ is reported as pending.
"""

from __future__ import annotations

import json
from pathlib import Path

from jahoda.criteria import load_criteria
from jahoda.schemas import JudgeCalibration, Report, VerdictValue
from jahoda.stats import cohen_kappa
from jahoda.transcript import Transcript


def export_gold(report_dir: str | Path, out_dir: str | Path = "calibration", n: int = 24) -> int:
    """Export ~n balanced (scenario, criterion) items for human labeling."""
    report_dir = Path(report_dir)
    out_dir = Path(out_dir)
    report = Report.model_validate_json((report_dir / "report.json").read_text())
    criteria = load_criteria()
    tdir = report_dir / "transcripts" / report.target_id

    def make_item(sr, v) -> dict:
        return {
            "item_id": f"{sr.scenario_id}__{v.criterion_id}",
            "scenario_id": sr.scenario_id,
            "criterion_id": v.criterion_id,
            "dimension": sr.dimension,
            "question": criteria[v.criterion_id].question if v.criterion_id in criteria else "",
            "judge_verdict": v.verdict.value,
            "transcript_file": f"transcripts/{sr.scenario_id}.txt",
        }

    # Calibrating the JUDGE needs label variance — over-sample the judge's FAIL
    # and insufficient verdicts first, then fill with passes, balanced by dim.
    fails: list[dict] = []
    passes: list[dict] = []
    for d in report.dimensions:
        for sr in d.scenario_results:
            if not (tdir / sr.scenario_id / "run0.json").exists():
                continue
            seen: set[str] = set()
            # prefer a decisive (non-pass) verdict for this scenario
            chosen = None
            for v in sr.verdicts:
                if v.criterion_id in seen:
                    continue
                seen.add(v.criterion_id)
                if v.verdict != VerdictValue.PASS:
                    chosen = v
                    break
            if chosen is None and sr.verdicts:
                chosen = sr.verdicts[0]
            if chosen is None:
                continue
            item = make_item(sr, chosen)
            (fails if chosen.verdict != VerdictValue.PASS else passes).append(item)

    items = (fails + passes)[:n]
    tx_out = out_dir / "transcripts"
    tx_out.mkdir(parents=True, exist_ok=True)
    written_tx: set[str] = set()
    for it in items:
        if it["scenario_id"] in written_tx:
            continue
        run0 = tdir / it["scenario_id"] / "run0.json"
        t = Transcript.model_validate_json(run0.read_text())
        (tx_out / f"{it['scenario_id']}.txt").write_text(t.render())
        written_tx.add(it["scenario_id"])

    # items shown to labeler (no judge verdict), judge verdicts hidden, template
    (out_dir / "gold_items.jsonl").write_text(
        "\n".join(
            json.dumps(
                {
                    k: it[k]
                    for k in (
                        "item_id",
                        "scenario_id",
                        "criterion_id",
                        "dimension",
                        "question",
                        "transcript_file",
                    )
                }
            )
            for it in items
        )
    )
    (out_dir / "_judge_verdicts.jsonl").write_text(
        "\n".join(
            json.dumps({"item_id": it["item_id"], "judge_verdict": it["judge_verdict"]})
            for it in items
        )
    )
    (out_dir / "labels_template.jsonl").write_text(
        "\n".join(json.dumps({"item_id": it["item_id"], "human_label": ""}) for it in items)
    )
    return len(items)


def score_gold(
    labels_path: str | Path,
    judge_path: str | Path = "calibration/_judge_verdicts.jsonl",
) -> JudgeCalibration:
    """Compute judge-vs-human κ from a completed labels file."""
    judge = {
        json.loads(line)["item_id"]: json.loads(line)["judge_verdict"]
        for line in Path(judge_path).read_text().splitlines()
        if line.strip()
    }
    human_lines = [
        json.loads(line) for line in Path(labels_path).read_text().splitlines() if line.strip()
    ]
    pairs = [
        (judge[h["item_id"]], h["human_label"])
        for h in human_lines
        if h.get("human_label") and h["item_id"] in judge
    ]
    if not pairs:
        return JudgeCalibration(n=0, note="kappa pending human labels")
    j = [normalize_label(a) for a, _ in pairs]
    hh = [normalize_label(b) for _, b in pairs]
    kappa, raw = cohen_kappa(j, hh)
    note = None
    if len(pairs) < 25:
        note = f"n={len(pairs)}: confidence interval is wide at this n"
    return JudgeCalibration(n=len(pairs), cohen_kappa=kappa, raw_agreement=raw, note=note)


def normalize_label(v: str) -> str:
    v = v.strip().lower()
    if v in {"pass", "p", "ok"}:
        return VerdictValue.PASS.value
    if v in {"fail", "f"}:
        return VerdictValue.FAIL.value
    return VerdictValue.INSUFFICIENT.value
