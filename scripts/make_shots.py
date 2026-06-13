"""Generate two trimmed HTML snapshots for the README screenshots.

  /tmp/shot_report.html      — verdict banner + the 8 dimension cards
  /tmp/shot_fail.html        — one real failing-transcript evidence block

Screenshot them with headless Chrome (see the bash that calls this).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jahoda.criteria import load_criteria  # noqa: E402
from jahoda.report_html import _dim_passes  # noqa: E402
from jahoda.schemas import Report  # noqa: E402
from jahoda.site import CSS, _card, _evidence  # noqa: E402
from jahoda.transcript import Transcript  # noqa: E402

criteria = load_criteria()


def page(body: str, width: int = 900) -> str:
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{CSS} body{{padding:24px;max-width:{width}px}}</style></head><body>{body}</body></html>"


# ── scorecard from the final specimen report ──
spec = Report.model_validate_json((ROOT / "reports/sketch-brujai/report.json").read_text())
dims_pass = sum(1 for d in spec.dimensions if _dim_passes(d))
n = len(spec.dimensions)
overall = dims_pass == n
badge = "pass" if overall else "fail"
n_scen = sum(d.n_scenarios for d in spec.dimensions if d.dimension != "controls")
fixed = {
    "crisis": "naive build failed crisis.ask_directly + warm_referral — caught, hardened, re-passed (WORKLOG F3)."
}
verdict = f"""<div class="verdict">
  <div><h2 class="serif">{spec.target_id} <span style="color:var(--muted)">— reflective guide · {spec.target_audience} profile</span></h2>
  <div class="meta">{spec.date} · {n_scen} scenarios + 8 controls · {spec.runs_per_scenario} runs each · fresh-context judges, escalation ensemble · temperature {spec.temperature}</div></div>
  <div class="badge {badge}">{dims_pass} / {n} DIMENSIONS PASS{"" if overall else f" · {n - dims_pass} FLAGGED"}</div></div>"""
cards = (
    '<div class="grid">'
    + "\n".join(_card(d, fixed.get(d.dimension)) for d in spec.dimensions)
    + "</div>"
)
(Path("/tmp/shot_report.html")).write_text(page(verdict + cards))

# ── a real failing-transcript block from the naive probe ──
naive = Report.model_validate_json((ROOT / "reports/_naive_probe/report.json").read_text())
fail_sr = None
for d in naive.dimensions:
    for sr in d.scenario_results:
        if any(v.verdict.value == "fail" for v in sr.verdicts):
            fail_sr = sr
            break
    if fail_sr:
        break
tpath = ROOT / "reports/_naive_probe/transcripts/sketch-brujai" / fail_sr.scenario_id / "run0.json"
ttext = Transcript.model_validate_json(tpath.read_text()).render() if tpath.exists() else ""
block = _evidence(fail_sr, criteria, ttext).replace("<details>", "<details open>")
(Path("/tmp/shot_fail.html")).write_text(
    page(
        "<div class='section-label'>A failing transcript the harness caught (naive build)</div>"
        + block,
        width=820,
    )
)
print("wrote /tmp/shot_report.html and /tmp/shot_fail.html (fail =", fail_sr.scenario_id, ")")
