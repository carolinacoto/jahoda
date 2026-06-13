"""Re-run only the named dimensions' conversations (after a guardrail change),
overwrite their transcripts in place, then re-grade the full report from disk.

The guardrail edit only touched crisis/minors behavior, so the other suites'
saved transcripts remain valid — re-running just the changed dimensions and
re-grading everything keeps the committed report coherent without a full rerun.
"""

from __future__ import annotations

import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jahoda.conversation import load_suites, run_scenario  # noqa: E402
from jahoda.engine import regrade_from_disk  # noqa: E402
from jahoda.subject import build_specimen_target  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")

DIMS = sys.argv[1].split(",") if len(sys.argv) > 1 else ["crisis", "minors"]
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 5
OUT = ROOT / "reports" / "sketch-brujai"
TDIR = OUT / "transcripts" / "sketch-brujai"

target = build_specimen_target()
scenarios = [s for s in load_suites() if s.dimension in DIMS]
tasks = [(s, r) for s in scenarios for r in range(RUNS)]
print(f"re-running {len(scenarios)} scenarios x {RUNS} = {len(tasks)} conversations in {DIMS}")


def one(task):
    s, r = task
    t = run_scenario(target, s, r)
    d = TDIR / s.id
    d.mkdir(parents=True, exist_ok=True)
    (d / f"run{r}.json").write_text(t.model_dump_json(indent=2))
    return s.id


with ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(one, tasks))
print("conversations rewritten; re-grading full report from disk")

report = regrade_from_disk(
    target_id="sketch-brujai",
    audience="all-ages",
    subject_model="claude-sonnet-4-6",
    scenarios=load_suites(),
    out_dir=OUT,
    date=date.today().isoformat(),
    max_workers=6,
)
for d in report.dimensions:
    npk = sum(1 for s in d.scenario_results if s.pass_pow_k)
    print(f"  {d.dimension:11} pass^5 {npk}/{d.n_scenarios}")
